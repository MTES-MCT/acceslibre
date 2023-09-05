async function fetchWithTimeout(resource, options) {
  // see https://dmitripavlutin.com/timeout-fetch-request/
  const { timeout = 8000 } = options
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)
  const response = await fetch(resource, {
    ...options,
    signal: controller.signal,
  })
  clearTimeout(id)
  return response
}

function _getCurrentPosition() {
  // TODO use maximumAge here instead of re-implementing it
  return new Promise((resolve, reject) => {
    console.log('IN _getCurrentPosition')
    console.log('geolocation' in navigator)
    console.log(navigator)
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10000 })
    } else {
      reject("La géolocalisation n'est pas disponible sur votre navigateur.")
    }
  })
}

async function hasPermission(name) {
  // Exemple name: "geolocation"
  if (!navigator?.permissions?.query) {
    return false
  }
  // Will return ['granted', 'prompt', 'denied']
  const { state } = await navigator.permissions.query({ name })
  return state
}

async function _getUserLocation() {
  _getCurrentPosition().then(
    async function (result) {
      const {
        coords: { latitude: lat, longitude: lon },
        timestamp,
      } = result
      let label
      try {
        // Reverse geolocalization is purely cosmectic, so let's not block on slow requests
        const { features } = await reverseGeocode({ lat, lon }, { type: 'street', timeout: 800 })
        label = `(${features[0].properties.label})`
      } catch (e) {
        label = '✓'
      }
      return saveUserLocation({ lat, lon, label, timestamp })
    },
    function () {
      console.log('TODO show modal')
    }
  )
}

function getLastStoredLocation() {
  let storedLocation = null
  let storedLocationIsRecent = false

  try {
    storedLocation = JSON.parse(sessionStorage['a4a-loc'] || 'null')
    storedLocationIsRecent = storedLocation.timestamp && new Date().getTime() - storedLocation.timestamp < 5 * 60000
  } catch (e) {
    return null
  }

  if (storedLocation && storedLocationIsRecent) {
    return storedLocation
  }

  return null
}

async function loadUserLocation(options = {}) {
  let storedLocation = getLastStoredLocation()

  if (storedLocation) {
    return storedLocation
  }

  try {
    return await _getUserLocation()
  } catch (e) {
    console.error(e)
  }
}

async function reverseGeocode({ lat, lon }, options = {}) {
  const { timeout = 8000 } = options
  let url = `https://api-adresse.data.gouv.fr/reverse/?lon=${lon}&lat=${lat}`
  if (options.type) {
    url += `&type=${options.type}`
  }
  try {
    const res = await fetchWithTimeout(url, { timeout })
    return await res.json()
  } catch (e) {
    console.error('reverse geocoding error', e)
  }
}

function saveUserLocation(loc) {
  sessionStorage['a4a-loc'] = JSON.stringify(loc)
  return loc
}

function getMunicipalityApi(q) {
  return `https://geo.api.gouv.fr/communes?nom=${encodeURIComponent(
    q
  )}&boost=population&fields=centre,codesPostaux,codeDepartement&limit=10`
}

function getAddressApi(q, loc) {
  let url = `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(q)}&limit=10`
  const { lat, lon } = loc || {}
  if (lat && lon) url += `&lat=${lat}&lon=${lon}`
  return url
}

function buildResultFromAddressApi({
  properties: { type, label, context, citycode, postcode, search_type, city, street, municipality },
  geometry: { coordinates },
}) {
  context = '' // Empty the context, which initially contains department, region

  return {
    id: 'loc',
    text: label,
    context: context,
    code: citycode,
    lat: coordinates[1],
    lon: coordinates[0],
    search_type: type,
    postcode: postcode,
    street_name: street,
    municipality: municipality,
  }
}

function buildResultFromMunicipalityApi({ code, nom, centre, codesPostaux, codeDepartement }) {
  return {
    id: 'loc',
    text: `${nom} (${codeDepartement})`,
    context: '',
    code: code,
    lat: centre['coordinates'][1],
    lon: centre['coordinates'][0],
    search_type: 'municipality',
    postcode: codesPostaux,
    street_name: '',
    municipality: nom,
  }
}

async function searchLocation(q, loc, kind = '') {
  if (q.trim().length <= 2) {
    return { q, results: [] }
  }

  let url = ''
  if (kind == 'municipality') {
    url = getMunicipalityApi(q)
  } else {
    url = getAddressApi(q, loc)
  }

  const response = await fetch(url)
  let results = null

  if (kind == 'municipality') {
    let json = await response.json()
    results = json.map(buildResultFromMunicipalityApi)
  } else {
    const { features } = await response.json()
    results = features.filter(({ properties: { score } }) => {
      return score > 0.4
    })
    results = results.map(buildResultFromAddressApi)
  }

  return { q, results }
}

async function getCoordinate(q) {
  let response = await searchLocation(q)
  return response
}

export default {
  hasPermission,
  loadUserLocation,
  reverseGeocode,
  searchLocation,
  getCoordinate,
  getLastStoredLocation,
}
