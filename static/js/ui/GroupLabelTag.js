function _toggleChild(parent, toogleHidden = false) {
  if (toogleHidden) {
    parent.classList.toggle('hidden')
  }

  let inputFilter = parent.querySelector('input')
  inputFilter.checked = !inputFilter.checked

  let button = parent.querySelector('button')
  button.setAttribute('aria-pressed', button.getAttribute('aria-pressed') != 'true')
}

function _toggleChildren(children) {
  let needRefresh = false

  children.forEach(function (child) {
    _toggleChild(document.querySelector(`#${child}`).parentNode, true)
    _toggleChild(document.querySelector(`#${child}-clone`).parentNode, false)

    needRefresh = true
  })

  return needRefresh
}

function _toggleSuggestions(suggestions) {
  if (suggestions) {
    suggestions.forEach(function (suggestion) {
      let parent = document.querySelector(`#${suggestion}`).parentNode
      parent.classList.toggle('hidden')
    })
  }
}

function ListenToshortcutLabelClicked() {
  document.addEventListener('shortcutLabelClicked', function (event) {
    let equipmentsShortcut = event.detail.source
    let children = equipmentsShortcut.getAttribute('data-children').split(',')
    let suggestions = equipmentsShortcut.getAttribute('data-suggestions')
    if (suggestions) {
      suggestions = suggestions.split(',')
    }
    const needRefresh = _toggleChildren(children)

    _toggleSuggestions(suggestions)

    if (needRefresh) {
      document.dispatchEvent(new Event('filterAdded'))
    }
  })
}

export default ListenToshortcutLabelClicked
