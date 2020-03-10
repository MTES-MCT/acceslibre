// The localStorage key to use to store serialized session data
const storeKey = "a4a";

// Mutable data
let layers = [],
  markers,
  map;

// Elm app
const app = Elm.Main.init({
  flags: {
    clientUrl: location.origin + location.pathname,
    rawStore: localStorage[storeKey] || ""
  }
});

// Ensure session is refreshed when it changes in another tab/window
window.addEventListener(
  "storage",
  event => {
    if (event.storageArea === localStorage && event.key === storeKey) {
      app.ports.storeChanged.send(event.newValue);
    }
  },
  false
);

// Ports
app.ports.saveStore.subscribe(rawStore => {
  localStorage[storeKey] = rawStore;
});

app.ports.initMap.subscribe(function() {

});

function createIcon(info) {
  let iconUrl = "/static/img/markers/common.png";
  let iconRetinaUrl = "/static/img/markers/common-2x.png";
  if (info) {
    iconUrl = "/static/img/markers/info.png";
    iconRetinaUrl = "/static/img/markers/info-2x.png";
  }
  const options = {
    iconUrl: iconUrl,
    iconRetinaUrl: iconRetinaUrl,
    shadowUrl: "/static/img/markers/shadow.png",
    iconSize: [34, 41],
    iconAnchor: [16, 41],
    popupAnchor: [1, -36],
    tooltipAnchor: [16, -28],
    shadowSize: [41, 41]
  };
  return L.icon(options);
}

// see https://leafletjs.com/examples/geojson/
function onEachFeature(feature, layer) {
  const properties = feature.properties;
  const content = [
    '<p><strong><a href="',
    properties.absolute_url,
    '">',
    properties.nom,
    "</a></strong>",
    (properties.activite__nom && "<br>" + properties.activite__nom) || "",
    "<br>" + properties.adresse,
    "</p>"
  ].join("");
  layer.bindPopup(content);
  layer.pk = parseInt(feature.properties.pk, 10);
  layers.push(layer);
}

function pointToLayer(feature, coords) {
  return L.marker(coords, {
    icon: createIcon(feature.properties.has_accessibilite)
  });
}

function iconCreateFunction(cluster) {
  return L.divIcon({
    html: cluster.getChildCount(),
    className: "a4a-cluster-icon",
    iconSize: null
  });
}

function initMap(info, pk, around, geoJson) {
  const tiles = L.tileLayer(
    "https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}",
    {
      attribution: [
        'Cartographie &copy; contributeurs <a href="https://www.openstreetmap.org/">OpenStreetMap</a>',
        '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
        'Imagerie © <a href="https://www.mapbox.com/">Mapbox</a>'
      ].join(", "),
      maxZoom: 18,
      id: "n1k0/ck7daao8i07o51ipn747gwtdq",
      tileSize: 512,
      zoomOffset: -1,
      accessToken:
        "pk.eyJ1IjoibjFrMCIsImEiOiJjazdkOTVncDMweHc2M2xyd2Nhd3BueTJ5In0.-Mbvg6EfocL5NqjFbzlOSw"
    }
  );
  const geoJsonLayer = L.geoJSON(geoJson, {
    onEachFeature: onEachFeature,
    pointToLayer: pointToLayer
  });

  map = L.map("map")
    .addLayer(tiles)
    .setMinZoom(info.zoom - 2);

  markers = L.markerClusterGroup({
    disableClusteringAtZoom: 17,
    showCoverageOnHover: false,
    iconCreateFunction: iconCreateFunction
  });
  markers.addLayer(geoJsonLayer);
  map.addLayer(markers);

  if (around) {
    L.marker(around, {
      icon: L.divIcon({ className: "a4a-center-icon icon icon-target" })
    }).addTo(map);
    L.circle(around, {
      fillColor: "#0f0",
      fillOpacity: 0.1,
      stroke: 0,
      radius: 400
    }).addTo(map);
    map.setView(around, 16);
  } else if (geoJson.features.length > 0) {
    map.fitBounds(markers.getBounds().pad(0.1));
  } else {
    map.setView(info.center, info.zoom);
  }

  L.control
    .locate({
      icon: "icon icon-street-view a4a-locate-icon",
      strings: { title: "Localisez moi" }
    })
    .addTo(map);

  if (pk) {
    openMarkerPopup(pk);
  }
}

function openMarkerPopup(pk) {
  if (!markers) {
    console.warn("No marker clusters were registered, cannot open marker.");
    return;
  }
  layers.forEach(function(layer) {
    if (layer.pk === pk) {
      markers.zoomToShowLayer(layer, function() {
        layer.openPopup();
      });
    }
  });
}
