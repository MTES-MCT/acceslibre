function initMap(info, geoJson) {
  var map = L.map("map").setView(info.center, info.zoom).setMinZoom(info.zoom - 2);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

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
  }

  var group = L.geoJSON(geoJson, { onEachFeature }).addTo(map);
  map.fitBounds(group.getBounds());
}
