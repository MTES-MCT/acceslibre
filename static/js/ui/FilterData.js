function hasVisibleChildren(element) {
  let visibleChildren = false
  Array.from(element.children).forEach(function (child) {
    if (child.offsetWidth > 0) {
      visibleChildren = true
    }
  })
  return visibleChildren
}

function listenToFilterClicked(root) {
  const dataToToogle = root.querySelectorAll('[data-filters]')
  document.addEventListener('filterClicked', () => {
    const inputFilters = document.querySelectorAll('[name=erp_filter]:checked')
    const activeFilters = Array.from(inputFilters).map((filter) => filter.value)
    const titlesToToggle = root.querySelectorAll('[data-filter-title]')

    if (activeFilters.length === 0) {
      dataToToogle.forEach((element) => {
        element.classList.remove('hidden')
      })
      titlesToToggle.forEach((element) => {
        element.classList.remove('hidden')
      })
      return
    }

    dataToToogle.forEach((element) => {
      const filtersForElement = element.dataset.filters
      const filterFound = activeFilters.some((filter) => filtersForElement.includes(filter))
      const forceDisplay = filtersForElement.includes('all')
      if (filterFound || forceDisplay) {
        element.classList.remove('hidden')
      } else {
        element.classList.add('hidden')
      }
    })

    hideEmptyTitles(root)
  })
}

function hideEmptyTitles(root) {
  const titlesToToggle = root.querySelectorAll('[data-filter-title]')
  titlesToToggle.forEach((titleElement) => {
    const shouldBeVisible = hasVisibleChildren(titleElement.nextElementSibling)
    if (shouldBeVisible === true) {
      titleElement.classList.remove('hidden')
    } else {
      titleElement.classList.add('hidden')
    }
  })
}

function filterData(root) {
  hideEmptyTitles(root)
  listenToFilterClicked(root)
}

export default filterData
