var erp_pk = document.getElementById('widget-a11y-container').getAttribute('data-pk');
var base_url = document.getElementById('widget-a11y-container').getAttribute('data-baseurl');
var opts = {
  method: 'GET',
  headers: {}
};

fetch(base_url + '/uuid/' + erp_pk + '/widget/', opts).then(function (response) {
  return response.text();
})
  .then(function (body) {
    var container = document.getElementById('widget-a11y-container');
    var newDiv = document.createElement("div");
    newDiv.innerHTML = body;
    container.appendChild(newDiv);
    var head = document.getElementsByTagName('head')[0];
    var link = document.createElement('link');
    link.id = 1;
    link.rel = 'stylesheet';
    link.type = 'text/css';
    link.href = base_url + '/static/dist/dsfr/dist/css/dsfr.css';
    link.media = 'all';
    head.appendChild(link);

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
    });

    function showPopup() {
      const dialog = document.getElementById();
      // open dialog
      trigger.addEventListener('click', (event) => {
        event.preventDefault();
        open(dialog);
      })
    }
  });
