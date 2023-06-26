// INFO: we suppose we're always having a single map on a page
// TODO: split these into better scoped components

import api from "./api";
import mapUtils from "./mapUtils";
import dom from "./dom";
import ui from "./ui";

var L = window.L; // Let's make EsLint happy :)

let currentErpIdentifier,
  layers = [],
  markers,
  map,
  satelliteTiles,
  streetTiles,
  mapMovedDueToPopup,
  shouldTryToBroadenSearchToGetOneResult,
  geoJsonLayer;

mapMovedDueToPopup = false;
shouldTryToBroadenSearchToGetOneResult = false;


function recalculateMapSize() {
  if (!map) {
    return;
  }
  // store current identifier before it gets destroyed for unclear reasons
  const _erpIdentifier = currentErpIdentifier;
  map.invalidateSize(false);
  // ensure repositioning any opened popup
  // see https://stackoverflow.com/a/38172374
  const currentPopup = map._popup;
  if (currentPopup) {
    currentPopup.update();
  } else if (_erpIdentifier) {
    openMarkerPopup(_erpIdentifier);
  }
}

function _createIcon(highlight, iconName) {
  const size = highlight ? 48 : 32;
  const options = {
    iconUrl: `/static/img/mapicons.svg#${iconName}`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
    tooltipAnchor: [size / 2, -28],
    className: `shadow-sm act-icon act-icon-rounded act-icon-${size}${
      (highlight && " act-icon-invert") || ""
    }`,
  };
  return L.icon(options);
}

function _drawPopUpMarker({ geometry, properties: props, id }, layer) {
  let zoomLink = "";
  layer.bindPopup(`
    <div class="a4a-map-popup-content">
      <strong>
        <a class="text-primary" href="${props.absolute_url || props.web_url}">${
    props.nom
  }</a>
      </strong>
      ${(props.activite__nom && "<br>" + props.activite__nom) || ""}
      <br>${props.adresse}
    </div>`);
  layer.identifier = props.uuid;
  layers.push(layer);
}

function _createPointIcon({ properties: props }, coords) {
  let activity_icon = props.activite__vector_icon;
  if (!activity_icon && props.activite) {
    activity_icon = props.activite.vector_icon;
  } else {
    activity_icon = "building";
  }

  return L.marker(coords, {
    alt: props.nom,
    title: (props.activite__nom ? props.activite__nom + ": " : "") + props.nom,
    icon: _createIcon(
      currentErpIdentifier && Number(props.uuid) === currentErpIdentifier,
      activity_icon
    ),
  });
}

function _createClusterIcon(cluster) {
  return L.divIcon({
    html: cluster.getChildCount(),
    className: "a4a-cluster-icon",
    iconSize: null,
  });
}

function createStreetTiles() {
  return L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: `&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> et contributeurs`,
  });
}

function createCustomTiles(styleId) {
  return L.tileLayer(
    "https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}",
    {
      id: styleId,
      attribution: `
        &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>
        <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>
        Imagerie © <a href="https://www.mapbox.com/">Mapbox</a>`,
      maxZoom: 18,
      tileSize: 512,
      zoomOffset: -1,
      accessToken:
        "pk.eyJ1IjoiYWNjZXNsaWJyZSIsImEiOiJjbGVyN2p0cW8wNzBoM3duMThhaGY4cTRtIn0.jEdq_xNlv-oBu_q_UAmkxw",
    }
  );
}

function getStreetTiles() {
  if (!streetTiles) {
    streetTiles = createStreetTiles();
  }
  return streetTiles;
}

function getSatelliteTiles() {
  if (!satelliteTiles) {
    satelliteTiles = createCustomTiles("acceslibre/cliiv23h1005i01qv6365088q");
  }
  return satelliteTiles;
}

function safeBase64Encode(data) {
  return btoa(unescape(encodeURIComponent(JSON.stringify(data))));
}

function _displayCustomMenu(root, { latlng, target: map }) {
  // prevent imprecise locations by requiring a minimum zoom level
  if (map.getZoom() < 16) {
    return;
  }

  const popup = L.popup()
    .setLatLng(latlng)
    .setContent(
      '<a href="#" class="a4a-map-add">Ajouter un établissement ici</a>'
    )
    .openOn(map);

  root
    .querySelector(".a4a-map-add")
    .addEventListener("click", async (event) => {
      event.preventDefault();
      const { lat, lng: lon } = latlng;
      const { features } = await api.reverseGeocode({ lat, lon });
      const results = features.filter(
        ({ properties }) => properties.type == "housenumber"
      );
      if (results.length == 0) {
        event.target.outerHTML =
          "Aucune adresse ne correspond à cet emplacement.";
        return;
      }
      const adresses = results.map(({ properties, geometry }) => {
        return {
          label: properties.label,
          data: safeBase64Encode({
            source: "public",
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
        };
      }, []);
      event.target.outerHTML = `
      <p><b>Choisissez une adresse :</b></p>
      <ul class="a4a-map-reverse-results">
        ${adresses.map(({ data, label }) => {
          return `<li><a href="/contrib/admin-infos/?data=${data}">${label}</a></li>`;
        })}
      </ul>`;
    });
}

function createMap(domTarget, options = {}) {
  const defaults = { layers: [getStreetTiles()], scrollWheelZoom: true, ...options };
  const map = L.map(domTarget, { ...defaults, options });
  L.control.scale({ imperial: false }).addTo(map);
  L.control
    .layers({
      "Plan des rues": getStreetTiles(),
      "Vue satellite": getSatelliteTiles(),
    })
    .addTo(map);
  return map;
}

function parseJsonScript(scriptNode) {
  return JSON.parse(scriptNode.textContent);
}

function _parseAround({ lat, lon, label }) {
  if (!lat || !lon) return;
  try {
    return { label, point: L.latLng(lat, lon) };
  } catch (_) {}
}

function refreshList(data) {
  const listContainer = document.querySelector("#erp-results-list");
  if (!listContainer) {
    return;
  }
  let HTMLResult = "";
  data.features.forEach(function (point) {
    HTMLResult += mapUtils.generateHTMLForResult(point);
  });
  listContainer.innerHTML = HTMLResult;
}

function updateNumberOfResults(data) {
  const numberContainer = document.querySelector("#number-of-results");
  const translation = ngettext(" établissement", " établissements", data.count);
  numberContainer.innerHTML = data.count + translation;
}

function _getDataPromiseFromAPI(map, refreshApiUrl, apiKey) {
  const southWest = map.getBounds().getSouthWest();
  const northEast = map.getBounds().getNorthEast();
  const queryTerm = document.querySelector("#what-input").value;
  let url =
    refreshApiUrl +
    "?q=" +
    queryTerm +
    "&zone=" +
    southWest.lng +
    "," +
    southWest.lat +
    "," +
    northEast.lng +
    "," +
    northEast.lat;
  return fetch(url, {
    timeout: 10000,
    headers: {
      Accept: "application/geo+json",
      Authorization: "Api-Key " + apiKey,
    },
  });
}

function refreshData(map, refreshApiUrl, apiKey) {
    if (mapMovedDueToPopup) {
      mapMovedDueToPopup = false;
      return;
    }

    const fetchPromise = _getDataPromiseFromAPI(map, refreshApiUrl, apiKey);
    fetchPromise.then((response) => {
      response.json().then((jsonData) => {
        map.removeLayer(markers);
        markers = _createMarkersFromGeoJson(jsonData);
        map.addLayer(markers);
        refreshList(jsonData);
        updateNumberOfResults(jsonData);
        dom.mountAll(".a4a-geo-link", ui.GeoLink);

        if (shouldTryToBroadenSearchToGetOneResult){
          if (jsonData.count >= 1) {
            shouldTryToBroadenSearchToGetOneResult = false;
          } else {
            map.setView(L.latLng(map.getCenter()), map.getZoom() - 1);
          }
        }
      });
    });
}

function refreshDataOnMove(map, refreshApiUrl, apiKey) {
  const debouncedFunction = debounce(refreshData, 300);
  map.on("moveend", function() {
    debouncedFunction(map, refreshApiUrl, apiKey)
  });
}

const debounce = (callback, wait) => {
  let timeoutId = null;
  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => {
      callback.apply(null, args);
    }, wait);
  };
};

function _createMarkersFromGeoJson(geoJson) {
  geoJsonLayer = L.geoJSON(geoJson, {
    onEachFeature: _drawPopUpMarker,
    pointToLayer: _createPointIcon,
  });

  markers = L.markerClusterGroup({
    maxClusterRadius: 30,
    showCoverageOnHover: false,
    iconCreateFunction: _createClusterIcon,
  });
  markers.addLayer(geoJsonLayer);
  return markers;
}

function _addLocateButton(map) {
  L.control
    .locate({
      icon: "icon icon-street-view a4a-locate-icon",
      strings: { title: "Localisez moi" },
    })
    .addTo(map);
}

function _addMarkerAtCenterOfSearch(dataset, markers) {
  const around = _parseAround(dataset);
  if (around) {
    let aroundPoint = L.circleMarker(around.point, {
      color: "#fff",
      fillColor: "#3388ff",
      fillOpacity: 1,
      radius: 9,
    })
      .bindPopup(around.label)
      .addTo(map);
    markers.addLayer(aroundPoint);
  }
}


function broadenSearchOnClick(broaderSearchButton, map, root){
  broaderSearchButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      shouldTryToBroadenSearchToGetOneResult = true
      map.setView(L.latLng(root.dataset.lat, root.dataset.lon), map.getZoom() - 1);
  });
}

function AppMap(root) {
  const municipalityData = parseJsonScript(root.querySelector("#commune-data"));
  const erpIdentifier = root.dataset.erpIdentifier;
  const geoJson = parseJsonScript(root.querySelector("#erps-data"));
  currentErpIdentifier = erpIdentifier;

  map = createMap(root);
  map.on("contextmenu", _displayCustomMenu.bind(map, root));

  if (municipalityData) {
    map.setMinZoom(municipalityData.zoom - 2);
    if (municipalityData.contour) {
      L.polygon(municipalityData.contour, {
        color: "#075ea2",
        opacity: 0.6,
        weight: 3,
        fillOpacity: 0.05,
      }).addTo(map);
    }
  }

   const broaderSearchButton = document.querySelector("#broaderSearch");
   if (broaderSearchButton){
      broadenSearchOnClick(broaderSearchButton, map, root)
   }

  markers = _createMarkersFromGeoJson(geoJson);
  _addMarkerAtCenterOfSearch(root.dataset, markers);
  map.addLayer(markers);
  refreshList(geoJson);

  if (geoJson.features.length > 0) {
    map.fitBounds(markers.getBounds(), { padding: [70, 70] });
  } else if (municipalityData) {
    map.setView(municipalityData.center, municipalityData.zoom);
  } else {
    map.setView(L.latLng(root.dataset.lat, root.dataset.lon), 14);
    refreshData(map, root.dataset.refreshApiUrl, root.dataset.apiKey)
  }

  _addLocateButton(map);

  if (erpIdentifier) {
    openMarkerPopup(erpIdentifier);
  }

  if (root.dataset.shouldRefresh == "True") {
    refreshDataOnMove(map, root.dataset.refreshApiUrl, root.dataset.apiKey);
  }
  return map;
}

function openMarkerPopup(erpIdentifier, options = {}) {
  if (!markers) {
    console.warn("No marker clusters were registered, cannot open marker.");
    return;
  }
  currentErpIdentifier = erpIdentifier;
  layers.forEach((layer) => {
    if (layer.identifier === erpIdentifier) {
      mapMovedDueToPopup = true;
      layer.__parent._group._map = map;
      markers.zoomToShowLayer(layer, () => {
        layer.openPopup();
      });
    }
  });
}

function update_map(query, map) {
  var mapDomEl = document.querySelector(".a4a-localisation-map");
  var btnSubmit = document.querySelector('[name="contribute"]');
  btnSubmit.setAttribute("disabled", "");
  mapDomEl.style.opacity = 0.3;
  api
    .getCoordinate(query)
    .then(function (response) {
      var result = response.results[0];
      if (result !== undefined) {
        map.setView(
          {
            lat: result.lat,
            lon: result.lon,
          },
          18
        );
      }
    })
    .then(function (response) {
      mapDomEl.style.opacity = 1;
      btnSubmit.removeAttribute("disabled");
    });
}

export default {
  AppMap,
  createMap,
  openMarkerPopup,
  recalculateMapSize,
  update_map,
};
