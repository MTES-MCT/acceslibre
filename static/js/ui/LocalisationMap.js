import geo from '../geo'

function LocalisationMap(root) {
  const mapDomEl = root.querySelector('.a4a-localisation-map')
  const hiddenLat = root.querySelector('input[type=hidden][name=lat]')
  const hiddenLon = root.querySelector('input[type=hidden][name=lon]')
  const mapOptions = JSON.parse(root.querySelector('#map-options').textContent.trim())
  const map = geo.createMap(mapDomEl, { scrollWheelZoom: false, ...mapOptions })
  map.setView(
    {
      lat: hiddenLat.value,
      lon: hiddenLon.value,
    },
    18
  )
  const control = L.control.centerCross({ show: true, position: 'topright' })
  map.addControl(control)
  map.on('move', function (event) {
    const coords = event.target.getCenter()
    hiddenLat.value = coords.lat
    hiddenLon.value = coords.lng
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
}

export default LocalisationMap
