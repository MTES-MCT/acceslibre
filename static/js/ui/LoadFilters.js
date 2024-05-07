function _clickOnSelector(filter, selector) {
  document.querySelectorAll(selector).forEach((button) => {
    if (filter === button.innerText) {
      button.click()
    }
  })
}

function LoadFilters() {
  const activeFilters = localStorage.getItem('activeFilters')

  if (!activeFilters) {
    return
  }

  activeFilters.split(',').forEach((item) => {
    _clickOnSelector(item, '[data-event-type=filterClicked]') // ERP details page
    _clickOnSelector(item, '[data-event-type=shortcutClicked]') // Search results page
  })
}

export default LoadFilters
