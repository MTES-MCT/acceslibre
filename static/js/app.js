window.a4a = (function () {
  let currentPk,
    layers = [],
    markers,
    map;

  function createIcon(highlight, features) {
    const iconName = features.activite__icon || "amenity_public_building";
    const iconPathPrefix = "/static/img/activites/png/" + iconName;
    const size = highlight ? 32 : 24;
    const iconUrl = iconPathPrefix + ".n." + size + ".png";
    const iconRetinaUrl = iconPathPrefix + ".n." + size + ".png";
    const options = {
      iconUrl: iconUrl,
      iconRetinaUrl: iconRetinaUrl,
      shadowUrl: "/static/img/markers/shadow.png",
      iconSize: [size, size],
      iconAnchor: [size / 2, size],
      popupAnchor: [0, -size],
      tooltipAnchor: [size / 2, -28],
      shadowSize: [size, size],
      className: highlight && " highlighted" || "",
    };
    return L.icon(options);
  }

  // see https://leafletjs.com/examples/geojson/
  function onEachFeature(feature, layer) {
    const properties = feature.properties;
    const content = [
      '<div class="a4a-map-popup-content"><strong><a class="text-primary" href="',
      properties.absolute_url,
      '">',
      properties.nom,
      "</a></strong>",
      (properties.activite__nom && "<br>" + properties.activite__nom) || "",
      "<br>" + properties.adresse,
      "</div>",
    ].join("");
    layer.bindPopup(content);
    layer.pk = parseInt(feature.properties.pk, 10);
    layers.push(layer);
  }

  function pointToLayer(feature, coords) {
    const props = feature.properties;
    return L.marker(coords, {
      alt: props.nom,
      title: (props.activite__nom ? props.activite__nom + ": " : "") + props.nom,
      icon: createIcon(
        currentPk && Number(props.pk) === currentPk,
        props
      ),
    });
  }

  function iconCreateFunction(cluster) {
    return L.divIcon({
      html: cluster.getChildCount(),
      className: "a4a-cluster-icon",
      iconSize: null,
    });
  }

  function createTiles() {
    return L.tileLayer(
      "https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}",
      {
        attribution: [
          'Cartographie &copy; contributeurs <a href="https://www.openstreetmap.org/">OpenStreetMap</a>',
          '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
          'Imagerie © <a href="https://www.mapbox.com/">Mapbox</a>',
        ].join(", "),
        maxZoom: 18,
        id: "n1k0/ck7daao8i07o51ipn747gwtdq",
        tileSize: 512,
        zoomOffset: -1,
        accessToken:
          "pk.eyJ1IjoibjFrMCIsImEiOiJjazdkOTVncDMweHc2M2xyd2Nhd3BueTJ5In0.-Mbvg6EfocL5NqjFbzlOSw",
      }
    );
  }

  function initHomeMap() {
    const tiles = createTiles();
    return L.map("home-map")
      .addLayer(tiles)
      .setZoom(6)
      .setMinZoom(6)
      .setView([46.227638, 2.213749], 6);
  }

  function initAppMap(info, pk, around, geoJson) {
    currentPk = pk;
    const tiles = createTiles();
    const geoJsonLayer = L.geoJSON(geoJson, {
      onEachFeature: onEachFeature,
      pointToLayer: pointToLayer,
    });

    map = L.map("app-map")
      .addLayer(tiles)
      .setMinZoom(info.zoom - 2);

    markers = L.markerClusterGroup({
      maxClusterRadius: 20,
      showCoverageOnHover: false,
      iconCreateFunction: iconCreateFunction,
    });
    markers.addLayer(geoJsonLayer);
    map.addLayer(markers);

    if (around) {
      L.marker(around, {
        icon: L.divIcon({ className: "a4a-center-icon icon icon-target" }),
      }).addTo(map);
      L.circle(around, {
        fillColor: "#0f0",
        fillOpacity: 0.1,
        stroke: 0,
        radius: 400,
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
        strings: { title: "Localisez moi" },
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
    layers.forEach(function (layer) {
      if (layer.pk === pk) {
        markers.zoomToShowLayer(layer, function () {
          layer.openPopup();
        });
      }
    });
  }

  window.addEventListener("DOMContentLoaded", function () {
    if (window.hasOwnProperty("$")) {
      [].forEach.call(document.querySelectorAll(".a4a-geo-link"), function (
        link
      ) {
        link.addEventListener("click", function (event) {
          event.preventDefault();
          event.stopPropagation();
          const pk = parseInt(link.dataset.erpId, 10);
          if (pk) openMarkerPopup(pk);
        });
      });

      $("#q").autocomplete({
        deferRequestBy: 100,
        minChars: 2,
        lookup: function (query, done) {
          const $input = $("#q");
          const commune = $input.data("commune");
          const communeSlug = $input.data("commune-slug");
          const lat = $input.data("lat");
          const lon = $input.data("lon");
          const results = {};
          const streetsReq = $.ajax({
            url: "https://api-adresse.data.gouv.fr/search",
            data: {
              q: query + (commune ? ", " + commune : ""),
              type: "street",
              lat: lat,
              lon: lon,
            },
          })
            .then(function (result) {
              return result.features
                .filter(function (feature) {
                  return (
                    (commune &&
                      feature.properties.city.toLowerCase() ===
                        commune.toLowerCase()) ||
                    true
                  );
                })
                .map(function (feature) {
                  return {
                    value: feature.properties.label,
                    data: {
                      type: "adr",
                      score: feature.properties.score,
                      url:
                        "/app/" +
                        communeSlug +
                        "/?around=" +
                        feature.geometry.coordinates[1] +
                        "," +
                        feature.geometry.coordinates[0],
                    },
                  };
                });
            })
            .fail(function (err) {
              console.error(err);
            });
          const erpsReq = $.ajax({
            url: "/app/autocomplete/",
            dataType: "json",
            data: { q: query, commune_slug: communeSlug },
          })
            .then(function (result) {
              return result.suggestions.map(function (sugg) {
                return {
                  value: sugg.value,
                  data: {
                    type: "erp",
                    score: sugg.data.score,
                    url: sugg.data.url,
                  },
                };
              });
            })
            .fail(function (err) {
              console.error(err);
            });
          $.when(streetsReq, erpsReq)
            .done(function (streets, erps) {
              const results = [].sort.call(streets.concat(erps), function (
                a,
                b
              ) {
                return b.data.score - a.data.score;
              });
              done({ suggestions: results });
            })
            .fail(function (err) {
              console.error(err);
            });
        },
        onSelect: function (suggestion) {
          document.location = suggestion.data.url;
        },
      });
    }
  });

  return {
    initAppMap: initAppMap,
  };
})();
