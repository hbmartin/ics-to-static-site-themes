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
    btn.textContent = favorited ? '♥' : '♡';
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

  function getEventExportData() {
    var el = document.getElementById('event-export-data');
    if (!el) {
      return [];
    }
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return [];
    }
  }

  function extractVevent(ics) {
    var start = ics.indexOf('BEGIN:VEVENT');
    var end = ics.indexOf('END:VEVENT');
    if (start < 0 || end < 0) {
      return '';
    }
    return ics.substring(start, end + 'END:VEVENT'.length);
  }

  function buildFavoritesIcs() {
    var favs = getFavorites();
    var vevents = [];
    getEventExportData().forEach(function(entry) {
      if (favs.indexOf(entry.id) >= 0) {
        var vevent = extractVevent(entry.ics);
        if (vevent) {
          vevents.push(vevent);
        }
      }
    });
    if (vevents.length === 0) {
      return null;
    }
    return 'BEGIN:VCALENDAR\r\n' +
      'VERSION:2.0\r\n' +
      'PRODID:-//ical-events//favorites//EN\r\n' +
      vevents.join('\r\n') + '\r\n' +
      'END:VCALENDAR\r\n';
  }

  function downloadIcs(content, filename) {
    var blob = new Blob([content], { type: 'text/calendar;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function() {
      URL.revokeObjectURL(url);
    }, 1000);
  }

  function initExportFavorites() {
    var btn = document.querySelector('.export-favorites');
    if (!btn) {
      return;
    }
    btn.addEventListener('click', function() {
      var ics = buildFavoritesIcs();
      if (ics) {
        downloadIcs(ics, 'favorites.ics');
      } else {
        window.alert('No favorites yet. Click the ♡ on events to add them.');
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

  function initAll() {
    initFavorites();
    initCopyLinks();
    initExportFavorites();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  window.__getFavorites = getFavorites;
  window.__isFavorited = isFavorited;
})();
