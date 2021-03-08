import dom from "../dom";
import geo from "../geo";

function SearchForm(node) {
  if (!node) {
    console.log("missing element");
    return;
  }

  function renderError(error) {
    dom.findOne("#loc").innerHTML = `
      <div class="text-danger">
        <i aria-hidden="false" class="icon icon-exclamation-circle"></i>
        ${error}
      </div>`;
  }

  const { geolocation } = navigator;
  if (!geolocation) {
    renderError("La géolocalisation n'est pas disponible sur votre navigateur.");
    return;
  }

  function listenToLocCheckboxChange() {
    return function ({ target }) {
      processLocCheckbox(target, { initial: false });
    };
  }

  function processLocCheckbox(node, options = { initial: false }) {
    if (!node.checked) {
      dom.findOne("#loc").innerText = "";
      dom.findOne("input[name=lat]").value = null;
      dom.findOne("input[name=lon]").value = null;
    } else {
      $("#geoloader").show();
      dom.findOne("#loc").innerHTML = "";
      geo
        .getUserLocation()
        .then(({ lat, lon, label }) => {
          const loc = dom.findOne("#loc");
          loc.innerText = label;
          loc.setAttribute("role", "status");
          dom.findOne("input[name=lat]").value = lat;
          dom.findOne("input[name=lon]").value = lon;
          $("#geoloader").hide(); // XXX: drop jquery
          // if ongoing search, submit form with localization data
          if (!options.initial && $("#search").val().trim()) {
            // XXX: drop jquery
            $("#search-form").trigger("submit"); // XXX: drop jquery
          }
        })
        .catch((err) => {
          $("#geoloader").hide(); // XXX: drop jquery
          dom.findOne("#localize").checked = false;
          renderError(err);
        });
    }
  }

  $("#geoloader").hide();
  const locCheckbox = dom.findOne("#localize");
  locCheckbox.addEventListener("change", listenToLocCheckboxChange());
  setTimeout(() => {
    // Note: a timeout is required in order to reprocess the form state after navigating back
    processLocCheckbox(locCheckbox, { initial: true });
  }, 10);
}

export default {
  SearchForm,
};
