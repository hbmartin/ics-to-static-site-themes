(function() {
  'use strict';

  var favoritesOnly = false;

  function updateFilter() {
    var cards = document.querySelectorAll('.event-card');
    var separators = document.querySelectorAll('.month-separator');
    var countEl = document.querySelector('.event-count');
    var emptyState = document.querySelector('.empty-state');
    var visibleCount = 0;

    // Track which months have visible events
    var visibleMonths = {};

    cards.forEach(function(card) {
      var uid = card.getAttribute('data-uid');
      var month = card.getAttribute('data-month');

      if (favoritesOnly && !window.__isFavorited(uid)) {
        card.classList.add('hidden');
      } else {
        card.classList.remove('hidden');
        visibleCount++;
        if (month) {
          visibleMonths[month] = true;
        }
      }
    });

    // Show/hide month separators
    separators.forEach(function(sep) {
      var month = sep.getAttribute('data-month');
      if (favoritesOnly && !visibleMonths[month]) {
        sep.classList.add('hidden');
      } else {
        sep.classList.remove('hidden');
      }
    });

    // Update count
    if (countEl) {
      var total = cards.length;
      if (favoritesOnly) {
        countEl.textContent = visibleCount + ' favorite' + (visibleCount !== 1 ? 's' : '') + ' of ' + total + ' events';
      } else {
        countEl.textContent = total + ' event' + (total !== 1 ? 's' : '');
      }
    }

    // Empty state
    if (emptyState) {
      if (favoritesOnly && visibleCount === 0) {
        emptyState.classList.remove('hidden');
        emptyState.textContent = 'No favorites yet. Click the \u2661 on events to add them.';
      } else {
        emptyState.classList.add('hidden');
      }
    }
  }

  function init() {
    var toggleBtn = document.querySelector('.favorites-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', function() {
        favoritesOnly = !favoritesOnly;
        toggleBtn.setAttribute('aria-pressed', favoritesOnly ? 'true' : 'false');
        updateFilter();
      });
    }

    // Initial filter
    updateFilter();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.__updateFilter = updateFilter;
})();
