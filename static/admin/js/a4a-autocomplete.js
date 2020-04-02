window.addEventListener("DOMContentLoaded", function() {
  (function($) {
    function resetAutocompleted() {
      $("#id_nom").val();
      $("#id_numero").val();
      $("#id_voie").val();
      $("#id_lieu_dit").val();
      $("#id_code_postal").val();
      $("#id_commune").val();
      $("#id_code_insee").val();
    }

    // Photon autocomplete
    const photonAutocomplete = {
      deferRequestBy: 100,
      minChars: 2,
      lookup: function(query, done) {
        const results = {};
        const req = $.ajax({
          url: "http://photon.komoot.de/api/",
          data: {
            q: query,
            lang: "fr",
            bbox:
              "-5.164307602273511,40.64730356252251,9.733153335226492,52.44261787120725"
          }
        })
          .then(function(result) {
            return result.features
              .filter(function(feature) {
                return (
                  ["place", "boundary"].indexOf(feature.properties.osm_key) ===
                  -1
                );
              })
              .map(function(feature) {
                return {
                  value: [
                    feature.properties.name,
                    feature.properties.housenumber,
                    feature.properties.street,
                    feature.properties.postcode,
                    feature.properties.city,
                    feature.properties.osm_value
                      ? `(${feature.properties.osm_value})`
                      : ""
                  ]
                    .join(" ")
                    .replace(/\s\s+/g, " "),
                  data: feature.properties
                };
              });
          })
          .fail(function(err) {
            console.error("erreur Photon autocomplete", err);
          })
          .done(function(res) {
            done({ suggestions: res });
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
      deferRequestBy: 100,
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
