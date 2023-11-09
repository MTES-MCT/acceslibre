import url from '../url.js'

function _show(elt) {
  elt.classList.remove('hidden')
}

function _toggleHidden(elt, display) {
  const isClone = elt.querySelector('label').getAttribute('for').includes('-clone')
  if (display) {
    _show(elt)
  } else if (!isClone) {
    // never hide a clone, the modal should contain all equipments
    elt.classList.add('hidden')
  }
}

function _toggleChild(parent, display = true, keepItInPlace = false) {
  parent.querySelector('input').checked = display
  if (keepItInPlace) {
    _show(parent)
  } else {
    _toggleHidden(parent, display)
  }

  const button = parent.querySelector('button')
  if (button) {
    button.setAttribute('aria-pressed', display)
  }
}

function _toggleChildren(children, display = true, keepItInPlace = false) {
  children.forEach(function (child) {
    _toggleChild(document.querySelector(`#${child}`).parentNode, display, keepItInPlace)
    _toggleChild(document.querySelector(`#${child}-clone`).parentNode, display, keepItInPlace)
  })
}

function _toggleShortcutSuggestions(shortcut, display = true) {
  shortcut = shortcut.parentNode.querySelector('button')
  let suggestions = shortcut.getAttribute('data-suggestions')
  if (!suggestions) {
    return
  }
  suggestions = suggestions.split(',')

  suggestions.forEach(function (suggestion) {
    let parent = document.querySelector(`#${suggestion}`).parentNode
    var wasChecked = parent.querySelector('button').getAttribute('aria-pressed') === 'true'
    if (!wasChecked || display) {
      _toggleHidden(parent, display)
    }
  })
}

function _toggleDefaultSuggestion(display) {
  document.querySelectorAll('.default-suggestion').forEach(function (btn) {
    let equipmentSlug = btn.parentNode.querySelector('label').getAttribute('for')
    let equipmentAlreadyChecked = document.querySelector(`input[name=equipments][value=${equipmentSlug}]:checked`)
    if (!equipmentAlreadyChecked) {
      _toggleHidden(btn.parentNode, display)
    }
  })
}

function _checkForSuggestionToShow(equipmentSlug) {
  // If an equipment is unchecked and if it is part of a checked shortcut, it should reappear in suggestion list
  let shortcutsChecked = document.querySelectorAll('input[name=equipments_shortcuts]:checked')
  if (!shortcutsChecked.length) {
    return
  }

  let suggestionToShow = false
  shortcutsChecked.forEach(function (shortcut) {
    if (!suggestionToShow) {
      if (
        (shortcut.parentNode.querySelector('button').getAttribute('data-suggestions') || []).includes(equipmentSlug)
      ) {
        suggestionToShow = true
      }
    }
  })

  if (suggestionToShow) {
    let suggestion = document.querySelector(`#${equipmentSlug}`)
    _toggleHidden(suggestion.parentNode, true)
  }
}

function listenToLabelEvents() {
  const featureEnabled = document.querySelectorAll('.row.equipments').length
  if (!featureEnabled) {
    return
  }

  // Initial map loading, trigger an API search request.
  document.dispatchEvent(new Event('filterChanged'))

  let shortcutsChecked = document.querySelectorAll('input[name=equipments_shortcuts]:checked')
  if (!shortcutsChecked.length) {
    _toggleDefaultSuggestion(true)
  } else {
    shortcutsChecked.forEach(function (shortcut) {
      _toggleShortcutSuggestions(shortcut, true)
    })
  }

  document.addEventListener('shortcutClicked', function (event) {
    let equipmentsShortcut = event.detail.source
    let display = equipmentsShortcut.getAttribute('aria-pressed') === 'true'
    if (display) {
      _toggleDefaultSuggestion(false)
    }
    let input = equipmentsShortcut.parentNode.querySelector('input')
    input.checked = display
    let children = (equipmentsShortcut.getAttribute('data-children') || '').split(',').filter((r) => r)
    _toggleChildren(children, display)
    _toggleShortcutSuggestions(equipmentsShortcut, display)

    document.dispatchEvent(new Event('filterChanged'))
  })

  document.addEventListener('equipmentClicked', function (event) {
    let parent = event.detail.source.parentNode
    let equipmentSlug = parent.querySelector('label').getAttribute('for').replace('-clone', '')
    const isClone = parent.querySelector('label').getAttribute('for').includes('-clone')
    let display = true
    if (isClone) {
      display = parent.querySelector('input[type=checkbox]').checked
    } else {
      display = event.detail.source.getAttribute('aria-pressed') === 'true'
    }

    _toggleChildren([equipmentSlug], display, true)

    if (!display) {
      _checkForSuggestionToShow(equipmentSlug)
    }

    if (!(event.skipRefresh && event.skipRefresh === true)) {
      document.dispatchEvent(new Event('filterChanged'))
    }
  })

  document.addEventListener('suggestionClicked', function (event) {
    event.preventDefault()
    let equipmentSlug = event.detail.source.parentNode.querySelector('label').getAttribute('for')
    _toggleChildren([equipmentSlug], true)
    _toggleChild(event.detail.source.parentNode, false, true)
    document.dispatchEvent(new Event('filterChanged'))
  })

  document.querySelector('#remove-all-filters').addEventListener('click', function () {
    let equipments = document.querySelectorAll('.equipments-selected button')
    equipments.forEach(function (equipment) {
      let equipmentSlug = equipment.parentNode.querySelector('label').getAttribute('for')
      _toggleChildren([equipmentSlug], false)
    })

    let shortcuts = document.querySelectorAll('.equipments-shortcuts button[aria-pressed=true]')
    shortcuts.forEach(function (shortcut) {
      shortcut.parentNode.querySelector('input').checked = false
      shortcut.parentNode.querySelector('button').setAttribute('aria-pressed', false)
      url.refreshSearchURL()
    })
    document.dispatchEvent(new Event('filterChanged'))
  })

  document.addEventListener('filterChanged', function () {
    let nbTagDisplayed = document.querySelectorAll(
      '.equipments-selected > span:not(.hidden):not(.section-text)'
    ).length
    if (nbTagDisplayed == 0) {
      _toggleDefaultSuggestion(true)
    }
  })
}

export default listenToLabelEvents
