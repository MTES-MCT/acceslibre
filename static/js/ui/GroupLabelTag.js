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
function listenToLabelEvents() {
  document.addEventListener('shortcutLabelClicked', function (event) {
    let equipmentsShortcut = event.detail.source
    let children = equipmentsShortcut.getAttribute('data-children').split(',')
    let suggestions = equipmentsShortcut.getAttribute('data-suggestions')
    _toggleChildren(children, equipmentsShortcut.getAttribute('aria-pressed') === 'true')

    if (suggestions) {
      suggestions = suggestions.split(',')
      _toggleSuggestions(equipmentsShortcut, suggestions)
    }

    if (children) {
      document.dispatchEvent(new Event('filterAdded'))
    }
  })

  document.addEventListener('equipmentClicked', function (event) {
    let equipmentSlug = event.detail.source.parentNode.querySelector('label').getAttribute('for').replace('-clone', '')
    _toggleChildren([equipmentSlug], event.detail.source.getAttribute('aria-pressed') === 'true')
    document.dispatchEvent(new Event('filterAdded'))
  })
}

export default listenToLabelEvents
