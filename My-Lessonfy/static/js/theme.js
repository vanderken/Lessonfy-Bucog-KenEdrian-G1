(function () {
  'use strict';

  var root = document.documentElement;
  var sel = document.getElementById('bg');
  var btn = document.getElementById('theme');
  if (!sel && !btn) return;
  var script = document.querySelector('script[data-settings-url]');
  var url = script ? script.getAttribute('data-settings-url') : null;
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';

  function remember(key, value) {
    try { localStorage.setItem('lessonfy:' + key, value); } catch (e) { }
  }
  function save(key, value) {
    remember(key, value);
    if (!url) return;
    var payload = {};
    payload[key] = value;
    fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify(payload)
    }).catch(function () { });
  }

  if (sel) {
    sel.value = root.getAttribute('data-bg') || 'default';
    sel.addEventListener('change', function () {
      root.setAttribute('data-bg', sel.value);
      save('background', sel.value);
    });
  }
  if (btn) {
    btn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      save('theme', next);
    });
  }

  window.addEventListener('storage', function (e) {
    if (e.key === 'lessonfy:theme' && e.newValue) {
      root.setAttribute('data-theme', e.newValue);
    } else if (e.key === 'lessonfy:bg' && e.newValue) {
      root.setAttribute('data-bg', e.newValue);
      if (sel) sel.value = e.newValue;
    }
  });
})();
