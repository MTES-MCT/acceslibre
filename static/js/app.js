function initMap(info, geoJson) {
  var map = L.map('map').setView(info.center, info.zoom);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  // see https://leafletjs.com/examples/geojson/
  function onEachFeature({ properties }, layer) {
    const content = `<p><strong>${properties.nom}</strong><br>${properties.activite__nom}<br>${properties.adresse}</p>`
    layer.bindPopup(content);
  }

  var group = L.geoJSON(geoJson, { onEachFeature }).addTo(map);
  map.fitBounds(group.getBounds());
}
