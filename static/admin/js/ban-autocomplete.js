window.addEventListener("DOMContentLoaded", function() {
  (function($) {
    $("#id_ban_autocomplete").autocomplete({
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
    });
  })(django.jQuery);
});
