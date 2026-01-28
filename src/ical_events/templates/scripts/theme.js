(function() {
  'use strict';

  var COOKIE_NAME = 'events-theme';
  var DEFAULT_THEME = 'win95';
  var COOKIE_DAYS = 365;

  function setCookie(name, value, days) {
    var d = new Date();
    d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = name + '=' + encodeURIComponent(value) +
      ';expires=' + d.toUTCString() +
      ';path=/;SameSite=Lax';
  }

  function getCookie(name) {
    var prefix = name + '=';
    var parts = document.cookie.split(';');
    for (var i = 0; i < parts.length; i++) {
      var c = parts[i].trim();
      if (c.indexOf(prefix) === 0) {
        return decodeURIComponent(c.substring(prefix.length));
      }
    }
    return null;
  }

  function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    setCookie(COOKIE_NAME, theme, COOKIE_DAYS);

    var buttons = document.querySelectorAll('.theme-btn');
    buttons.forEach(function(btn) {
      var isSelected = btn.getAttribute('data-theme-value') === theme;
      btn.setAttribute('aria-checked', isSelected ? 'true' : 'false');
    });
  }

  function init() {
    var saved = getCookie(COOKIE_NAME) || DEFAULT_THEME;
    setTheme(saved);

    document.addEventListener('click', function(e) {
      var btn = e.target.closest('.theme-btn');
      if (btn) {
        var theme = btn.getAttribute('data-theme-value');
        if (theme) {
          setTheme(theme);
        }
      }
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        var btn = e.target.closest('.theme-btn');
        if (btn) {
          e.preventDefault();
          var theme = btn.getAttribute('data-theme-value');
          if (theme) {
            setTheme(theme);
          }
        }
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.__setTheme = setTheme;
})();
