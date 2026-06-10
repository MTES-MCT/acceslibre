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
      announceResults(root, activeFilters)
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
    announceResults(root, activeFilters)
  })
}

function announceResults(root, activeFilters) {
  const status = document.getElementById('filter-status')

  if (!status) return

  if (activeFilters.length === 0) {
    status.textContent = gettext('Filtres réinitialisés. Toutes les informations d’accessibilité sont affichées.')
    return
  }

  const visibleCount = root.querySelectorAll('[data-filters]:not(.hidden)').length

  status.textContent =
    visibleCount === 0
      ? gettext('Aucune information d’accessibilité ne correspond aux filtres sélectionnés.')
      : `${visibleCount} ${ngettext(
          'information d’accessibilité affichée',
          'informations d’accessibilité affichées',
          visibleCount
        )}`
}

function hideEmptyTitles(root) {
  const titlesToToggle = root.querySelectorAll('[data-filter-title]')

  titlesToToggle.forEach((section) => {
    const hasContent = section.parentNode.querySelectorAll('li:not(.hidden)')

    if (hasContent.length === 0) {
      section.parentNode.classList.add('hidden')
    } else {
      section.parentNode.classList.remove('hidden')
    }
  })
}

function filterData(root) {
  hideEmptyTitles(root)
  listenToFilterClicked(root)
}

export default filterData
