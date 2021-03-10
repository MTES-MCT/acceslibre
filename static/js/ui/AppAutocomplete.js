// App Autocomplete
// FIXME: Replaced this by a common autocomplete component. As a bonus, drop jquery usage entirely.

function AppAutocomplete(root) {
  const $input = $(root).find("input[name=q]");

  $input.autocomplete({
    deferRequestBy: 100,
    minChars: 2,
    lookup: function (query, done) {
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
        .then(function ({ features }) {
          return features
            .filter(({ properties: { city } }) => {
              return (commune && city.toLowerCase() === commune.toLowerCase()) || true;
            })
            .map(function ({ properties: { label, score }, geometry: { coordinates } }) {
              return {
                value: label,
                data: {
                  type: "adr",
                  score,
                  url: `/app/${communeSlug}/?around=${coordinates[1]},${coordinates[0]}`,
                },
              };
            });
        })
        .fail((err) => {
          console.error(err);
        });

      const erpsReq = $.ajax({
        url: "/app/autocomplete/",
        dataType: "json",
        data: { q: query, commune_slug: communeSlug },
      })
        .then((result) => {
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
        .fail((err) => {
          console.error(err);
        });
      $.when(streetsReq, erpsReq)
        .done((streets, erps) => {
          done({
            suggestions: [].sort.call(streets.concat(erps), (a, b) => {
              return a.data.score - b.data.score;
            }),
          });
        })
        .fail((err) => {
          console.error(err);
        });
    },
    onSelect: (suggestion) => {
      document.location = suggestion.data.url;
    },
  });
}

export default AppAutocomplete;
