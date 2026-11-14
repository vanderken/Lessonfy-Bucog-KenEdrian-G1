/* Bionic reading: a visual layer ONLY.
   It bolds the first part of each word in text that is already on screen.
   It never changes the stored text or pin offsets: the plain text of the
   result is always exactly the same as the input. */
(function () {
  'use strict';

  // Letters (any language), digits, and apostrophes count as part of a word.
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
