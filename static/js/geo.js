// INFO: we suppose we're always having a single map on a page
// TODO: split these into better scoped components

import api from "./api";
var L = window.L; // Let's make EsLint happy :)

let currentPk,
  layers = [],
  markers,
  map,
  satelliteTiles,
  streetTiles,
  geoJsonLayer;

function recalculateMapSize() {
  if (!map) {
    return;
  }
  // store current pk before it gets destroyed for unclear reasons
  const _pk = currentPk;
  map.invalidateSize(false);
  // ensure repositioning any opened popup
  // see https://stackoverflow.com/a/38172374
  const currentPopup = map._popup;
  if (currentPopup) {
    currentPopup.update();
  } else if (_pk) {
    openMarkerPopup(_pk);
  }
}

function _createIcon(highlight, iconName = "building") {
  const size = highlight ? 48 : 32;
  const options = {
    iconUrl: `/static/img/mapicons.svg#${iconName}`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
    tooltipAnchor: [size / 2, -28],
    className: `shadow-sm act-icon act-icon-rounded act-icon-${size}${(highlight && " act-icon-invert") || ""}`,
  };
  return L.icon(options);
}

// TODO move me to another file ?
// TODO fix issue with icons
function _generateHTMLForResult(result) {
    return `
    <div class="list-group-item d-flex justify-content-between align-items-center pt-2 pr-2 pb-1 pl-0">
    <div>
        <div class="d-flex w-100 justify-content-between">
            <a href="${ result.properties.web_url }">
                <h3 class="h6 font-weight-bold w-100 mb-0 pb-0">
                    <img alt="" class="act-icon act-icon-20 mb-1" src="{% static " img/mapicons.svg" %}#{{ erp.get_activite_vector_icon }}">
                   ${ result.properties.nom }
                    <span class="sr-only">
                        ${ result.properties.activite.nom }
                        {% translate "à l'adresse" %} ${ result.properties.adresse }
                    </span>
                </h3>
            </a>
        </div>
        <div aria-hidden="true">
            <small class="font-weight-bold text-muted">${ result.properties.activite.nom }</small>
            <address class="d-inline mb-0">
                <small>${ result.properties.adresse }</small>
            </address>
        </div>
    </div>
    <button class="btn btn-sm btn-outline-primary d-none d-sm-none d-md-block a4a-icon-btn a4a-geo-link ml-2"
            title="${gettext('Localiser sur la carte')}"
            data-erp-id="{{ erp.pk }}">
        ${gettext("Localiser")}
        <br>
        <i aria-hidden="true" class="icon icon-target"></i>
    </button>
</div>`;
}

function _drawPopUpMarker({ geometry, properties: props }, layer) {
  let zoomLink = "";
  layer.bindPopup(`
    <div class="a4a-map-popup-content">
      <strong>
        <a class="text-primary" href="${props.absolute_url}">${props.nom}</a>
      </strong>
      ${(props.activite__nom && "<br>" + props.activite__nom) || ""}
      <br>${props.adresse}
    </div>`);
  layer.pk = parseInt(props.pk, 10);
  layers.push(layer);
}

function _createPointIcon({ properties: props }, coords) {
  return L.marker(coords, {
    alt: props.nom,
    title: (props.activite__nom ? props.activite__nom + ": " : "") + props.nom,
    icon: _createIcon(currentPk && Number(props.pk) === currentPk, props.activite__vector_icon),
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
  return L.tileLayer("https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}", {
    id: styleId,
    attribution: `
        &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>
        <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>
        Imagerie © <a href="https://www.mapbox.com/">Mapbox</a>`,
    maxZoom: 18,
    tileSize: 512,
    zoomOffset: -1,
    accessToken: "pk.eyJ1IjoiYWNjZXNsaWJyZSIsImEiOiJjbGVyN2p0cW8wNzBoM3duMThhaGY4cTRtIn0.jEdq_xNlv-oBu_q_UAmkxw",
  });
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
    .setContent('<a href="#" class="a4a-map-add">Ajouter un établissement ici</a>')
    .openOn(map);

  root.querySelector(".a4a-map-add").addEventListener("click", async (event) => {
    event.preventDefault();
    const { lat, lng: lon } = latlng;
    const { features } = await api.reverseGeocode({ lat, lon });
    const results = features.filter(({ properties }) => properties.type == "housenumber");
    if (results.length == 0) {
      event.target.outerHTML = "Aucune adresse ne correspond à cet emplacement.";
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
  const defaults = { layers: [getStreetTiles()], scrollWheelZoom: false };
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
  listContainer.innerHTML = "";
  data.features.forEach(function(point){
    let html = _generateHTMLForResult(point);
    listContainer.innerHTML += html;
    // TODO see how many point we will handle ?
  });
}

function updateNumberOfResults(data) {
  const numberContainer = document.querySelector("#number-of-results");
  if (data.count > 1) {
    numberContainer.innerHTML = data.count + gettext(" établissements");
  } else {
    numberContainer.innerHTML = data.count + gettext(" établissement");
  }
}

// TODO clean this function
function refreshDataOnMove(map, refreshApiUrl) {
  map.on("moveend", function () {
    const southWest = map.getBounds().getSouthWest()
    const northEast = map.getBounds().getNorthEast()
    // TODO solve issue for api key

    const apiKey = "";
    let url = refreshApiUrl + "?in_bbox=" + southWest.lng + "," + southWest.lat + "," + northEast.lng + "," + northEast.lat

    const fetchPromise = fetch(url, { timeout: 10000, headers: {"Content-Type": "application/geo+json", "Authorization": apiKey} });

    fetchPromise.then((response) => {
      const jsonPromise = response.json();
      jsonPromise.then((jsonData) => {
        map.removeLayer(markers);
        markers = _createMarkersFromGeoJson(jsonData);
        map.addLayer(markers);
        refreshList(jsonData);
        updateNumberOfResults(jsonData);

      });
    });
  });
}

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

function _addMarkerAtCenterOfSearch(dataset, markers){
  const around = _parseAround(dataset);
   if (around) {
      let aroundPoint = L.circleMarker(around.point, { color: "#fff", fillColor: "#3388ff", fillOpacity: 1, radius: 9 })
        .bindPopup(around.label)
        .addTo(map);
      markers.addLayer(aroundPoint);
    }
}

function AppMap(root) {
  const municipalityData = parseJsonScript(root.querySelector("#commune-data"));
  const pk = parseJsonScript(root.querySelector("#erp-pk-data"));
  const geoJson = parseJsonScript(root.querySelector("#erps-data"));
  currentPk = pk;

  // TODO handle initial results on page load + delete result row html file
  map = createMap(root);
  map.on("contextmenu", _displayCustomMenu.bind(map, root));

  if (municipalityData) {
    map.setMinZoom(municipalityData.zoom - 2);
    if (municipalityData.contour) {
      L.polygon(municipalityData.contour, { color: "#075ea2", opacity: 0.6, weight: 3, fillOpacity: 0.05 }).addTo(map);
    }
  }

  markers = _createMarkersFromGeoJson(geoJson);
  _addMarkerAtCenterOfSearch(root.dataset, markers)
  map.addLayer(markers);

  if (geoJson.features.length > 0) {
    map.fitBounds(markers.getBounds(), { padding: [70, 70] });
  } else if (municipalityData) {
    map.setView(municipalityData.center, municipalityData.zoom);
  }

  _addLocateButton(map);

  if (pk) {
    openMarkerPopup(pk);
  }

  refreshDataOnMove(map, root.dataset.refreshApiUrl);

  return map;
}

function openMarkerPopup(pk, options = {}) {
  if (!markers) {
    console.warn("No marker clusters were registered, cannot open marker.");
    return;
  }
  layers.forEach((layer) => {
    if (layer.pk === pk) {
      markers.zoomToShowLayer(layer, () => {
        layer.openPopup();
        if (options.highlight) {
          map.setView(layer.getLatLng(), 18);
        }
      });
    }
  });
}

function zoomTo(lat, lon) {
  map.setView([lat, lon], 18);
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
  zoomTo,
};
