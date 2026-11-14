/* Reading settings: instant apply, saved in the background (with the CSRF token),
   plus the focus timer and the background sound.
   Settings come from the server on page load (see #reader-data). */
(function () {
  'use strict';

  var $ = function (s) { return document.querySelector(s); };
  var data = JSON.parse(document.getElementById('reader-data').textContent);
  var S = data.settings;
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  var reduceMotion = function () { return matchMedia('(prefers-reduced-motion: reduce)').matches; };

  /* ---------- status line ---------- */
  var statusTimer;
  function status(msg, opts) {
    opts = opts || {};
    var el = $('#status');
    el.textContent = msg;
    el.classList.toggle('error', !!opts.error);
    clearTimeout(statusTimer);
    if (msg) statusTimer = setTimeout(function () { el.textContent = ''; el.classList.remove('error'); }, opts.ms || 4000);
  }

  /* ---------- POST helper (JSON + CSRF) ---------- */
  function api(url, body) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify(body || {})
    }).then(function (r) {
      return r.json().catch(function () { return null; }).then(function (j) {
        if (!r.ok) {
          var msg = (j && j.error) || (r.status === 403 ? 'Security check failed. Reload the page.' : 'Something went wrong (' + r.status + ').');
          throw new Error(msg);
        }
        return j;
      });
    }, function () {
      throw new Error('No connection. Check your internet and try again.');
    });
  }

  /* ---------- saving settings (batched) ---------- */
  var dirty = {}, saveTimer = null, saving = false;
  function queueSave(key, value) {
    dirty[key] = value;
    clearTimeout(saveTimer);
    saveTimer = setTimeout(flush, 400);
  }
  function flush() {
    if (saving) { saveTimer = setTimeout(flush, 300); return; }
    var payload = dirty; dirty = {};
    if (!Object.keys(payload).length) return;
    saving = true;
    status('Saving...', { ms: 8000 });
    api(data.urls.settings, payload).then(function () {
      status('Settings saved.', { ms: 1800 });
    }).catch(function (e) {
      Object.keys(payload).forEach(function (k) { if (!(k in dirty)) dirty[k] = payload[k]; });
      status('Could not save settings: ' + e.message, { error: true, ms: 8000 });
    }).then(function () { saving = false; });
  }
  function changed(key) {
    document.dispatchEvent(new CustomEvent('lessonfy:setting', { detail: { key: key } }));
  }

  /* ---------- look: size, spacing, theme, background ---------- */
  function applyStyle() {
    var r = $('#reader');
    r.style.setProperty('--fs', S.font_size + 'px');
    r.style.setProperty('--lh', S.line_spacing);
  }
  function applyTheme() {
    document.documentElement.setAttribute('data-theme', S.theme);
    document.documentElement.setAttribute('data-bg', S.background);
  }
  function applyFocus() { document.body.classList.toggle('focus', S.focus_mode); }

  $('#size').oninput = function (e) { S.font_size = +e.target.value; applyStyle(); queueSave('font_size', S.font_size); };
  $('#gap').oninput = function (e) { S.line_spacing = +e.target.value; applyStyle(); queueSave('line_spacing', S.line_spacing); };
  $('#bionic').onchange = function (e) { S.bionic_reading = e.target.checked; changed('bionic_reading'); queueSave('bionic_reading', S.bionic_reading); };
  $('#focus').onchange = function (e) { S.focus_mode = e.target.checked; applyFocus(); queueSave('focus_mode', S.focus_mode); };
  $('#theme').onclick = function () { S.theme = S.theme === 'dark' ? 'light' : 'dark'; applyTheme(); queueSave('theme', S.theme); };
  $('#bg').onchange = function (e) { S.background = e.target.value; applyTheme(); queueSave('background', S.background); };

  /* ---------- timer ---------- */
  var T = { mode: 'focus', left: 0, run: false, id: null };
  function lens() { return S.timer_preset.split('-').map(Number); }
  function showT() {
    var m = Math.floor(T.left / 60), s = T.left % 60;
    $('#time').textContent = String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    $('#phase').textContent = T.mode === 'focus' ? 'Focus' : 'Break';
    $('#tstart').textContent = T.run ? 'Pause' : 'Start';
  }
  function stopT() { T.run = false; clearInterval(T.id); showT(); }
  function tick() {
    T.left--;
    if (T.left <= 0) {
      beep();
      var l = lens();
      T.mode = T.mode === 'focus' ? 'break' : 'focus';
      T.left = (T.mode === 'focus' ? l[0] : l[1]) * 60;
      stopT();
      status(T.mode === 'break' ? 'Focus block done. Take a ' + l[1] + ' minute break.' : 'Break over. Ready for the next block.', { ms: 9000 });
    }
    showT();
  }
  $('#tstart').onclick = function () {
    ensureAC();
    if (T.run) { stopT(); return; }
    T.run = true; T.id = setInterval(tick, 1000); showT();
  };
  $('#treset').onclick = function () { stopT(); T.mode = 'focus'; T.left = lens()[0] * 60; showT(); };
  $('#tlen').onchange = function (e) { S.timer_preset = e.target.value; queueSave('timer_preset', S.timer_preset); $('#treset').click(); };

  /* ---------- sound: noise made in the browser (no audio files needed) ---------- */
  var AC = null, src = null, gain = null, playing = false;
  function ensureAC() {
    try { AC = AC || new (window.AudioContext || window.webkitAudioContext)(); if (AC.resume) AC.resume(); } catch (e) { AC = null; }
    return AC;
  }
  function beep() {
    if (!ensureAC()) return;
    var o = AC.createOscillator(), g = AC.createGain();
    o.frequency.value = 660; g.gain.value = 0.12;
    o.connect(g); g.connect(AC.destination); o.start(); o.stop(AC.currentTime + 0.3);
  }
  function setVol() { if (gain) gain.gain.value = S.volume * (S.sound === 'brown' ? 1 : 0.5); }
  function showSound() {
    var b = $('#soundtoggle');
    b.textContent = playing ? 'Stop' : 'Play';
    b.setAttribute('aria-pressed', playing ? 'true' : 'false');
    b.disabled = S.sound === 'off';
  }
  function stopSound() {
    if (src) { try { src.stop(); } catch (e) {} src = null; }
    playing = false; showSound();
  }
  function playSound() {
    stopSound();
    if (S.sound === 'off') return;
    if (!ensureAC()) { status('Your browser could not start the sound.', { error: true }); return; }
    var n = AC.sampleRate * 2, buf = AC.createBuffer(1, n, AC.sampleRate), d = buf.getChannelData(0), last = 0, i;
    for (i = 0; i < n; i++) {
      var w = Math.random() * 2 - 1;
      if (S.sound === 'brown') { last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; } else d[i] = w;
    }
    src = AC.createBufferSource(); src.buffer = buf; src.loop = true;
    if (!gain) { gain = AC.createGain(); gain.connect(AC.destination); }
    setVol();
    if (S.sound === 'rain') {
      var hp = AC.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 800;
      var lp = AC.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 6000;
      src.connect(hp); hp.connect(lp); lp.connect(gain);
    } else src.connect(gain);
    src.start();
    playing = true; showSound();
  }
  // Browsers block sound until the person clicks, so a saved choice does not
  // start by itself. Choosing a sound or pressing Play starts it.
  $('#sound').onchange = function (e) { S.sound = e.target.value; queueSave('sound', S.sound); playSound(); };
  $('#soundtoggle').onclick = function () { if (playing) stopSound(); else playSound(); };
  $('#vol').oninput = function (e) { S.volume = +e.target.value; setVol(); queueSave('volume', S.volume); };

  /* ---------- start up ---------- */
  applyStyle(); applyTheme(); applyFocus();
  T.left = lens()[0] * 60; showT(); showSound();

  window.Lessonfy = {
    data: data,
    settings: S,
    api: api,
    status: status,
    reduceMotion: reduceMotion
  };
})();
