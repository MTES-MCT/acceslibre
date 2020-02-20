let layers = [];

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

  const map = L.map("map").addLayer(tiles).setMinZoom(info.zoom - 2);
  const markers = L.markerClusterGroup({
    disableClusteringAtZoom: 17,
    showCoverageOnHover: false,
    iconCreateFunction
  });
  const geoJsonLayer = L.geoJSON(geoJson, { onEachFeature });

  markers.addLayer(geoJsonLayer);
  map.addLayer(markers);
  map.fitBounds(markers.getBounds().pad(.1));
}

function openMarkerPopup(target) {
  for (const layer of layers) {
    if (layer.pk === target) {
      layer.openPopup();
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
