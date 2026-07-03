(function() {
  'use strict';

  var COOKIE_NAME = 'events-theme';
  var DEFAULT_THEME = 'win95';
  var DEFAULT_DARK_THEME = 'phosphor';
  var COOKIE_DAYS = 365;

  function validThemes() {
    var buttons = document.querySelectorAll('.theme-btn');
    var themes = [];
    buttons.forEach(function(btn) {
      themes.push(btn.getAttribute('data-theme-value'));
    });
    return themes;
  }

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

  function getThemeFromUrl() {
    try {
      var params = new URLSearchParams(window.location.search);
      return params.get('theme');
    } catch (e) {
      return null;
    }
  }

  function updateUrl(theme) {
    if (!window.history || !window.history.replaceState) {
      return;
    }
    try {
      var url = new URL(window.location.href);
      url.searchParams.set('theme', theme);
      window.history.replaceState(null, '', url.toString());
    } catch (e) {
      // URL API unavailable — skip deep-link update
    }
  }

  function setTheme(theme, skipUrl) {
    document.body.setAttribute('data-theme', theme);
    setCookie(COOKIE_NAME, theme, COOKIE_DAYS);
    if (!skipUrl) {
      updateUrl(theme);
    }

    var buttons = document.querySelectorAll('.theme-btn');
    buttons.forEach(function(btn) {
      var isSelected = btn.getAttribute('data-theme-value') === theme;
      btn.setAttribute('aria-checked', isSelected ? 'true' : 'false');
    });
  }

  function initialTheme() {
    var themes = validThemes();
    var fromUrl = getThemeFromUrl();
    if (fromUrl && themes.indexOf(fromUrl) >= 0) {
      return fromUrl;
    }
    var saved = getCookie(COOKIE_NAME);
    if (saved && themes.indexOf(saved) >= 0) {
      return saved;
    }
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return DEFAULT_DARK_THEME;
    }
    return DEFAULT_THEME;
  }

  function init() {
    setTheme(initialTheme(), true);

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
