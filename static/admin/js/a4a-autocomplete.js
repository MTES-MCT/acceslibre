window.addEventListener("DOMContentLoaded", function() {
  (function($) {
    function resetAutocompleted() {
      $("#id_nom").val("");
      $("#id_numero").val("");
      $("#id_voie").val("");
      $("#id_lieu_dit").val("");
      $("#id_code_postal").val("");
      $("#id_commune").val("");
      $("#id_code_insee").val("");
      $("#id_ban_autocomplete").val("");
      $("#id_photon_autocomplete").val("");
    }

    function buildPhotonQueryString(q) {
      return (
        "https://photon.komoot.de/api/?" +
        [
          "lang=fr",
          "limit=100",
          "bbox=-5.22,41.33,9.55,51.2",
          "osm_tag=!admin_level",
          "osm_tag=!aerialway",
          "osm_tag=!aeroway",
          "osm_tag=!boundary",
          "osm_tag=!bridge",
          "osm_tag=!highway",
          "osm_tag=!historic",
          "osm_tag=!man_made",
          "osm_tag=!natural",
          "osm_tag=!place",
          "osm_tag=!railway",
          "osm_tag=!tunnel",
          "osm_tag=!waterway",
          "osm_tag=!wikipedia",
          "q=" + encodeURIComponent(q)
        ].join("&")
      );
    }

    // Photon autocomplete
    const photonAutocomplete = {
      deferRequestBy: 100,
      minChars: 2,
      lookup: function(query, done) {
        const req = $.ajax(buildPhotonQueryString(query))
          .then(function(result) {
            return result.features
              .filter(function(feature) {
                const p = feature.properties;
                return p.country === "France";
              })
              .map(function(feature) {
                return {
                  value: [
                    feature.properties.name,
                    feature.properties.housenumber,
                    feature.properties.street,
                    feature.properties.postcode,
                    feature.properties.city,
                    feature.properties.osm_key && feature.properties.osm_value
                      ? `(${feature.properties.osm_key}:${feature.properties.osm_value})`
                      : ""
                  ]
                    .join(" ")
                    .replace(/\s\s+/g, " "),
                  data: feature.properties
                };
              });
          })
          .fail(function(err) {
            console.error(
              "erreur Photon autocomplete: ",
              err.responseJSON.message
            );
          })
          .done(function(res) {
            // console.log(
            //   [
            //     ...new Set(
            //       res.map(x => `${x.data.osm_key}:${x.data.osm_value}`)
            //     )
            //   ]
            //     .sort()
            //     .join("\n")
            // );
            done({ suggestions: res.slice(0, 12) });
          });
      },
      onSelect: function(suggestion) {
        resetAutocompleted();
        $("#id_nom").val(suggestion.data.name);
        $("#id_numero").val(suggestion.data.housenumber);
        $("#id_voie").val(suggestion.data.street);
        $("#id_lieu_dit").val(suggestion.data.locality);
        $("#id_code_postal").val(suggestion.data.postcode);
        $("#id_commune").val(suggestion.data.city);
      }
    };

    // BAN autocomplete
    const banAutocomplete = {
      deferRequestBy: 30,
      minChars: 2,
      lookup: function(query, done) {
        const results = {};
        const req = $.ajax({
          url: "https://api-adresse.data.gouv.fr/search",
          data: { q: query }
        })
          .then(function(result) {
            return result.features.map(function(feature) {
              return {
                value: feature.properties.label,
                data: feature.properties
              };
            });
          })
          .fail(function(err) {
            console.error("erreur BAN autocomplete", err);
          })
          .done(function(res) {
            done({ suggestions: res });
          });
      },
      onSelect: function(suggestion) {
        let numero, voie, lieu_dit;
        resetAutocompleted();
        switch (suggestion.data.type) {
          case "locality":
            lieu_dit = suggestion.data.name;
            break;
          case "street":
            voie = suggestion.data.name;
            break;
          case "housenumber":
            numero = suggestion.data.housenumber;
            voie = suggestion.data.street;
            break;
          default:
            alert("Adresse incompatible.");
            return;
        }
        $("#id_numero").val(numero);
        $("#id_voie").val(voie);
        $("#id_lieu_dit").val(lieu_dit);
        $("#id_code_postal").val(suggestion.data.postcode);
        $("#id_commune").val(suggestion.data.city);
        $("#id_code_insee").val(suggestion.data.citycode);
      }
    };

    // Registration
    $("#id_ban_autocomplete").autocomplete(banAutocomplete);
    $("#id_photon_autocomplete").autocomplete(photonAutocomplete);
  })(django.jQuery);
});
