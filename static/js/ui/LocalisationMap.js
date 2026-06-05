import geo from '../geo'

function LocalisationMap(root) {
  const mapDomEl = root.querySelector('.a4a-localisation-map')
  const inputLat = root.querySelector('input[name=lat]')
  const inputLon = root.querySelector('input[name=lon]')
  const mapOptions = JSON.parse(root.querySelector('#map-options').textContent.trim())
  const map = geo.createMap(mapDomEl, { scrollWheelZoom: false, zoomControl: false, ...mapOptions })
  const lat = parseFloat(inputLat.value)
  const lon = parseFloat(inputLon.value)

  map.setView({ lat, lon }, 18)

  const tenKmInDegrees = 10 / 111 // approx. 0.09° (1° ≈ 111 km)
  const southWest = L.latLng(lat - tenKmInDegrees, lon - tenKmInDegrees)
  const northEast = L.latLng(lat + tenKmInDegrees, lon + tenKmInDegrees)
  const bounds = L.latLngBounds(southWest, northEast)
  map.setMaxBounds(bounds)

  const control = L.control.centerCross({ show: true, position: 'topright' })
  map.addControl(control)
  map.on('move', function (event) {
    const coords = event.target.getCenter()
    inputLat.value = coords.lat
    inputLon.value = coords.lng
  })

  let numero = document.getElementById('id_numero')
  let voie = document.getElementById('id_voie')
  let lieu_dit = document.getElementById('id_lieu_dit')
  let code_postal = document.getElementById('id_code_postal')
  let ville = document.getElementById('id_commune')

  ;[numero, voie, lieu_dit, code_postal, ville].forEach((elem) =>
    elem.addEventListener('change', function () {
      let query = numero.value + ' ' + voie.value + ' ' + lieu_dit.value + ' ' + code_postal.value + ' ' + ville.value
      geo.updateMap(query, map)
    })
  )

  function updateMapFromCoords() {
    const newLat = parseFloat(inputLat.value)
    const newLon = parseFloat(inputLon.value)
    if (!isNaN(newLat) && !isNaN(newLon)) {
      map.setView({ lat: newLat, lon: newLon }, map.getZoom())
    }
  }

  inputLat.addEventListener('change', updateMapFromCoords)
  inputLon.addEventListener('change', updateMapFromCoords)
}

export default LocalisationMap
