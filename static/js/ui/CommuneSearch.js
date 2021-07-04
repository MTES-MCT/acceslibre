function CommuneSearch(root) {
  // FIXME: replace use of select2 with something else, so we can drop jQuery
  const codeInseeSelect = $(root);
  const searchLabel = $("#id_commune_search");

  codeInseeSelect.select2({
    language: "fr",
    placeholder: "Rechercher une commune",
    theme: "bootstrap4",
    minimumInputLength: 1,
    ajax: {
      cache: true,
      delay: 100,
      url: "https://api-adresse.data.gouv.fr/search/",
      dataType: "json",
      data: function (params) {
        return {
          q: params.term || "",
          type: "municipality",
          autocomplete: 1,
          limit: 5,
        };
      },
      processResults: function (results) {
        return {
          results: results.features.map(function (result) {
            return {
              id: result.properties.citycode,
              text: result.properties.label + " (" + result.properties.postcode.substr(0, 2) + ")",
            };
          }),
        };
      },
    },
  });

  codeInseeSelect.on("select2:select", function (event) {
    try {
      const communeSearch = event.params.data.text;
      $("#id_commune_search").val(communeSearch);
    } catch (err) {
      console.warn("Impossible de récupérer le nom de la commune : " + err);
    }
  });

  // Init and check for existing selected value
  const commune_search = searchLabel.val();
  const code_insee = "{{ form.code_insee.value }}";
  if (commune_search && code_insee) {
    let option = new Option(commune_search, code_insee, false, false);
    codeInseeSelect.append(option).trigger("change");
  }
}

export default CommuneSearch;
