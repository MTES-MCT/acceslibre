let layers = [];

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
    layer.pk = parseInt(properties.pk, 10);
    layers.push(layer);
  }

  group = L.geoJSON(geoJson, { onEachFeature }).addTo(map);
  map.fitBounds(group.getBounds().pad(.3));
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
