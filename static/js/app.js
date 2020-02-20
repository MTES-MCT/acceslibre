let layers = [], markers;

// see https://leafletjs.com/examples/geojson/
function onEachFeature({ properties }, layer) {
  layer.bindPopup(`
    <p><strong><a href="${properties.absolute_url}">${properties.nom}</a></strong>
      <br>
      ${properties.activite__nom}
      <br>
      ${properties.adresse}
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

  const map = L.map("map").addLayer(tiles).setMinZoom(info.zoom - 2);

  markers = L.markerClusterGroup({
    disableClusteringAtZoom: 17,
    showCoverageOnHover: false,
    iconCreateFunction
  });
  markers.addLayer(geoJsonLayer);
  map.addLayer(markers);
  map.fitBounds(markers.getBounds().pad(.1));
}

function openMarkerPopup(target) {
  if (!markers) {
    console.warn("No marker clusters were registered, cannot open marker.")
    return;
  }
  for (const layer of layers) {
    if (layer.pk === target) {
      markers.zoomToShowLayer(layer, () => {
        layer.openPopup();
      })
      break;
    }
  }
}

window.addEventListener("DOMContentLoaded", function() {
  document.querySelectorAll(".a4a-geo-link").forEach((link) => {
    link.addEventListener("click", function(event) {
      event.preventDefault();
      event.stopPropagation();
      const pk = parseInt(link.dataset.erpId, 10);
      if (pk) openMarkerPopup(pk);
    });
  });
});
