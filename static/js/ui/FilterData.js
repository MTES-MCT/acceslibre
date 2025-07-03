function listenToFilterClicked(root) {
  const dataToToogle = root.querySelectorAll('[data-filters]')

  document.addEventListener('filterClicked', () => {
    const inputFilters = document.querySelectorAll('button[data-filter-name][aria-pressed="true"]')
    const activeFilters = Array.from(inputFilters)
      .map((filter) => filter.dataset.filterName)
      .filter(Boolean)

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

  titlesToToggle.forEach((accordion) => {
    const hasContent = accordion.parentNode.querySelectorAll('.fr-collapse li:not(.hidden)')

    if (hasContent.length === 0) {
      accordion.parentNode.classList.add('hidden')
    } else {
      accordion.parentNode.classList.remove('hidden')
    }
  })
}

function filterData(root) {
  hideEmptyTitles(root)
  listenToFilterClicked(root)
}

export default filterData
