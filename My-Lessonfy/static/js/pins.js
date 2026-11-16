(function () {
  'use strict';

  var L = window.Lessonfy;
  var D = L.data, S = L.settings;
  var $ = function (s) { return document.querySelector(s); };
  var esc = Bionic.esc;

  var panels = D.panels.map(function (p) { p.cps = Array.from(p.text); return p; });
  var collections = D.collections.slice();
  var pins = D.pins.slice();
  var active = Math.max(0, panels.findIndex(function (p) { return !p.done; }));

  var panelIndexById = {};
  panels.forEach(function (p, i) { panelIndexById[p.id] = i; });
  function collectionById(id) { return collections.find(function (c) { return c.id === id; }); }
  function pinById(id) { return pins.find(function (p) { return p.id === id; }); }
  function pinsOf(panelId) { return pins.filter(function (p) { return p.panel === panelId; }); }
  function url(template, id) { return template.replace(/\/0\//, '/' + id + '/'); }

  function rangeOffsets(txtEl, range) {
    var pre = document.createRange();
    pre.selectNodeContents(txtEl);
    pre.setEnd(range.startContainer, range.startOffset);
    var start = Array.from(pre.toString()).length;
    pre.setEnd(range.endContainer, range.endOffset);
    var end = Array.from(pre.toString()).length;
    return { start: start, end: end };
  }

  function trimOffsets(cps, start, end) {
    while (start < end && /\s/.test(cps[start])) start++;
    while (end > start && /\s/.test(cps[end - 1])) end--;
    return { start: start, end: end };
  }

  function paraHTML(i) {
    var p = panels[i], cps = p.cps, len = cps.length;
    var ms = pinsOf(p.id);
    var points = new Set([0, len]);
    ms.forEach(function (m) { points.add(Math.min(m.start, len)); points.add(Math.min(m.end, len)); });
    var pts = Array.from(points).sort(function (a, b) { return a - b; });
    var out = '';
    for (var k = 0; k < pts.length - 1; k++) {
      var a = pts[k], b = pts[k + 1];
      if (a === b) continue;
      var seg = cps.slice(a, b).join('');
      var inner = S.bionic_reading ? Bionic.html(seg) : esc(seg);
      var cov = ms.filter(function (m) { return m.start <= a && m.end >= b; });
      if (!cov.length) { out += inner; continue; }
      var top = cov[cov.length - 1];
      var col = collectionById(top.collection);
      var color = col ? col.color : '#FFE45C';
      var allRes = cov.every(function (m) { return m.resolved; });
      var ids = cov.map(function (m) { return m.id; }).join(' ');
      out += '<span class="m' + (allRes ? ' res' : '') + '" style="background-color:' + esc(color) + '" data-pins="' + ids + '">' + inner + '</span>';
    }
    return out;
  }

  function lastIndex() { return panels.length - 1; }

  function chunkRowHTML(i) {
    var p = panels[i];
    return '<button class="btn" type="button" data-act="flag">Come back to this</button>' +
      '<button class="btn" type="button" data-act="prev"' + (i === 0 ? ' disabled' : '') + '>Previous</button>' +
      '<button class="btn pri" type="button" data-act="next">' + (p.done ? 'Done' : (i === lastIndex() ? 'Mark done' : 'Done, next')) + '</button>';
  }

  function render() {
    document.body.classList.toggle('focus', S.focus_mode);
    $('#chunks').innerHTML = panels.map(function (p, i) {
      return '<section class="chunk' + (i === active ? ' active' : '') + (p.done ? ' done' : '') + '" data-i="' + i + '">' +
        '<div class="txt" data-i="' + i + '">' + paraHTML(i) + '</div>' +
        '<div class="row">' + chunkRowHTML(i) + '</div></section>';
    }).join('') || '<p class="empty">This lesson has no sections yet. <a href="' + esc(document.querySelector('.sidepanel + p a').href) + '">Add one</a>.</p>';
    updateProgress();
    renderList();
  }

  function refreshPanel(i) {
    var sec = document.querySelector('.chunk[data-i="' + i + '"]');
    if (!sec) return;
    sec.querySelector('.txt').innerHTML = paraHTML(i);
    sec.classList.toggle('done', !!panels[i].done);
    sec.querySelector('.row').innerHTML = chunkRowHTML(i);
  }

  function updateProgress() {
    var n = panels.filter(function (p) { return p.done; }).length;
    $('#fill').style.width = (panels.length ? n / panels.length * 100 : 0) + '%';
    $('#pcount').textContent = n + ' of ' + panels.length + ' sections done';
  }

  function snip(m) { return m.snippet.length > 80 ? m.snippet.slice(0, 77) + '...' : m.snippet; }

  function renderList() {
    $('#count').textContent = pins.length;
    if (!pins.length) {
      $('#list').innerHTML = '<p class="empty">Nothing pinned yet. Select any text and pick a collection, or use "Come back to this" under a section.</p>';
      return;
    }
    var html = '';
    collections.forEach(function (c) {
      var mine = pins.filter(function (p) { return p.collection === c.id; })
        .sort(function (a, b) { return (panelIndexById[a.panel] - panelIndexById[b.panel]) || (a.start - b.start); });
      if (!mine.length) return;
      html += '<div class="group"><h3><span class="dot" style="background:' + esc(c.color) + '"></span>' + esc(c.name) + ' (' + mine.length + ')</h3><ul>';
      mine.forEach(function (m) {
        html += '<li class="item' + (m.resolved ? ' res' : '') + '" data-id="' + m.id + '">' +
          '<div class="snip" data-a="jump" tabindex="0" role="button">' + esc(snip(m)) + '</div>' +
          '<div class="meta">Section ' + (panelIndexById[m.panel] + 1) + (m.resolved ? ' · understood' : '') + '</div>' +
          '<div class="acts"><button class="btn sm" type="button" data-a="jump">Jump back</button>' +
          '<button class="btn sm" type="button" data-a="res">' + (m.resolved ? 'Not yet' : 'Got it') + '</button>' +
          '<button class="btn sm" type="button" data-a="del">Remove</button></div></li>';
      });
      html += '</ul></div>';
    });
    $('#list').innerHTML = html;
  }

  function setActive(i) {
    active = i;
    document.querySelectorAll('.chunk').forEach(function (c) { c.classList.toggle('active', +c.dataset.i === i); });
  }

  function scrollSmooth() { return L.reduceMotion() ? 'auto' : 'smooth'; }

  function jump(id) {
    var m = pinById(id);
    if (!m) return;
    var i = panelIndexById[m.panel];
    setActive(i);
    var els = document.querySelectorAll('.m[data-pins~="' + id + '"]');
    if (!els.length) return;
    els[0].scrollIntoView({ block: 'center', behavior: scrollSmooth() });
    els.forEach(function (e) { e.classList.remove('pulse'); void e.offsetWidth; e.classList.add('pulse'); });
    setTimeout(function () { els.forEach(function (e) { e.classList.remove('pulse'); }); }, 1500);
  }

  function fail(e) { L.status(e.message, { error: true, ms: 7000 }); }

  function createPin(panelIdx, collectionId, start, end) {
    var p = panels[panelIdx];
    L.status('Saving pin...', { ms: 8000 });
    return L.api(D.urls.pinCreate, { panel: p.id, collection: collectionId, start: start, end: end })
      .then(function (r) {
        pins.push(r.pin);
        refreshPanel(panelIdx);
        renderList();
        var c = collectionById(collectionId);
        L.status('Pinned to ' + (c ? c.name : 'collection') + '.', { ms: 2500 });
      }).catch(fail);
  }

  function quickCollectionId() {
    var c = collections.find(function (x) { return x.name.toLowerCase() === D.quickCollection.toLowerCase(); });
    if (c) return Promise.resolve(c.id);
    return L.api(D.urls.quickCollection, {}).then(function (r) {
      collections.push(r.collection);
      return r.collection.id;
    });
  }

  function flagPanel(i) {
    var p = panels[i];
    quickCollectionId().then(function (cid) {
      var dup = pins.some(function (m) { return m.panel === p.id && m.collection === cid && m.start === 0 && m.end === p.cps.length; });
      if (dup) { L.status('This section is already in your list.'); return; }
      return createPin(i, cid, 0, p.cps.length);
    }).catch(fail);
  }

  function setDone(i, done) {
    var p = panels[i];
    var before = p.done;
    p.done = done;
    refreshPanel(i); updateProgress();
    return L.api(url(D.urls.panelDone, p.id), { done: done }).catch(function (e) {
      p.done = before; refreshPanel(i); updateProgress(); fail(e);
    });
  }

  function goTo(i) {
    setActive(i);
    var c = document.querySelector('.chunk[data-i="' + i + '"]');
    if (c) c.scrollIntoView({ behavior: scrollSmooth(), block: 'start' });
  }

  $('#chunks').addEventListener('click', function (e) {
    var sec = e.target.closest('.chunk');
    if (!sec) return;
    var i = +sec.dataset.i, b = e.target.closest('[data-act]');
    if (!b) { if (i !== active && !getSelection().toString()) setActive(i); return; }
    var act = b.dataset.act;
    if (act === 'flag') { setActive(i); flagPanel(i); }
    else if (act === 'prev') { if (i > 0) goTo(i - 1); }
    else if (act === 'next') {
      var p = panels[i];
      if (!p.done) setDone(i, true);
      if (i < lastIndex()) goTo(i + 1); else setActive(i);
    }
  });

  $('#list').addEventListener('click', function (e) { listAction(e); });
  $('#list').addEventListener('keydown', function (e) {
    if ((e.key === 'Enter' || e.key === ' ') && e.target.classList.contains('snip')) { e.preventDefault(); listAction(e); }
  });
  function listAction(e) {
    var li = e.target.closest('.item'), a = e.target.closest('[data-a]');
    if (!li || !a) return;
    var id = +li.dataset.id, m = pinById(id);
    if (!m) return;
    if (a.dataset.a === 'jump') jump(id);
    else if (a.dataset.a === 'res') {
      var next = !m.resolved;
      L.api(url(D.urls.pinResolve, id), { resolved: next }).then(function (r) {
        m.resolved = r.pin.resolved; refreshPanel(panelIndexById[m.panel]); renderList();
      }).catch(fail);
    } else if (a.dataset.a === 'del') {
      L.api(url(D.urls.pinDelete, id), {}).then(function () {
        pins = pins.filter(function (x) { return x.id !== id; });
        refreshPanel(panelIndexById[m.panel]); renderList();
        L.status('Pin removed.', { ms: 2000 });
      }).catch(fail);
    }
  }

  var tb = $('#tb'), sel = null;

  function buildToolbar() {
    tb.innerHTML = collections.map(function (c) {
      return '<button type="button" data-c="' + c.id + '" style="background:' + esc(c.color) + '"><span class="dot" style="background:' + esc(c.color) + '"></span>' + esc(c.name) + '</button>';
    }).join('') + '<button type="button" class="cl" data-t="clear">Clear</button>';
  }

  function hideTb() { tb.style.display = 'none'; sel = null; }

  function txtOf(n) {
    var el = n && n.nodeType === 3 ? n.parentElement : n;
    return el && el.closest ? el.closest('.txt') : null;
  }

  document.addEventListener('selectionchange', function () {
    var s = getSelection();
    if (!s.rangeCount || s.isCollapsed) { hideTb(); return; }
    var r = s.getRangeAt(0), a = txtOf(r.startContainer), b = txtOf(r.endContainer);
    if (!a || a !== b) { hideTb(); return; }
    var i = +a.dataset.i;
    var o = rangeOffsets(a, r);
    o = trimOffsets(panels[i].cps, o.start, o.end);
    if (o.end <= o.start) { hideTb(); return; }
    sel = { i: i, start: o.start, end: o.end };
    buildToolbar();
    var rect = r.getBoundingClientRect();
    tb.style.display = 'flex';
    var w = tb.offsetWidth;
    tb.style.left = Math.max(8, Math.min(innerWidth - w - 8, rect.left + rect.width / 2 - w / 2)) + 'px';
    tb.style.top = (rect.top - tb.offsetHeight - 8 < 8 ? rect.bottom + 10 : rect.top - tb.offsetHeight - 8) + 'px';
  });

  ['mousedown', 'touchstart'].forEach(function (ev) {
    tb.addEventListener(ev, function (e) { e.preventDefault(); }, { passive: false });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && sel) { getSelection().removeAllRanges(); hideTb(); }
  });

  tb.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b || !sel) return;
    var x = sel;
    getSelection().removeAllRanges(); hideTb();
    setActive(x.i);
    if (b.dataset.t === 'clear') {
      L.api(D.urls.pinsClear, { panel: panels[x.i].id, start: x.start, end: x.end }).then(function (r) {
        pins = pins.filter(function (m) { return r.removed.indexOf(m.id) === -1; });
        refreshPanel(x.i); renderList();
        L.status(r.removed.length ? 'Pins removed.' : 'No pins on that text.', { ms: 2000 });
      }).catch(fail);
    } else {
      createPin(x.i, +b.dataset.c, x.start, x.end);
    }
  });

  document.addEventListener('lessonfy:setting', function (e) {
    if (e.detail.key === 'bionic_reading') {
      document.querySelectorAll('.chunk').forEach(function (c) { refreshPanel(+c.dataset.i); });
    }
  });

  render();

  window.LessonfyPins = { rangeOffsets: rangeOffsets, trimOffsets: trimOffsets };
})();
