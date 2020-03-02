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

function initMap(info, pk, around, geoJson) {
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

$(document).ready(function() {
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
    lookup: function(query, done) {
      const $input = $("#q");
      const commune = $input.data("commune");
      const communeSlug = $input.data("commune-slug");
      const lat = $input.data("lat");
      const lon = $input.data("lon");
      const results = {};
      const streetsReq = $.ajax({
        url: "https://api-adresse.data.gouv.fr/search",
        data: { q: query + ", " + commune, lat: lat, lon: lon }
      })
        .then(function(result) {
          return result.features.map(function(feature) {
            return {
              value: feature.properties.label,
              data: {
                type: "adr",
                loc: feature.geometry.coordinates,
                score: feature.properties.importance,
                url:
                  "/app/" +
                  communeSlug +
                  "/?around=" +
                  feature.geometry.coordinates[1] +
                  "," +
                  feature.geometry.coordinates[0]
              }
            };
          });
        })
        .fail(function(err) {
          console.error(err);
        });
      const erpsReq = $.ajax({
        url: "/app/" + communeSlug + "/autocomplete/",
        dataType: "json",
        data: { q: query }
      })
        .then(function(result) {
          return result.suggestions.map(function(sugg) {
            return {
              value: sugg.value,
              data: {
                type: "erp",
                loc: sugg.data.loc,
                score: sugg.data.score,
                url: sugg.data.url
              }
            };
          });
        })
        .fail(function(err) {
          console.error(err);
        });
      $.when(streetsReq, erpsReq)
        .done(function(streets, erps) {
          const results = [].sort.call(streets.concat(erps), function(a, b) {
            return b.data.score - a.data.score;
          });
          console.log(results);
          done({ suggestions: results });
        })
        .fail(function(err) {
          console.error(err);
        });
    },
    onSelect: function(suggestion) {
      // if (suggestion.data.type === "erp") {
      document.location = suggestion.data.url;
      // } else {
      //   map
      //     .setView([suggestion.data.loc[1], suggestion.data.loc[0]])
      //     .setZoom(17);
      // }
    }
  });
});
