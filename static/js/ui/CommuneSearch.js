function CommuneSearch(root) {
  // FIXME: replace use of select2 with something else, so we can drop jQuery
  const $root = $(root);
  const $searchLabel = $("#id_commune_search");

  $root.select2({
    language: "fr",
    placeholder: "Rechercher une commune",
    theme: "bootstrap4",
    minimumInputLength: 1,
    ajax: {
      cache: true,
      delay: 100,
      url: "https://api-adresse.data.gouv.fr/search/",
      dataType: "json",
      data: (params) => ({
        q: params.term || "",
        type: "municipality",
        autocomplete: 1,
        limit: 5,
      }),
      processResults: ({ features }) => {
        return {
          results: features.map(function ({ properties: { citycode: id, label, postcode } }) {
            return { id, text: `${label} (${postcode.substr(0, 2)})` };
          }),
        };
      },
    },
  });

  $root.on("select2:select", ({ params }) => {
    try {
      $("#id_commune_search").val(params.data.text);
    } catch (err) {
      console.warn(`Impossible de récupérer le nom de la commune: ${err}`);
    }
  });

  // Init and check for existing selected value
  const communeSearch = $searchLabel.val();
  const codeInsee = new URLSearchParams(location.search).get("code_insee") || "";
  if (communeSearch && codeInsee) {
    let option = new Option(communeSearch, codeInsee, false, false);
    $root.append(option).trigger("change");
  }
}

export default CommuneSearch;
