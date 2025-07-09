function _storeFilterFromSelector(selector) {
  const activeFilters = Array.from(document.querySelectorAll(selector)).map((item) => item.innerText)
  localStorage.setItem('activeFilters', activeFilters)
}

function StoreFilters() {
  document.addEventListener('shortcutClicked', function () {
    _storeFilterFromSelector('.equipments-shortcuts button[aria-pressed=true]')
  })

  document.addEventListener('filterClicked', function () {
    _storeFilterFromSelector('.a4a-label-tag[aria-pressed=true]')
  })

  document.addEventListener('shortcutClickedFromSearch', () => {
    const activeFilters = Array.from(
      document.querySelectorAll('input[type="checkbox"][data-event-type="shortcutClicked"]:checked')
    )

    const filterValues = activeFilters.map((filter) => filter.dataset.labelValue)

    localStorage.setItem('activeFilters', filterValues)
  })
}

export default StoreFilters
