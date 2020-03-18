// The localStorage key to use to store serialized session data
const storeKey = "a4a";

// Mutable data
let markers, map;

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

app.ports.communeMap.subscribe(function(commune) {
  createMap()
    .setMinZoom(commune.zoom - 2)
    .setView(commune.center, commune.zoom);
});

app.ports.franceMap.subscribe(function() {
  createMap()
    .setMinZoom(6)
    .setView([46.227638, 2.213749], 6);
});

app.ports.locateMap.subscribe(function(point) {
  createMap().setView(point, 18);
});

app.ports.addMapMarkers.subscribe(function(erps) {
  // Cluster
  if (markers) {
    markers.clearLayers();
    markers.remove();
  }

  markers = L.markerClusterGroup({
    disableClusteringAtZoom: 17,
    maxClusterRadius: 40,
    showCoverageOnHover: false,
    iconCreateFunction: iconCreateFunction
  });

  erps.forEach(function(erp) {
    const marker = createErpMarker(erp);
    markers.addLayer(marker);
  });

  map.addLayer(markers);
  map.fitBounds(markers.getBounds().pad(0.1));
});

app.ports.openMapErpMarker.subscribe(function(erpUrl) {
  openMarkerPopup(erpUrl);
});

function createErpMarker(erp) {
  const content = [
    '<p><strong><a href="',
    erp.url,
    '">',
    erp.nom,
    "</a></strong>",
    (erp.activite && "<br>" + erp.activite) || "",
    "<br>" + erp.adresse,
    "</p>"
  ].join("");

  const marker = L.marker(erp.geom, {
    icon: createIcon(erp.hasAccessibilite)
  }).bindPopup(content);

  marker.url = erp.url;

  return marker;
}

function createMap() {
  if (!map) {
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

    map = L.map("map").addLayer(tiles);

    // TODO geolocate me: would be nice to zoom out to a larger area, ideally bounded
    // to current points so we could see both user localization and the points
    L.control
      .locate({
        icon: "icon icon-street-view a4a-locate-icon",
        strings: { title: "Localisez moi" }
      })
      .addTo(map);
  }
  return map;
}

function createIcon(hasAccessibilite) {
  let iconUrl = "/static/img/markers/common.png";
  let iconRetinaUrl = "/static/img/markers/common-2x.png";
  if (hasAccessibilite) {
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

function iconCreateFunction(cluster) {
  return L.divIcon({
    html: cluster.getChildCount(),
    className: "a4a-cluster-icon",
    iconSize: null
  });
}

function openMarkerPopup(url) {
  if (!markers) {
    console.warn("No marker clusters were registered, cannot open marker.");
    return;
  }
  markers.getLayers().forEach(function(layer) {
    if (layer.url === url) {
      try {
        markers.zoomToShowLayer(layer, function() {
          layer.openPopup();
        });
      } catch (err) {
        layer.openPopup();
      }
    }
  });
}

// XXX: remove me once migrated
function OBSOLETE_initMap(info, pk, around, geoJson) {
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
}
