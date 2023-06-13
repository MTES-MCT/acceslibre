var erp_pk = document.getElementById('widget-a11y-container').getAttribute('data-pk');
var base_url = document.getElementById('widget-a11y-container').getAttribute('data-baseurl');
var opts = {
  method: 'GET',
  //headers: {'X-OriginUrl': window.location}
};

fetch(base_url + '/uuid/' + erp_pk + '/widget/', opts).then(function (response) {
  return response.text();
})
  .then(function (body) {
    var _paq = window._paq = window._paq || [];
    /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
    _paq.push(["trackPageView"]);
    _paq.push(["enableLinkTracking"]);
    _paq.push(['enableHeartBeatTimer']);
    _paq.push(['trackEvent', "widget", "display", true]);
    (function () {
      var u = "//stats.data.gouv.fr/";
      _paq.push(["setTrackerUrl", u + "matomo.php"]);
      _paq.push(["setSiteId", "118"]);
      var d = document, g = d.createElement("script"), s = d.getElementsByTagName("script")[0];
      g.type = "text/javascript"; g.async = true; g.defer = true; g.src = u + "matomo.js"; s.parentNode.insertBefore(g, s);
    })();

    var container = document.getElementById('widget-a11y-container');
    var newDiv = document.createElement("div");
    newDiv.innerHTML = body;
    container.appendChild(newDiv);

    const triggers = document.querySelectorAll('[aria-haspopup="dialog"]');
    const doc = document.querySelector('.js-document');
    const focusableElementsArray = [
      '[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ];
    const keyCodes = {
      tab: 9,
      enter: 13,
      escape: 27,
    };

    const open = function (dialog) {
      var _paq = window._paq = window._paq || [];
      /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
      _paq.push(["trackPageView"]);
      _paq.push(["enableLinkTracking"]);
      _paq.push(['enableHeartBeatTimer']);
      _paq.push(['trackEvent', "widget", "open", true]);
      (function () {
        var u = "//stats.data.gouv.fr/";
        _paq.push(["setTrackerUrl", u + "matomo.php"]);
        _paq.push(["setSiteId", "118"]);
      })();
      const focusableElements = dialog.querySelectorAll(focusableElementsArray);
      const firstFocusableElement = focusableElements[0];
      const lastFocusableElement = focusableElements[focusableElements.length - 1];

      dialog.setAttribute('aria-hidden', false);
      doc.setAttribute('aria-hidden', true);

      // return if no focusable element
      if (!firstFocusableElement) {
        return;
      }

      window.setTimeout(() => {
        firstFocusableElement.focus();

        // trapping focus inside the dialog
        focusableElements.forEach((focusableElement) => {
          if (focusableElement.addEventListener) {
            focusableElement.addEventListener('keydown', (event) => {
              const tab = event.which === keyCodes.tab;

              if (!tab) {
                return;
              }

              if (event.shiftKey) {
                if (event.target === firstFocusableElement) { // shift + tab
                  event.preventDefault();

                  lastFocusableElement.focus();
                }
              } else if (event.target === lastFocusableElement) { // tab
                event.preventDefault();

                firstFocusableElement.focus();
              }
            });
          }
        });
      }, 100);
    };

    const close = function (dialog, trigger) {
      dialog.setAttribute('aria-hidden', true);
      doc.setAttribute('aria-hidden', false);

      // restoring focus
      trigger.focus();
    };

    triggers.forEach((trigger) => {
      const dialog = document.getElementById(trigger.getAttribute('aria-controls'));
      const dismissTriggers = dialog.querySelectorAll('[data-dismiss]');

      // open dialog
      trigger.addEventListener('click', (event) => {
        event.preventDefault();
        open(dialog);


      });

      trigger.addEventListener('keydown', (event) => {
        if (event.which === keyCodes.enter) {
          event.preventDefault();
          open(dialog);
        }
      });

      // close dialog
      dialog.addEventListener('keydown', (event) => {
        if (event.which === keyCodes.escape) {
          close(dialog, trigger);
        }
      });

      dismissTriggers.forEach((dismissTrigger) => {
        const dismissDialog = document.getElementById(dismissTrigger.dataset.dismiss);

        dismissTrigger.addEventListener('click', (event) => {
          event.preventDefault();

          close(dismissDialog, trigger);
        });
      });

      window.addEventListener('click', (event) => {
        if (event.target === dialog) {
          close(dialog, trigger);
        }
      });
      var btn_close = document.getElementById('btn_acceslibre_close')
      btn_close.addEventListener('click', () => {
        var _paq = window._paq = window._paq || [];
        _paq.push(['trackEvent', "widget", "close", true]);
      });

      var btn_acceslibre_redirect = document.getElementById('btn_acceslibre')
      btn_acceslibre_redirect.addEventListener('click', () => {
        var _paq = window._paq = window._paq || [];
        _paq.push(['trackEvent', "widget", "redirect", true]);
      });
    });

  });

