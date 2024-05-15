function hasVisibleChildren(element) {
  let visibleChildren = false
  Array.from(element.children).forEach(function (child) {
    if (child.offsetWidth > 0) {
      visibleChildren = true
    }
  })
  return visibleChildren
}

function filterData(root) {
  const dataToToogle = root.querySelectorAll('[data-filters]')
  document.addEventListener('filterClicked', () => {
    const inputFilters = document.querySelectorAll('[name=erp_filter]:checked')
    const activeFilters = Array.from(inputFilters).map((filter) => filter.value)
    const titlesToToogle = root.querySelectorAll('[data-filter-title]')

    if (activeFilters.length === 0) {
      dataToToogle.forEach((element) => {
        element.classList.remove('hidden')
      })
      titlesToToogle.forEach((element) => {
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

    titlesToToogle.forEach((titleElement) => {
      const shouldBeVisible = hasVisibleChildren(titleElement.nextElementSibling)
      if (shouldBeVisible === true) {
        titleElement.classList.remove('hidden')
      } else {
        titleElement.classList.add('hidden')
      }
    })
  })
}

export default filterData
