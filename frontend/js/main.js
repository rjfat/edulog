// EduLog - shared frontend behaviour.
// Progressive enhancement only: every page works with JavaScript disabled.

(function () {
  'use strict';

  /* --- Mobile sidebar ---------------------------------------------------- */

  function initSidebar() {
    var sidebar = document.getElementById('sidebar');
    var toggle = document.querySelector('.sidebar-toggle');
    if (!sidebar || !toggle) return;

    var backdrop = null;

    function isOpen() {
      return sidebar.getAttribute('data-open') === 'true';
    }

    function open() {
      sidebar.setAttribute('data-open', 'true');
      toggle.setAttribute('aria-expanded', 'true');

      backdrop = document.createElement('button');
      backdrop.className = 'sidebar-backdrop';
      backdrop.setAttribute('aria-label', 'Close navigation menu');
      backdrop.addEventListener('click', close);
      document.body.appendChild(backdrop);

      var firstLink = sidebar.querySelector('.nav-link');
      if (firstLink) firstLink.focus();
    }

    function close() {
      sidebar.setAttribute('data-open', 'false');
      toggle.setAttribute('aria-expanded', 'false');
      if (backdrop) {
        backdrop.remove();
        backdrop = null;
      }
      toggle.focus();
    }

    toggle.addEventListener('click', function () {
      if (isOpen()) close();
      else open();
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && isOpen()) close();
    });

    // Reset state when the layout goes back to the two-column desktop grid.
    var desktop = window.matchMedia('(min-width: 769px)');
    desktop.addEventListener('change', function (event) {
      if (event.matches && isOpen()) close();
    });
  }

  /* --- Password visibility ----------------------------------------------- */

  var EYE = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>';
  var EYE_OFF = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9.9 4.24A9.1 9.1 0 0 1 12 4c6.4 0 10 7 10 7a17.6 17.6 0 0 1-2.7 3.72M6.6 6.6A17.6 17.6 0 0 0 2 11s3.6 7 10 7a9.1 9.1 0 0 0 4.1-.94"/><path d="m2 2 20 20"/><path d="M14.1 14.1a3 3 0 1 1-4.2-4.2"/></svg>';

  function initPasswordToggles() {
    var fields = document.querySelectorAll('.password-field');

    Array.prototype.forEach.call(fields, function (field) {
      var input = field.querySelector('input[type="password"]');
      if (!input) return;

      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'password-toggle';
      button.innerHTML = EYE;
      // Icon-only control, so it needs its own accessible name.
      button.setAttribute('aria-label', 'Show password');
      button.setAttribute('aria-pressed', 'false');

      button.addEventListener('click', function () {
        var hidden = input.type === 'password';
        input.type = hidden ? 'text' : 'password';
        button.innerHTML = hidden ? EYE_OFF : EYE;
        button.setAttribute('aria-label', hidden ? 'Hide password' : 'Show password');
        button.setAttribute('aria-pressed', String(hidden));
      });

      field.appendChild(button);
      // Leave room for the button so long values do not run underneath it.
      input.style.paddingRight = '3rem';
    });
  }

  /* --- Submit feedback ---------------------------------------------------- */

  function initSubmitFeedback() {
    var forms = document.querySelectorAll('form[data-submit-feedback]');

    Array.prototype.forEach.call(forms, function (form) {
      form.addEventListener('submit', function () {
        var button = form.querySelector('button[type="submit"]');
        if (!button || button.dataset.busy === 'true') return;

        button.dataset.busy = 'true';
        button.dataset.idleLabel = button.textContent;
        button.textContent = button.dataset.busyLabel || 'Working...';
        // aria-disabled rather than disabled, so the value still posts.
        button.setAttribute('aria-disabled', 'true');
      });
    });
  }

  /* --- Error summary focus ------------------------------------------------ */

  function focusErrorSummary() {
    var summary = document.querySelector('.error-summary');
    if (summary) summary.focus();
  }

  document.addEventListener('DOMContentLoaded', function () {
    initSidebar();
    initPasswordToggles();
    initSubmitFeedback();
    focusErrorSummary();
  });
})();
