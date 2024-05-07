function _storeFilterFromSelector(selector) {
  const activeFilters = Array.from(document.querySelectorAll(selector)).map((item) => item.innerText)
  localStorage.setItem('activeFilters', activeFilters)
}

function StoreFilters() {
  document.addEventListener('shortcutClicked', function (event) {
    _storeFilterFromSelector('.equipments-shortcuts button[aria-pressed=true]')
  })

  document.addEventListener('filterClicked', function (event) {
    _storeFilterFromSelector('.a4a-label-tag[aria-pressed=true]')
  })
}

export default StoreFilters
