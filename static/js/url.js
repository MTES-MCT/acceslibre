function refreshSearchURL() {
  const queryParams = new URLSearchParams()
  const disabilitiesFilters = ['equipments', 'equipments_shortcuts']
  const locationFilters = ['what', 'where', 'lat', 'lon', 'code', 'postcode', 'search_type', 'municipality']

  disabilitiesFilters.forEach(function (inputName) {
    const inputs = document.querySelectorAll(`#fr-modal-disabilities-filters input[name=${inputName}]:checked`)

    inputs.forEach((input) => {
      const filterType = input.dataset?.filterType

      if (filterType) {
        queryParams.append('equipments', input.dataset.filterType)
      }
    })
  })

  locationFilters.forEach(function (inputName) {
    const inputs = document.querySelectorAll(`#search-form input[name=${inputName}]`)

    inputs.forEach((input) => (input.value ? queryParams.append(inputName, input.value) : ''))
  })

  const queryParamsString = queryParams.toString()

  history.replaceState(null, null, queryParamsString ? '?' + queryParamsString : location.pathname)
}

export default {
  refreshSearchURL,
}
