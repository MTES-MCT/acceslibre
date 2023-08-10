function _toggleChild(parent) {
  // TODO would be safer to explicitely hide / display rather than toggle, we would avoid a desync
  let inputFilter = parent.querySelector('input')
  inputFilter.checked = !inputFilter.checked

  if (inputFilter.checked) {
    parent.classList.remove('hidden')
  }

  let button = parent.querySelector('button')
  button.setAttribute('aria-pressed', inputFilter.checked)
}

function _toggleChildren(children) {
  children.forEach(function (child) {
    _toggleChild(document.querySelector(`#${child}`).parentNode)
    _toggleChild(document.querySelector(`#${child}-clone`).parentNode)
  })
}

function _toggleSuggestions(shortcut, suggestions) {
  suggestions.forEach(function (suggestion) {
    let parent = document.querySelector(`#${suggestion}`).parentNode
    let shortcutJustUnchecked = shortcut.parentNode.querySelector('button').getAttribute('aria-pressed') !== 'true'
    let suggestionWasChecked = parent.querySelector('button').getAttribute('aria-pressed') === 'true'
    if (shortcutJustUnchecked && suggestionWasChecked) {
      _toggleChildren([suggestion])
    }

    parent.classList.toggle('hidden')
  })
}
function listenToLabelEvents() {
  document.addEventListener('shortcutLabelClicked', function (event) {
    let equipmentsShortcut = event.detail.source
    let children = equipmentsShortcut.getAttribute('data-children').split(',')
    let suggestions = equipmentsShortcut.getAttribute('data-suggestions')
    _toggleChildren(children)

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
    _toggleChildren([equipmentSlug])
    document.dispatchEvent(new Event('filterAdded'))
  })
}

export default listenToLabelEvents
