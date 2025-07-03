import url from '../url.js'

function _toggleShortcutFilters(shortcut, isChecked = true) {
  let suggestions = shortcut.getAttribute('data-children')

  if (!suggestions) {
    return
  }

  suggestions = suggestions.split(',')

  suggestions.forEach(function (suggestion) {
    let input = document.querySelector(`#${suggestion}-clone`)

    input.checked = isChecked
  })
}

function listenToLabelEvents() {
  const featureEnabled = document.querySelectorAll('[data-shortcuts-enabled="1"]')?.length > 0

  if (!featureEnabled) {
    return
  }

  // Initial map loading, trigger an API search request.
  document.dispatchEvent(new Event('filterChanged'))
  document.addEventListener('shortcutClicked', function (event) {
    let equipmentsShortcut = event.detail.source
    let isChecked = equipmentsShortcut.checked

    _toggleShortcutFilters(equipmentsShortcut, isChecked)

    document.dispatchEvent(new Event('filterChanged'))
  })

  document.addEventListener('equipmentClicked', function (event) {
    if (!(event.skipRefresh && event.skipRefresh === true)) {
      document.dispatchEvent(new Event('filterChanged'))
    }
  })

  document.querySelector('#remove-all-filters').addEventListener('click', function () {
    const shortcutFilters = document.querySelectorAll('.equipments-shortcuts input[type="checkbox"]')
    const filters = document.querySelectorAll('.equipments-selected input[type="checkbox"]')

    filters.forEach((filter) => (filter.checked = false))
    shortcutFilters.forEach((filter) => (filter.checked = false))
    url.refreshSearchURL()

    document.dispatchEvent(new Event('filterChanged'))
  })
}

export default listenToLabelEvents
