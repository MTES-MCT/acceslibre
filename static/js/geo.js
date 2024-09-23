// INFO: we suppose we're always having a single map on a page
// TODO: split these into better scoped components

import api from './api'
import mapUtils from './mapUtils'
import dom from './dom'
import ui from './ui'
import url from './url.js'

// Default coords used when we have no result and no selected city
const DEFAULT_LAT = 46.7
const DEFAULT_LON = 1.9

var L = window.L // Let's make EsLint happy :)

let currentErpIdentifier,
  layers = [],
  markers = null,
  map,
  satelliteTiles,
  streetTiles,
  shouldRefreshMap,
  shouldTryToBroadenSearchToGetOneResult,
  currentPage,
  geoJsonLayer

shouldRefreshMap = true
shouldTryToBroadenSearchToGetOneResult = false
currentPage = 1

function recalculateMapSize() {
  if (!map) {
    return
  }
  // store current identifier before it gets destroyed for unclear reasons
  const _erpIdentifier = currentErpIdentifier
  map.invalidateSize(false)
  // ensure repositioning any opened popup
  // see https://stackoverflow.com/a/38172374
  const currentPopup = map._popup
  if (currentPopup) {
    currentPopup.update()
  } else if (_erpIdentifier) {
    openMarkerPopup(_erpIdentifier)
  }
}

function _createIcon(highlight, iconName) {
  const size = highlight ? 48 : 32
  const options = {
    iconUrl: `/static/img/mapicons.svg#${iconName}`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
    tooltipAnchor: [size / 2, -28],
    className: `shadow-sm act-icon act-icon-rounded act-icon-${size}${(highlight && ' act-icon-invert') || ''}`,
  }
  return L.icon(options)
}

function _drawPopUpMarker({ properties: props }, layer) {
  layer.bindPopup(`
    <div class="a4a-map-popup-content">
      <strong>
        <a class="text-primary" href="${props.absolute_url || props.web_url}">${props.nom}</a>
      </strong>
      ${(props.activite__nom && '<br>' + props.activite__nom) || ''}
      <br>${props.adresse}
    </div>`)
  layer.identifier = props.uuid
  layers.push(layer)
}

function _createPointIcon({ properties: props }, coords) {
  let activity_icon = props.activite__vector_icon
  if (!activity_icon) {
    if (props.activite) {
      activity_icon = props.activite.vector_icon
    } else {
      activity_icon = 'building'
    }
  }

  return L.marker(coords, {
    alt: props.nom,
    title: (props.activite__nom ? props.activite__nom + ': ' : '') + props.nom,
    icon: _createIcon(currentErpIdentifier && Number(props.uuid) === currentErpIdentifier, activity_icon),
  })
}

function _createClusterIcon(cluster) {
  return L.divIcon({
    html: cluster.getChildCount(),
    className: 'a4a-cluster-icon',
    iconSize: null,
  })
}

function createStreetTiles() {
  return L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: `&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> et contributeurs`,
  })
}

function createCustomTiles(styleId) {
  return L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
    id: styleId,
    attribution: `
        &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>
        <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>
        Imagerie © <a href="https://www.mapbox.com/">Mapbox</a>`,
    maxZoom: 18,
    tileSize: 512,
    zoomOffset: -1,
    accessToken: 'pk.eyJ1IjoiYWNjZXNsaWJyZSIsImEiOiJjbGVyN2p0cW8wNzBoM3duMThhaGY4cTRtIn0.jEdq_xNlv-oBu_q_UAmkxw',
  })
}

function getStreetTiles() {
  if (!streetTiles) {
    streetTiles = createStreetTiles()
  }
  return streetTiles
}

function getSatelliteTiles() {
  if (!satelliteTiles) {
    satelliteTiles = createCustomTiles('acceslibre/cliiv23h1005i01qv6365088q')
  }
  return satelliteTiles
}

function safeBase64Encode(data) {
  return btoa(unescape(encodeURIComponent(JSON.stringify(data))))
}

function _displayCustomMenu(root, { latlng, target: map }) {
  // prevent imprecise locations by requiring a minimum zoom level
  if (map.getZoom() < 16) {
    return
  }

  L.popup()
    .setLatLng(latlng)
    .setContent('<a href="#" class="a4a-map-add">Ajouter un établissement ici</a>')
    .openOn(map)

  root.querySelector('.a4a-map-add').addEventListener('click', async (event) => {
    event.preventDefault()
    const { lat, lng: lon } = latlng
    const { features } = await api.reverseGeocode({ lat, lon })
    const results = features.filter(({ properties }) => properties.type == 'housenumber')
    if (results.length == 0) {
      event.target.outerHTML = 'Aucune adresse ne correspond à cet emplacement.'
      return
    }
    const adresses = results.map(({ properties, geometry }) => {
      return {
        label: properties.label,
        data: safeBase64Encode({
          source: 'public',
          source_id: `ban:${properties.id}`,
          coordonnees: [geometry.coordinates[0], geometry.coordinates[1]],
          naf: null,
          activite: null,
          nom: null,
          siret: null,
          numero: properties.housenumber,
          voie: properties.street,
          lieu_dit: properties.locality,
          code_postal: properties.postcode,
          commune: properties.city,
          code_insee: properties.citycode,
        }),
      }
    }, [])
    event.target.outerHTML = `
      <p><b>Choisissez une adresse :</b></p>
      <ul class="a4a-map-reverse-results">
        ${adresses.map(({ data, label }) => {
          return `<li><a href="/contrib/admin-infos/?data=${data}">${label}</a></li>`
        })}
      </ul>`
  })
}

function _loadMoreWhenLastElementIsDisplayed(map) {
  const container = document.querySelector('#erp-results-list')
  if (!container) {
    return
  }

  // Watch for end of scroll
  container.addEventListener('scroll', () => {
    if (container.offsetHeight + container.scrollTop >= container.scrollHeight) {
      currentPage += 1
      refreshData(map, currentPage)
    }
  })

  // Watch for last result being tabulated
  const nodes = document.querySelectorAll('.map-results')
  const lastElement = nodes[nodes.length - 1]
  if (!lastElement) {
    return
  }
  lastElement.addEventListener('focusin', function () {
    currentPage += 1
    refreshData(map, currentPage)
  })
}

function createMap(domTarget, options = {}) {
  const defaults = { layers: [getStreetTiles()], scrollWheelZoom: true, ...options }
  const map = L.map(domTarget, { ...defaults, options })
  L.control.scale({ imperial: false }).addTo(map)
  L.control
    .layers({
      'Plan des rues': getStreetTiles(),
      'Vue satellite': getSatelliteTiles(),
    })
    .addTo(map)
  return map
}

function _parseAround({ lat, lon, label }) {
  if (!lat || !lon) return
  try {
    return { label, point: L.latLng(lat, lon) }
  } catch (_) {}
}

function refreshList(data, clearHTML = true) {
  const listContainer = document.querySelector('#erp-results-list')
  if (!listContainer) {
    return
  }

  let HTMLResult = listContainer.innerHTML
  if (clearHTML) {
    HTMLResult = ''
  }
  data.features.forEach(function (point) {
    HTMLResult += mapUtils.generateHTMLForResult(point)
  })
  listContainer.innerHTML = HTMLResult
}

function updateNumberOfResults(data) {
  const numberContainer = document.querySelector('#number-of-results')
  const translation = ngettext('établissement', 'établissements', data.count)
  numberContainer.innerHTML = data.count + ' ' + translation
}

function _getDataPromiseFromAPI(map, page) {
  const southWest = map.getBounds().getSouthWest()
  const northEast = map.getBounds().getNorthEast()
  let equipments = document.querySelectorAll('input[name=equipments]:checked')
  let equipmentsQuery = ''
  equipments.forEach(function (eq) {
    equipmentsQuery += '&equipments=' + eq.value
  })
  urlParams = new URLSearchParams({
    q: document.querySelector('#what-input').value,
    zone: southWest.lng + ',' + southWest.lat + ',' + northEast.lng + ',' + northEast.lat,
    equipmentsQuery: equipmentsQuery,
    page: page,
    sortType: _getSortType(),
    where: _getWhere(),
  })
  return fetch(_getRefreshApiUrl() + '?' + urlParams.toString(), {
    timeout: 10000,
    headers: {
      Accept: 'application/geo+json',
      Authorization: 'Api-Key ' + _getApiKey(),
    },
  })
}

function _getRoot() {
  return document.querySelector('#app-map')
}

function _getRefreshApiUrl() {
  return _getRoot().dataset.refreshApiUrl
}

function _getApiKey() {
  return _getRoot().dataset.apiKey
}

function _getSortType() {
  return _getRoot().dataset.sortType
}

function _getWhere() {
  return _getRoot().dataset.where
}

function refreshData(map, page = 1) {
  if (!shouldRefreshMap) {
    shouldRefreshMap = true
    return
  }
  const fetchPromise = _getDataPromiseFromAPI(map, page)
  const clearOldResults = page == 1
  document.querySelector('#loading-spinner').classList.toggle('show-loader')
  fetchPromise.then((response) => {
    if (!response.ok) {
      document.querySelector('#loading-spinner').classList.toggle('show-loader')
      return
    }
    response.json().then((jsonData) => {
      if (clearOldResults && markers) {
        map.removeLayer(markers)
      }
      markers = _createMarkersFromGeoJson(jsonData)
      map.addLayer(markers)
      refreshList(jsonData, clearOldResults)
      updateNumberOfResults(jsonData)
      dom.mountAll('.a4a-geo-link', ui.GeoLink)
      document.querySelector('#loading-spinner').classList.toggle('show-loader')
      if (jsonData.count > 0) {
        document.querySelector('#no-results').classList.add('hidden')
      } else {
        document.querySelector('#no-results').classList.remove('hidden')
      }

      if (shouldTryToBroadenSearchToGetOneResult) {
        if (jsonData.count >= 1) {
          shouldTryToBroadenSearchToGetOneResult = false
        } else {
          map.setView(L.latLng(map.getCenter()), map.getZoom() - 1)
        }
      }
    })
  })
}

function refreshDataOnMove(map) {
  const debouncedFunction = debounce(refreshData, 300)
  map.on('moveend', function () {
    currentPage = 0
    debouncedFunction(map)
  })
}

const debounce = (callback, wait) => {
  let timeoutId = null
  return (...args) => {
    window.clearTimeout(timeoutId)
    timeoutId = window.setTimeout(() => {
      callback.apply(null, args)
    }, wait)
  }
}

function _createMarkersFromGeoJson(geoJson) {
  geoJsonLayer = L.geoJSON(geoJson, {
    onEachFeature: _drawPopUpMarker,
    pointToLayer: _createPointIcon,
  })

  markers = L.markerClusterGroup({
    maxClusterRadius: 30,
    showCoverageOnHover: false,
    iconCreateFunction: _createClusterIcon,
  })
  markers.addLayer(geoJsonLayer)
  return markers
}

function _addLocateButton(map) {
  L.control
    .locate({
      icon: 'icon icon-street-view a4a-locate-icon',
      strings: { title: 'Localisez moi' },
    })
    .addTo(map)
}

function _addMarkerAtCenterOfSearch(dataset, markers) {
  const around = _parseAround(dataset)
  if (around) {
    let aroundPoint = L.circleMarker(around.point, {
      color: '#fff',
      fillColor: '#3388ff',
      fillOpacity: 1,
      radius: 9,
    })
      .bindPopup(around.label)
      .addTo(map)
    markers.addLayer(aroundPoint)
  }
}

function broadenSearchOnClick(broaderSearchButton, map, root) {
  broaderSearchButton.addEventListener('click', (event) => {
    event.preventDefault()
    event.stopPropagation()
    shouldTryToBroadenSearchToGetOneResult = true
    map.setView(L.latLng(root.dataset.lat, root.dataset.lon), map.getZoom() - 1)
  })
}

function refreshMapOnEquipmentsChange(equipmentsInputs, map) {
  document.addEventListener('filterChanged', async function () {
    refreshData(map)
    url.refreshSearchURL()
  })
}

function _setZoomLevel(map, geoJson) {
  const root = _getRoot()
  const municipalityData = JSON.parse(root.querySelector('#commune-data').textContent)
  const departementData = JSON.parse(root.querySelector('#departement-data').textContent)
  if (municipalityData) {
    map.setMinZoom(municipalityData.zoom - 2)
    map.setView(municipalityData.center, municipalityData.zoom)
    if (municipalityData.contour) {
      const poly = L.polygon(municipalityData.contour, {
        color: '#075ea2',
        opacity: 0.6,
        weight: 3,
        fillOpacity: 0.05,
      })
      poly.addTo(map)
      map.fitBounds(poly.getBounds())
    }
  } else if (departementData) {
    const poly = L.polygon(departementData, {
      color: '#075ea2',
      opacity: 0.6,
      weight: 3,
      fillOpacity: 0.05,
    })
    poly.addTo(map)
    map.fitBounds(poly.getBounds())
  } else if (geoJson && geoJson.features.length > 0) {
    map.fitBounds(markers.getBounds(), { padding: [70, 70] })
  } else {
    map.setView(
      L.latLng(root.dataset.lat || DEFAULT_LAT, root.dataset.lon || DEFAULT_LON),
      root.dataset.defaultZoom || 14
    )
    refreshData(map)
  }
}

function AppMap(root) {
  const erpIdentifier = root.dataset.erpIdentifier
  shouldRefreshMap = true
  if (root.dataset.shouldRefreshOnMapLoad == 'False') {
    shouldRefreshMap = false
  }
  const erpData = root.querySelector('#erps-data').textContent
  const options = root.querySelector('#map-options')
  var mapOptions = {}
  if (options) {
    mapOptions = JSON.parse(options.textContent.trim())
  }
  let geoJson = null
  if (erpData) {
    geoJson = JSON.parse(erpData)
  }
  currentErpIdentifier = erpIdentifier
  map = createMap(root, mapOptions)
  map.on('contextmenu', _displayCustomMenu.bind(map, root))

  const broaderSearchButton = document.querySelector('#broaderSearch')
  if (broaderSearchButton) {
    broadenSearchOnClick(broaderSearchButton, map, root)
  }

  const equipmentsInputs = document.querySelectorAll('input[name=equipments]')
  if (equipmentsInputs) {
    refreshMapOnEquipmentsChange(equipmentsInputs, map)
  }

  if (geoJson) {
    markers = _createMarkersFromGeoJson(geoJson)
    _addMarkerAtCenterOfSearch(root.dataset, markers)
    map.addLayer(markers)
    refreshList(geoJson)
    _loadMoreWhenLastElementIsDisplayed(map)
  }

  _setZoomLevel(map, geoJson)
  _addLocateButton(map)

  if (erpIdentifier) {
    openMarkerPopup(erpIdentifier)
  }

  if (root.dataset.shouldRefresh == 'True') {
    refreshDataOnMove(map)
  }
  return map
}

function openMarkerPopup(erpIdentifier, options = {}) {
  if (!markers) {
    console.warn('No marker clusters were registered, cannot open marker.')
    return
  }
  currentErpIdentifier = erpIdentifier
  layers.forEach((layer) => {
    if (layer.identifier === erpIdentifier) {
      shouldRefreshMap = false
      layer.__parent._group._map = map
      markers.zoomToShowLayer(layer, () => {
        layer.openPopup()
      })
    }
  })
}

function updateMap(query, map) {
  var mapDomEl = document.querySelector('.a4a-localisation-map')
  var btnSubmit = document.querySelector('[name="contribute"]')
  btnSubmit.setAttribute('disabled', '')
  mapDomEl.style.opacity = 0.3
  api
    .getCoordinate(query)
    .then(function (response) {
      var result = response.results[0]
      if (result !== undefined) {
        map.setView(
          {
            lat: result.lat,
            lon: result.lon,
          },
          18
        )
      }
    })
    .then(function () {
      mapDomEl.style.opacity = 1
      btnSubmit.removeAttribute('disabled')
    })
}

export default {
  AppMap,
  createMap,
  openMarkerPopup,
  recalculateMapSize,
  updateMap,
}
