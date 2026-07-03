(function() {
  'use strict';

  var favoritesOnly = false;
  var searchQuery = '';
  var activeCategories = [];

  function matchesSearch(card) {
    if (!searchQuery) {
      return true;
    }
    var text = card.textContent.toLowerCase();
    return text.indexOf(searchQuery) >= 0;
  }

  function matchesCategories(card) {
    if (activeCategories.length === 0) {
      return true;
    }
    var raw = card.getAttribute('data-categories') || '';
    var cats = raw ? raw.split('||') : [];
    for (var i = 0; i < activeCategories.length; i++) {
      if (cats.indexOf(activeCategories[i]) >= 0) {
        return true;
      }
    }
    return false;
  }

  function anyFilterActive() {
    return favoritesOnly || searchQuery !== '' || activeCategories.length > 0;
  }

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

      var visible = true;
      if (favoritesOnly && !window.__isFavorited(uid)) {
        visible = false;
      }
      if (visible && !matchesSearch(card)) {
        visible = false;
      }
      if (visible && !matchesCategories(card)) {
        visible = false;
      }

      if (!visible) {
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
      if (anyFilterActive() && !visibleMonths[month]) {
        sep.classList.add('hidden');
      } else {
        sep.classList.remove('hidden');
      }
    });

    // Update count
    if (countEl) {
      var total = cards.length;
      if (anyFilterActive()) {
        countEl.textContent = visibleCount + ' of ' + total + ' event' + (total !== 1 ? 's' : '');
      } else {
        countEl.textContent = total + ' event' + (total !== 1 ? 's' : '');
      }
    }

    // Empty state
    if (emptyState) {
      if (anyFilterActive() && visibleCount === 0) {
        emptyState.classList.remove('hidden');
        if (favoritesOnly && window.__getFavorites().length === 0) {
          emptyState.textContent = 'No favorites yet. Click the ♡ on events to add them.';
        } else {
          emptyState.textContent = 'No events match the current filters.';
        }
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

    var searchInput = document.querySelector('.search-input');
    if (searchInput) {
      searchInput.addEventListener('input', function() {
        searchQuery = searchInput.value.trim().toLowerCase();
        updateFilter();
      });
    }

    document.querySelectorAll('.category-chip').forEach(function(chip) {
      chip.addEventListener('click', function() {
        var cat = chip.getAttribute('data-category');
        var idx = activeCategories.indexOf(cat);
        if (idx >= 0) {
          activeCategories.splice(idx, 1);
          chip.setAttribute('aria-pressed', 'false');
        } else {
          activeCategories.push(cat);
          chip.setAttribute('aria-pressed', 'true');
        }
        updateFilter();
      });
    });

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
