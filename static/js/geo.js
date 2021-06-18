// INFO: we suppose we're always having a single map on a page
// TODO: split these into better scoped components

import api from "./api";

let currentPk,
  layers = [],
  markers,
  map,
  satelliteTiles,
  streetTiles;

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

function createIcon(highlight, iconName = "building") {
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

// see https://leafletjs.com/examples/geojson/
function onEachFeature({ geometry, properties: props }, layer) {
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

function pointToLayer({ properties: props }, coords) {
  return L.marker(coords, {
    alt: props.nom,
    title: (props.activite__nom ? props.activite__nom + ": " : "") + props.nom,
    icon: createIcon(currentPk && Number(props.pk) === currentPk, props.activite__vector_icon),
  });
}

function iconCreateFunction(cluster) {
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
    accessToken: "pk.eyJ1IjoibjFrMCIsImEiOiJjazdkOTVncDMweHc2M2xyd2Nhd3BueTJ5In0.-Mbvg6EfocL5NqjFbzlOSw",
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
    satelliteTiles = createCustomTiles("n1k0/ckh8z9k2q2gbj19mw0x32efym");
  }
  return satelliteTiles;
}

function safeBase64Encode(data) {
  return btoa(unescape(encodeURIComponent(JSON.stringify(data))));
}

function onMapContextMenu(root, { latlng, target: map }) {
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

function parseAround({ lat, lon, label }) {
  if (!lat || !lon) return;
  try {
    return { label, point: L.latLng(lat, lon) };
  } catch (_) {}
}

function AppMap(root) {
  const info = parseJsonScript(root.querySelector("#commune-data"));
  const pk = parseJsonScript(root.querySelector("#erp-pk-data"));
  const geoJson = parseJsonScript(root.querySelector("#erps-data"));
  const around = parseAround(root.dataset);
  currentPk = pk;

  map = createMap(root);
  if (info) {
    map.setMinZoom(info.zoom - 2);
  }

  const geoJsonLayer = L.geoJSON(geoJson, {
    onEachFeature: onEachFeature,
    pointToLayer: pointToLayer,
  });

  // right-click menu
  map.on("contextmenu", onMapContextMenu.bind(map, root));

  // markers
  markers = L.markerClusterGroup({
    maxClusterRadius: 30,
    showCoverageOnHover: false,
    iconCreateFunction: iconCreateFunction,
  });
  markers.addLayer(geoJsonLayer);
  map.addLayer(markers);

  if (geoJson.features.length > 0) {
    map.fitBounds(markers.getBounds().pad(0.1));
  } else if (info) {
    map.setView(info.center, info.zoom);
  }

  if (around) {
    const circle = L.circleMarker(around.point, { fillOpacity: 1, radius: 6 }).bindPopup(around.label).addTo(map);
    if (!pk) circle.openPopup();
  }

  L.control
    .locate({
      icon: "icon icon-street-view a4a-locate-icon",
      strings: { title: "Localisez moi" },
    })
    .addTo(map);

  if (pk) {
    openMarkerPopup(pk);
  }

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

export default {
  AppMap,
  createMap,
  openMarkerPopup,
  recalculateMapSize,
  zoomTo,
};
