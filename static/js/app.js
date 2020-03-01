let layers = [],
  markers,
  map;

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

function iconCreateFunction(cluster) {
  return L.divIcon({
    html: cluster.getChildCount(),
    className: "a4a-cluster-icon",
    iconSize: null
  });
}

function initMap(info, geoJson) {
  const tiles = L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }
  );

  const geoJsonLayer = L.geoJSON(geoJson, { onEachFeature: onEachFeature });

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

  if (geoJson.features.length > 0) {
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
}

function openMarkerPopup(target) {
  if (!markers) {
    console.warn("No marker clusters were registered, cannot open marker.");
    return;
  }
  layers.forEach(function(layer) {
    if (layer.pk === target) {
      markers.zoomToShowLayer(layer, function() {
        layer.openPopup();
      });
    }
  });
}

window.addEventListener("DOMContentLoaded", function() {
  [].forEach.call(document.querySelectorAll(".a4a-geo-link"), function(link) {
    link.addEventListener("click", function(event) {
      event.preventDefault();
      event.stopPropagation();
      const pk = parseInt(link.dataset.erpId, 10);
      if (pk) openMarkerPopup(pk);
    });
  });

  $("#q").autocomplete({
    dataType: "json",
    deferRequestBy: 350,
    minChars: 2,
    paramName: "q",
    preserveInput: true,
    serviceUrl: "https://api-adresse.data.gouv.fr/search",
    params: {
      type: "street",
      lat: $("#q").data("lat"),
      lon: $("#q").data("lon")
    },
    onSearchStart: function(params) {
      // ensure city is always passed to query
      params.q += ", " + $("#q").data("commune");
      return params;
    },
    onSelect: function(suggestion) {
      map.setView([suggestion.data[1], suggestion.data[0]]).setZoom(17);
    },
    transformResult: function(response) {
      return {
        suggestions: response.features
          .filter(function(feature) {
            return (
              feature.properties.city.toLowerCase() ===
              $("#q")
                .data("commune")
                .toLowerCase()
            );
          })
          .map(function(feature) {
            return {
              value: feature.properties.label,
              data: feature.geometry.coordinates
            };
          })
      };
    }
  });
});
