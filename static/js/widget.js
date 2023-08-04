;(function () {
  const baseURL = document.querySelector('[data-baseurl]').getAttribute('data-baseurl')
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

  function getTracker() {
    if (window.AccesLibreMatomoTracker) {
      return window.AccesLibreMatomoTracker
    } else {
      // In case Matomo is not available (eg: Adblock) return a mock to avoid errors
      // in the rest of the code
      return {
        trackEvent: function () {},
      }
    }
  }

  function openModal(dialog) {
    getTracker().trackEvent('widget', 'open', true)
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
      getTracker().trackEvent('widget', trackingString, true)
    })
  }

  function trackEventOnClose() {
    var closeButtons = document.querySelectorAll('.btn_acceslibre_close')
    closeButtons.forEach(function (closeButton) {
      _trackOnClick(closeButton, 'close')
    })
  }

  function trackEventOnRedirect() {
    var redirectButtons = document.querySelectorAll('.btn_acceslibre')
    redirectButtons.forEach(function (redirectButton) {
      _trackOnClick(redirectButton, 'redirect')
    })
  }

  function finishSetup() {
    loadTriggers()
    trackEventOnClose()
    trackEventOnRedirect()
  }

  function setupAnalytics() {
    var u = 'https://stats.data.gouv.fr/'
    var matomoTracker = Matomo.getTracker(u + 'matomo.php', 118)
    window.AccesLibreMatomoTracker = matomoTracker
    matomoTracker.trackPageView()
    matomoTracker.enableLinkTracking()
    matomoTracker.enableHeartBeatTimer()
  }
  function setupAnalyticsScript() {
    var u = 'https://stats.data.gouv.fr/'
    ;(function () {
      var d = document,
        g = d.createElement('script'),
        s = d.getElementsByTagName('script')[0]
      g.type = 'text/javascript'
      g.async = true
      g.defer = true
      g.src = u + 'matomo.js'
      s.parentNode.insertBefore(g, s)

      g.onreadystatechange = setupAnalytics
      g.onload = setupAnalytics
    })()
  }

  setupAnalyticsScript()

  allContainers.forEach(function (container) {
    var erpPK = container.getAttribute('data-pk')
    fetch(baseURL + '/uuid/' + erpPK + '/widget/')
      .then(function (response) {
        return response.text()
      })
      .then(function (body) {
        getTracker().trackEvent('widget', 'display', true)
        var container = document.querySelector(`[data-pk="${erpPK}"]`)
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
