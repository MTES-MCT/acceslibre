import url from '../url.js'

function _toggleChild(input, isChecked = true) {
  console.log('toggleChild', { input, isChecked })
  input.checked = isChecked
}

function _toggleChildren(children, isChecked = true) {
  console.log('toggleChildren', children)

  children.forEach(function (child) {
    // _toggleChild(document.querySelector(`#${child}`).parentNode, isChecked, keepItInPlace)
    // _toggleChild(document.querySelector(`#${child}-clone`), isChecked)
    _toggleChild(document.querySelector(`#${child}`), isChecked)
  })
}

function _toggleShortcutFilters(shortcut, isChecked = true) {
  let suggestions = shortcut.getAttribute('data-children')

  if (!suggestions) {
    return
  }

  suggestions = suggestions.split(',')

  suggestions.forEach(function (suggestion) {
    let input = document.querySelector(`#${suggestion}-clone`)

    input.checked = isChecked
    // var wasChecked = parent.querySelector('button').getAttribute('aria-pressed') === 'true'
    // if (!wasChecked || display) {
    //   _toggleHidden(parent, display)
    // }
  })
}

function _toggleDefaultSuggestion(display) {
  // document.querySelectorAll('.default-suggestion').forEach(function (btn) {
  // let equipmentSlug = btn.parentNode.querySelector('label').getAttribute('for')
  // let equipmentAlreadyChecked = document.querySelector(`input[name=equipments][value=${equipmentSlug}]:checked`)
  // if (!equipmentAlreadyChecked) {
  //   _toggleHidden(btn.parentNode, display)
  // }
  // })
}

// function _checkForSuggestionToShow(equipmentSlug) {
//   // If an equipment is unchecked and if it is part of a checked shortcut, it should reappear in suggestion list
//   let shortcutsChecked = document.querySelectorAll('input[name=equipments_shortcuts]:checked')
//   if (!shortcutsChecked.length) {
//     return
//   }
//
//   let suggestionToShow = false
//   shortcutsChecked.forEach(function (shortcut) {
//     if (!suggestionToShow) {
//       if (
//         (shortcut.parentNode.querySelector('button').getAttribute('data-suggestions') || []).includes(equipmentSlug)
//       ) {
//         suggestionToShow = true
//       }
//     }
//   })
//
//   if (suggestionToShow) {
//     let suggestion = document.querySelector(`#${equipmentSlug}`)
//     _toggleHidden(suggestion.parentNode, true)
//   }
// }

function listenToLabelEvents() {
  const featureEnabled = document.querySelectorAll('[data-shortcuts-enabled="1"]')?.length > 0

  console.log({ featureEnabled })
  if (!featureEnabled) {
    return
  }

  // Initial map loading, trigger an API search request.
  document.dispatchEvent(new Event('filterChanged'))

  // let shortcutsChecked = document.querySelectorAll('input[name=equipments_shortcuts]:checked')
  // console.log({shortcutsChecked})
  // if (!shortcutsChecked.length) {
  //   _toggleDefaultSuggestion(true)
  // } else {
  //   shortcutsChecked.forEach(function (shortcut) {
  //     _toggleShortcutFilters(shortcut, true)
  //   })
  // }

  document.addEventListener('shortcutClicked', function (event) {
    // alert('test')
    console.log('shortcutClicked', event)

    let equipmentsShortcut = event.detail.source

    let isChecked = equipmentsShortcut.checked

    _toggleDefaultSuggestion(isChecked)

    // let input = equipmentsShortcut.parentNode.querySelector('input')
    // input.checked = isChecked
    // let children = (equipmentsShortcut.getAttribute('data-children') || '').split(',').filter((r) => r)
    // _toggleChildren(children, isChecked)

    _toggleShortcutFilters(equipmentsShortcut, isChecked)

    document.dispatchEvent(new Event('filterChanged'))
  })

  document.addEventListener('equipmentClicked', function (event) {
    console.log('equipmentClicked', event)
    // let parent = event.detail.source.parentNode
    // let equipmentSlug = parent.querySelector('label').getAttribute('for').replace('-clone', '')
    // const isClone = parent.querySelector('label').getAttribute('for').includes('-clone')

    // let display = true
    // if (isClone) {
    //   display = parent.querySelector('input[type=checkbox]').checked
    // } else {
    //   display = event.detail.source.getAttribute('aria-pressed') === 'true'
    // }

    // _toggleChildren([equipmentSlug], display, true)

    // if (!display) {
    //   _checkForSuggestionToShow(equipmentSlug)
    // }
    // url.refreshSearchURL()

    if (!(event.skipRefresh && event.skipRefresh === true)) {
      document.dispatchEvent(new Event('filterChanged'))
    }
  })
  //
  // document.addEventListener('suggestionClicked', function (event) {
  //   console.log('suggestion clicked')
  //   // event.preventDefault()
  //
  //   let equipmentSlug = event.detail.source.parentNode.querySelector('label').getAttribute('for')
  //
  //   _toggleChildren([equipmentSlug], true)
  //   _toggleChild(event.detail.source.parentNode, false, true)
  //
  //   document.dispatchEvent(new Event('filterChanged'))
  // })

  document.querySelector('#remove-all-filters').addEventListener('click', function () {
    const shortcutFilters = document.querySelectorAll('.equipments-shortcuts input[type="checkbox"]')
    const filters = document.querySelectorAll('.equipments-selected input[type="checkbox"]')

    filters.forEach((filter) => (filter.checked = false))
    shortcutFilters.forEach((filter) => (filter.checked = false))
    url.refreshSearchURL()

    // const equipments = document.querySelectorAll('.equipments-selected button')
    //
    // equipments.forEach(function (equipment) {
    //   const equipmentSlug = equipment.parentNode.querySelector('label').getAttribute('for')
    //
    //   console.log({equipmentSlug})
    //   _toggleChildren([equipmentSlug], false)
    // })

    // let shortcuts = document.querySelectorAll('.equipments-shortcuts button[aria-pressed=true]')
    // shortcuts.forEach(function (shortcut) {
    //   shortcut.parentNode.querySelector('input').checked = false
    //   shortcut.parentNode.querySelector('button').setAttribute('aria-pressed', false)
    //   url.refreshSearchURL()
    // })
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
