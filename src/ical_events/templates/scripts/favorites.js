(function() {
  'use strict';

  var STORAGE_KEY = 'events-favorites';

  function getFavorites() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function saveFavorites(favs) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(favs));
    } catch (e) {
      // storage unavailable
    }
  }

  function toggleFavorite(uid) {
    var favs = getFavorites();
    var idx = favs.indexOf(uid);
    if (idx >= 0) {
      favs.splice(idx, 1);
    } else {
      favs.push(uid);
    }
    saveFavorites(favs);
    return idx < 0; // returns true if now favorited
  }

  function isFavorited(uid) {
    return getFavorites().indexOf(uid) >= 0;
  }

  function updateFavoriteButton(btn, favorited) {
    btn.setAttribute('aria-pressed', favorited ? 'true' : 'false');
    btn.setAttribute('aria-label', favorited ? 'Remove from favorites' : 'Add to favorites');
    btn.textContent = favorited ? '\u2665' : '\u2661';
  }

  function initFavorites() {
    var buttons = document.querySelectorAll('.favorite-btn');
    buttons.forEach(function(btn) {
      var uid = btn.getAttribute('data-uid');
      if (uid) {
        updateFavoriteButton(btn, isFavorited(uid));
      }
    });

    document.addEventListener('click', function(e) {
      var btn = e.target.closest('.favorite-btn');
      if (btn) {
        var uid = btn.getAttribute('data-uid');
        if (uid) {
          var nowFavorited = toggleFavorite(uid);
          updateFavoriteButton(btn, nowFavorited);
          // Trigger filter update if favorites filter is active
          if (typeof window.__updateFilter === 'function') {
            window.__updateFilter();
          }
        }
      }
    });
  }

  function copyEventLink(anchorId) {
    var base = window.location.href.split('#')[0];
    var url = base + '#event-' + anchorId;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url);
    } else {
      // Fallback
      var ta = document.createElement('textarea');
      ta.value = url;
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
  }

  function initCopyLinks() {
    document.addEventListener('click', function(e) {
      var btn = e.target.closest('.copy-btn');
      if (btn) {
        var anchorId = btn.getAttribute('data-anchor');
        if (anchorId) {
          copyEventLink(anchorId);
          var feedback = btn.querySelector('.copy-feedback');
          if (feedback) {
            feedback.classList.add('show');
            setTimeout(function() {
              feedback.classList.remove('show');
            }, 1500);
          }
        }
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initFavorites();
      initCopyLinks();
    });
  } else {
    initFavorites();
    initCopyLinks();
  }

  window.__getFavorites = getFavorites;
  window.__isFavorited = isFavorited;
})();
