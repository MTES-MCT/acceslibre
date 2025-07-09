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
    // ERP details page
    _clickOnSelector(item, '[data-event-type=filterClicked]')

    // Search results page
    Array.from(document.querySelectorAll('[data-event-type="shortcutClicked"]')).map((elem) => {
      if (item === elem.dataset.labelValue) {
        elem.setAttribute('checked', 'checked')
      }
    })
  })
}

export default LoadFilters
