window.a4a = (function () {
  let currentPk,
    layers = [],
    markers,
    map,
    satelliteTiles,
    streetTiles;

  function recalculateMapSize() {
    if (!map) {
      return;
    }
    // store current pk before it gets destroyed for unclear reasons
    _pk = currentPk;
    map.invalidateSize(false);
    // ensure repositioning any opened popup
    // see https://stackoverflow.com/a/38172374
    const currentPopup = map._popup;
    if (currentPopup) {
      currentPopup.update();
    } else if (_pk) {
      openMarkerPopup(_pk);
    }
  }

  function createIcon(highlight, features) {
    const iconName = features.activite__vector_icon || "building";
    const size = highlight ? 48 : 32;
    const options = {
      iconUrl: "/static/img/mapicons.svg#" + iconName,
      iconSize: [size, size],
      iconAnchor: [size / 2, size],
      popupAnchor: [0, -size],
      tooltipAnchor: [size / 2, -28],
      className:
        "shadow-sm act-icon act-icon-rounded act-icon-" +
        size +
        ((highlight && " invert") || ""),
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
      '<br><a href="' + properties.contrib_localisation_url + '">',
      '<i aria-hidden="true" class="icon icon-pencil a4a-icon-small-top"></i>',
      " Affiner la localisation</a>",
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
      title:
        (props.activite__nom ? props.activite__nom + ": " : "") + props.nom,
      icon: createIcon(currentPk && Number(props.pk) === currentPk, props),
    });
  }

  function iconCreateFunction(cluster) {
    return L.divIcon({
      html: cluster.getChildCount(),
      className: "a4a-cluster-icon",
      iconSize: null,
    });
  }

  function createTiles(styleId) {
    return L.tileLayer(
      "https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}",
      {
        id: styleId,
        attribution: [
          'Cartographie &copy; contributeurs <a href="https://www.openstreetmap.org/">OpenStreetMap</a>',
          '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
          'Imagerie © <a href="https://www.mapbox.com/">Mapbox</a>',
        ].join(", "),
        maxZoom: 20,
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

  function getStreetsTiles() {
    if (!streetTiles) {
      streetTiles = createTiles("n1k0/ck7daao8i07o51ipn747gwtdq");
    }
    return streetTiles;
  }

  function getSatelliteTiles() {
    if (!satelliteTiles) {
      satelliteTiles = createTiles("n1k0/ckh8z9k2q2gbj19mw0x32efym");
    }
    return satelliteTiles;
  }

  function createMap(id, options) {
    options = options || {};
    const defaults = { layers: [getStreetsTiles()] };
    const _options = Object.assign({}, defaults, options);
    const map = L.map(id, _options);
    L.control
      .layers({
        "Plan des rues": getStreetsTiles(),
        "Vue satellite": getSatelliteTiles(),
      })
      .addTo(map);
    return map;
  }

  function initAppMap(info, pk, around, geoJson) {
    currentPk = pk;
    const geoJsonLayer = L.geoJSON(geoJson, {
      onEachFeature: onEachFeature,
      pointToLayer: pointToLayer,
    });
    map = createMap("app-map").setMinZoom(info.zoom - 2);

    // markers
    markers = L.markerClusterGroup({
      maxClusterRadius: 30,
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
      [].forEach.call(
        document.querySelectorAll(".a4a-geo-link"),
        function (link) {
          link.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            const pk = parseInt(link.dataset.erpId, 10);
            if (pk) openMarkerPopup(pk);
          });
        }
      );

      // Django crispy forms asterisk a11y improvements
      $(".asteriskField").each(function (i, elem) {
        $(elem).replaceWith(
          '&nbsp;<small>(requis)</small><abbr class="asteriskField" title="(obligatoire)">*</abbr>'
        );
      });

      // Autocomplete
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
              citycode: $input.data("code-insee"),
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
              const results = [].sort.call(
                streets.concat(erps),
                function (a, b) {
                  return a.data.score - b.data.score;
                }
              );
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
    createMap: createMap,
    createTiles: createTiles,
    recalculateMapSize: recalculateMapSize,
    initAppMap: initAppMap,
  };
})();
