let layers = [], markers, map;

// see https://leafletjs.com/examples/geojson/
function onEachFeature({ properties }, layer) {
  layer.bindPopup(`
    <p><strong><a href="${properties.absolute_url}">${properties.nom}</a></strong>
      ${properties.activite__nom && ("<br>" + properties.activite__nom) || ""}
      <br>${properties.adresse}
    </p>
  `);
  layer.pk = parseInt(properties.pk, 10);
  layers.push(layer);
}

function iconCreateFunction(cluster) {
  return L.divIcon({
    html: cluster.getChildCount(),
    className: "a4a-cluster-icon",
    iconSize: null
  });
}

function initMap(info, geoJson) {
  const tiles = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  });

  const geoJsonLayer = L.geoJSON(geoJson, { onEachFeature });

  map = L.map("map").addLayer(tiles).setMinZoom(info.zoom - 2);

  markers = L.markerClusterGroup({
    disableClusteringAtZoom: 17,
    showCoverageOnHover: false,
    iconCreateFunction
  });
  markers.addLayer(geoJsonLayer);
  map.addLayer(markers);
  map.fitBounds(markers.getBounds().pad(.1));

  L.control.locate({
    icon: "icon icon-street-view a4a-locate-icon",
    strings: { title: "Localisez moi" }
  }).addTo(map);
}

function openMarkerPopup(target) {
  if (!markers) {
    console.warn("No marker clusters were registered, cannot open marker.")
    return;
  }
  for (const layer of layers) {
    if (layer.pk === target) {
      markers.zoomToShowLayer(layer, function() {
        layer.openPopup();
      })
      break;
    }
  }
}

window.addEventListener("DOMContentLoaded", function() {
  document.querySelectorAll(".a4a-geo-link").forEach(function(link) {
    link.addEventListener("click", function(event) {
      event.preventDefault();
      event.stopPropagation();
      const pk = parseInt(link.dataset.erpId, 10);
      if (pk) openMarkerPopup(pk);
    });
  });
});
