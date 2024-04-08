function refreshSearchURL() {
  let queryParams = new URLSearchParams()
  ;['equipments', 'equipments_shortcuts'].forEach(function (inputName) {
    let inputs = document.querySelectorAll(`input[name=${inputName}]:checked`)
    inputs.forEach((input) => queryParams.append(inputName, input.value))
  })
  ;['what', 'where', 'lat', 'lon', 'code', 'postcode', 'search_type', 'municipality'].forEach(function (inputName) {
    let inputs = document.querySelectorAll(`input[name=${inputName}]`)
    inputs.forEach((input) => (input.value ? queryParams.append(inputName, input.value) : ''))
  })
  queryParams = queryParams.toString()
  history.replaceState(null, null, queryParams ? '?' + queryParams : location.pathname)
}

export default {
  refreshSearchURL,
}
