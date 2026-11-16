(function () {
  'use strict';

  var WORD = /([\p{L}\p{N}'\u2019]+)/u;

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function html(str) {
    return str
      .split(WORD)
      .map(function (part, i) {
        if (i % 2 === 0) return esc(part); // text between words
        var chars = Array.from(part);
        var n = Math.max(1, Math.ceil(chars.length * 0.45));
        return '<b>' + esc(chars.slice(0, n).join('')) + '</b>' + esc(chars.slice(n).join(''));
      })
      .join('');
  }

  window.Bionic = { html: html, esc: esc };
})();
