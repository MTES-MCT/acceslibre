function _toggleChild(parent, display = true) {
  let inputFilter = parent.querySelector('input')
  inputFilter.checked = display

  if (display) {
    parent.classList.remove('hidden')
  }

  let button = parent.querySelector('button')
  button.setAttribute('aria-pressed', display)
}

function _toggleChildren(children, display = true) {
  children.forEach(function (child) {
    _toggleChild(document.querySelector(`#${child}`).parentNode, display)
    _toggleChild(document.querySelector(`#${child}-clone`).parentNode, display)
  })
}

function _toggleSuggestions(shortcut, suggestions) {
  suggestions.forEach(function (suggestion) {
    let parent = document.querySelector(`#${suggestion}`).parentNode
    let shortcutJustUnchecked = shortcut.parentNode.querySelector('button').getAttribute('aria-pressed') !== 'true'
    let suggestionWasChecked = parent.querySelector('button').getAttribute('aria-pressed') === 'true'
    if (shortcutJustUnchecked && suggestionWasChecked) {
      _toggleChildren([suggestion], !shortcutJustUnchecked)
    }

    parent.classList.toggle('hidden')
  })
}

function _checkForShortcutToHide() {
  let shortcutsDisplayed = document.querySelectorAll('input[name=equipments_shortcuts]:checked')
  shortcutsDisplayed.forEach(function (shortcut) {
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
      shortcut.checked = false
      shortcut.parentNode.querySelector('button').setAttribute('aria-pressed', false)
    }
  })
}

function listenToLabelEvents() {
  document.addEventListener('shortcutClicked', function (event) {
    let equipmentsShortcut = event.detail.source
    let display = equipmentsShortcut.getAttribute('aria-pressed') === 'true'
    let input = equipmentsShortcut.parentNode.querySelector('input')
    input.checked = display
    let children = equipmentsShortcut.getAttribute('data-children').split(',')
    let suggestions = equipmentsShortcut.getAttribute('data-suggestions')
    _toggleChildren(children, display)

    if (suggestions) {
      suggestions = suggestions.split(',')
      _toggleSuggestions(equipmentsShortcut, suggestions)
    }

    if (children.length) {
      document.dispatchEvent(new Event('filterChanged'))
    }
  })

  document.addEventListener('equipmentClicked', function (event) {
    let equipmentSlug = event.detail.source.parentNode.querySelector('label').getAttribute('for').replace('-clone', '')
    let display = event.detail.source.getAttribute('aria-pressed') === 'true'
    _toggleChildren([equipmentSlug], display)
    document.dispatchEvent(new Event('filterChanged'))

    if (!display) {
      _checkForShortcutToHide()
    }
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
}

export default listenToLabelEvents
