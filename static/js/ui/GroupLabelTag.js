// TODO : when the group is unchecked, uncheck all the suggestions to avoid that the filter is still applied?
function _toogle_children(children) {
  let needRefresh = false

  children.forEach(function (child) {
    let parent = document.querySelector(`#${child}`).parentNode
    parent.classList.toggle('hidden')

    let inputFilter = parent.querySelector('input')
    inputFilter.checked = !inputFilter.checked

    let button = parent.querySelector('button')
    button.setAttribute('aria-pressed', true)

    needRefresh = true
  })

  return needRefresh
}

function _toogle_suggestions(suggestions) {
  if (suggestions) {
    suggestions.split(',').forEach(function (suggestion) {
      let parent = document.querySelector(`#${suggestion}`).parentNode
      parent.classList.toggle('hidden')
    })
  }
}

function ListenToshortcutLabelClicked() {
  document.addEventListener('shortcutLabelClicked', function (event) {
    let equipmentsGroup = event.detail.source
    let children = equipmentsGroup.getAttribute('data-children').split(',')
    const needRefresh = _toogle_children(children)

    _toogle_suggestions(equipmentsGroup.getAttribute('data-suggestions'))

    if (needRefresh) {
      document.dispatchEvent(new Event('filterAdded'))
    }
  })
}

export default ListenToshortcutLabelClicked
