import url from '../url.js'

function _toggleHidden(elt, display) {
  const isClone = elt.querySelector('label').getAttribute('for').includes('-clone')
  if (display) {
    elt.classList.remove('hidden')
  } else if (!isClone) {
    // never hide a clone, the modal should contain all equipments
    elt.classList.add('hidden')
  }
}

function _toggleChild(parent, display = true) {
  let inputFilter = parent.querySelector('input')
  inputFilter.checked = display
  _toggleHidden(parent, display)

  let button = parent.querySelector('button')
  button.setAttribute('aria-pressed', display)
}

function _toggleChildren(children, display = true) {
  children.forEach(function (child) {
    _toggleChild(document.querySelector(`#${child}`).parentNode, display)
    _toggleChild(document.querySelector(`#${child}-clone`).parentNode, display)
  })
}

function _toggleSuggestions(shortcut, display = true) {
  shortcut = shortcut.parentNode.querySelector('button')
  let suggestions = shortcut.getAttribute('data-suggestions')
  if (!suggestions) {
    return
  }
  suggestions = suggestions.split(',')

  suggestions.forEach(function (suggestion) {
    let parent = document.querySelector(`#${suggestion}-suggestion`).parentNode
    _toggleHidden(parent, display)
  })
}

function _toggleDefaultSuggestion(display) {
  document.querySelectorAll('.default-suggestion').forEach(function (btn) {
    let equipmentSlug = btn.parentNode.querySelector('label').getAttribute('for').replace('-suggestion', '')
    let equipmentAlreadyChecked = document.querySelector(`input[name=equipments][value=${equipmentSlug}]:checked`)
    if (!equipmentAlreadyChecked) {
      _toggleHidden(btn.parentNode, display)
    }
  })
}

function _checkForShortcutToHide() {
  // If all equipments of a shortcut are unchecked, the shortcut and its suggestions should be hidden.
  let shortcutsChecked = document.querySelectorAll('input[name=equipments_shortcuts]:checked')
  shortcutsChecked.forEach(function (shortcut) {
    let allChildrenUnchecked = true
    let children = shortcut.parentNode.querySelector('button').getAttribute('data-children').split(',')
    children.forEach(function (child) {
      if (allChildrenUnchecked) {
        let displayed = document.querySelector(`input[value=${child}]`).checked
        if (displayed) {
          allChildrenUnchecked = false
        }
      }
    })

    if (allChildrenUnchecked) {
      _toggleSuggestions(shortcut, false)
      shortcut.checked = false
      shortcut.parentNode.querySelector('button').setAttribute('aria-pressed', false)
      url.refreshSearchURL()
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
      if (shortcut.parentNode.querySelector('button').getAttribute('data-suggestions').includes(equipmentSlug)) {
        suggestionToShow = true
      }
    }
  })

  if (suggestionToShow) {
    let suggestion = document.querySelector(`#${equipmentSlug}-suggestion`)
    _toggleHidden(suggestion.parentNode, true)
  }
}

function listenToLabelEvents() {
  const featureEnabled = document.querySelectorAll('.row.equipments').length
  if (!featureEnabled) {
    return
  }

  let shortcutsChecked = document.querySelectorAll('input[name=equipments_shortcuts]:checked')
  if (!shortcutsChecked.length) {
    _toggleDefaultSuggestion(true)
  } else {
    shortcutsChecked.forEach(function (shortcut) {
      _toggleSuggestions(shortcut, true)
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
    let children = equipmentsShortcut.getAttribute('data-children').split(',')
    _toggleChildren(children, display)
    _toggleSuggestions(equipmentsShortcut, display)

    if (children.length) {
      document.dispatchEvent(new Event('filterChanged'))
    }
  })

  document.addEventListener('equipmentClicked', function (event) {
    let equipmentSlug = event.detail.source.parentNode.querySelector('label').getAttribute('for').replace('-clone', '')
    let display = event.detail.source.getAttribute('aria-pressed') === 'true'
    _toggleChildren([equipmentSlug], display)

    if (!display) {
      _checkForShortcutToHide()
      _checkForSuggestionToShow(equipmentSlug)
    }
    document.dispatchEvent(new Event('filterChanged'))
  })

  document.addEventListener('suggestionClicked', function (event) {
    event.preventDefault()
    let equipmentSlug = event.detail.source.parentNode
      .querySelector('label')
      .getAttribute('for')
      .replace('-suggestion', '')
    _toggleChildren([equipmentSlug], true)
    _toggleChild(event.detail.source.parentNode, false)
    document.dispatchEvent(new Event('filterChanged'))
  })

  document.querySelector('#remove-all-filters').addEventListener('click', function () {
    let equipments = document.querySelectorAll('.equipments-selected button[aria-pressed=true]')
    equipments.forEach(function (equipment) {
      let equipmentSlug = equipment.parentNode.querySelector('label').getAttribute('for').replace('-clone', '')
      _toggleChildren([equipmentSlug], false)
    })
    if (equipments.length) {
      _checkForShortcutToHide()
      document.dispatchEvent(new Event('filterChanged'))
    }
  })

  document.addEventListener('filterChanged', function () {
    let nbSuggestionDisplayed = document.querySelectorAll(
      '.equipments-suggestions > span:not(.hidden):not(.section-text)'
    ).length
    if (nbSuggestionDisplayed == 0) {
      _toggleDefaultSuggestion(true)
    }
  })
}

export default listenToLabelEvents
