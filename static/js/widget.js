;(function () {
  const base_url = document.querySelector('[data-baseurl]').getAttribute('data-baseurl')
  const allContainers = document.querySelectorAll('[data-pk]')
  const keyCodes = {
    tab: 9,
    enter: 13,
    escape: 27,
  }
  const focusableElementsArray = [
    '[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ]

  var itemsProcessed = 0

  function closeModal(dialog, trigger) {
    dialog.setAttribute('aria-hidden', true)
    dialog.parentNode.setAttribute('aria-hidden', false)

    // restoring focus
    trigger.focus()
  }

  function openModal(dialog) {
    var _paq = (window._paq = window._paq || [])
    /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
    _paq.push(['trackPageView'])
    _paq.push(['enableLinkTracking'])
    _paq.push(['enableHeartBeatTimer'])
    _paq.push(['trackEvent', 'widget', 'open', true])
    ;(function () {
      var u = '//stats.data.gouv.fr/'
      _paq.push(['setTrackerUrl', u + 'matomo.php'])
      _paq.push(['setSiteId', '118'])
    })()
    const focusableElements = dialog.querySelectorAll(focusableElementsArray)
    const firstFocusableElement = focusableElements[0]
    const lastFocusableElement = focusableElements[focusableElements.length - 1]

    dialog.setAttribute('aria-hidden', false)
    dialog.parentNode.setAttribute('aria-hidden', true)

    // return if no focusable element
    if (!firstFocusableElement) {
      return
    }

    window.setTimeout(() => {
      firstFocusableElement.focus()

      // trapping focus inside the dialog
      focusableElements.forEach((focusableElement) => {
        if (focusableElement.addEventListener) {
          focusableElement.addEventListener('keydown', (event) => {
            const tab = event.which === keyCodes.tab

            if (!tab) {
              return
            }

            if (event.shiftKey) {
              if (event.target === firstFocusableElement) {
                // shift + tab
                event.preventDefault()

                lastFocusableElement.focus()
              }
            } else if (event.target === lastFocusableElement) {
              // tab
              event.preventDefault()

              firstFocusableElement.focus()
            }
          })
        }
      })
    }, 100)
  }

  function loadTriggers() {
    const triggers = document.querySelectorAll('[aria-haspopup="dialog"]')

    triggers.forEach((trigger) => {
      var dialog = null
      if (triggers.length == 1) {
        // For retro compatibility purposes
        dialog = document.getElementById(trigger.getAttribute('aria-controls'))
      } else {
        const triggerPk = trigger.getAttribute('data-erp-pk')
        dialog = document.querySelector(`[data-pk="${triggerPk}"]`).querySelector('[id=dialog]')
      }
      const dismissTriggers = dialog.querySelectorAll('[data-dismiss]')

      trigger.addEventListener('click', (event) => {
        event.preventDefault()
        openModal(dialog)
      })

      trigger.addEventListener('keydown', (event) => {
        if (event.which === keyCodes.enter) {
          event.preventDefault()
          openModal(dialog)
        }
      })

      dialog.addEventListener('keydown', (event) => {
        if (event.which === keyCodes.escape) {
          closeModal(dialog, trigger)
        }
      })

      dismissTriggers.forEach((dismissTrigger) => {
        const closeTriggerPk = dismissTrigger.dataset.dismiss
        const dismissDialog = document.querySelector(`[data-pk="${closeTriggerPk}"]`).querySelector('[id=dialog]')

        dismissTrigger.addEventListener('click', (event) => {
          event.preventDefault()

          closeModal(dismissDialog, trigger)
        })
      })
    })
  }

  function _trackOnClick(element, trackingString) {
    element.addEventListener('click', () => {
      var _paq = (window._paq = window._paq || [])
      _paq.push(['trackEvent', 'widget', trackingString, true])
    })
  }

  function trackEventOnClose() {
    var close_buttons = document.querySelectorAll('.btn_acceslibre_close')
    close_buttons.forEach(function (close_button) {
      _trackOnClick(close_button, 'close')
    })
  }

  function trackEventOnRedirect() {
    var redirect_buttons = document.querySelectorAll('.btn_acceslibre')
    redirect_buttons.forEach(function (redirect_button) {
      _trackOnClick(redirect_button, 'redirect')
    })
  }

  function finishSetup() {
    loadTriggers()
    trackEventOnClose()
    trackEventOnRedirect()
  }

  allContainers.forEach(function (container) {
    var erp_pk = container.getAttribute('data-pk')
    fetch(base_url + '/uuid/' + erp_pk + '/widget/')
      .then(function (response) {
        return response.text()
      })
      .then(function (body) {
        var _paq = (window._paq = window._paq || [])
        /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
        _paq.push(['trackPageView'])
        _paq.push(['enableLinkTracking'])
        _paq.push(['enableHeartBeatTimer'])
        _paq.push(['trackEvent', 'widget', 'display', true])
        ;(function () {
          var u = '//stats.data.gouv.fr/'
          _paq.push(['setTrackerUrl', u + 'matomo.php'])
          _paq.push(['setSiteId', '118'])
          var d = document,
            g = d.createElement('script'),
            s = d.getElementsByTagName('script')[0]
          g.type = 'text/javascript'
          g.async = true
          g.defer = true
          g.src = u + 'matomo.js'
          s.parentNode.insertBefore(g, s)
        })()

        var container = document.querySelector(`[data-pk="${erp_pk}"]`)
        var newDiv = document.createElement('div')
        newDiv.innerHTML = body
        container.appendChild(newDiv)
        itemsProcessed++
        if (itemsProcessed == allContainers.length) {
          finishSetup()
        }
      })
  })
})()
