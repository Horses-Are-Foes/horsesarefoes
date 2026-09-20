// Self-hosted visitor counter - starts at 6000
// Uses localStorage to track visits per browser
(function() {
    var STORAGE_KEY = 'horsesarefoes_visits';
    var START_COUNT = 6000;
    
    // Initialize counter if first visit
    var count = localStorage.getItem(STORAGE_KEY);
    if (!count || count === 'null' || count === undefined) {
        count = START_COUNT;
        localStorage.setItem(STORAGE_KEY, count);
    } else {
        count = parseInt(count) + 1;
        localStorage.setItem(STORAGE_KEY, count);
    }
    
    // Format as 6-digit number
    var formatted = String(count).padStart(6, '0');
    
    // Create counter display
    var counterHTML = '<font face="Courier New, monospace" size="4" color="#00ff00"><b>' + formatted + '</b></font>';
    
    // Replace all counter placeholders
    var placeholders = document.querySelectorAll('[data-counter="horsesarefoes"]');
    placeholders.forEach(function(el) {
        el.innerHTML = counterHTML;
    });
    
    // Also add to any elements with class "visitor-counter"
    var counterElements = document.querySelectorAll('.visitor-counter');
    counterElements.forEach(function(el) {
        el.innerHTML = counterHTML;
    });
})();
