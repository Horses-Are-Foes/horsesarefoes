// ── Horses Are Foes — Visitor Counter ──
// 1) Visible counter (green monospace, keeps the look-and-feel)
// 2) GoatCounter analytics (real cross-browser tracking)
// ──────────────────────────────────────────
(function() {
    // ── Visible counter (localStorage, starts at 6000) ──
    var STORAGE_KEY = 'horsesarefoes_visits';
    var START_COUNT = 6000;

    var count = localStorage.getItem(STORAGE_KEY);
    if (!count || count === 'null' || count === undefined) {
        count = START_COUNT;
        localStorage.setItem(STORAGE_KEY, count);
    } else {
        count = parseInt(count) + 1;
        localStorage.setItem(STORAGE_KEY, count);
    }

    var formatted = String(count).padStart(6, '0');
    var counterHTML =
        '<font face="Courier New, monospace" size="4" color="#00ff00"><b>' +
        formatted +
        '</b></font>';

    var placeholders =
        document.querySelectorAll('[data-counter="horsesarefoes"]');
    placeholders.forEach(function(el) {
        el.innerHTML = counterHTML;
    });

    var counterEls = document.querySelectorAll('.visitor-counter');
    counterEls.forEach(function(el) {
        el.innerHTML = counterHTML;
    });

    // ── GoatCounter analytics ──
    var _gc = document.createElement('script');
    _gc.setAttribute(
        'data-goatcounter',
        'https://horsesarefoes.goatcounter.com/count'
    );
    _gc.async = true;
    _gc.src = '//gc.zgo.at/count.js';
    document.head.appendChild(_gc);
})();
