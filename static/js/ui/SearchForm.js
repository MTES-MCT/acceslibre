import api from "../api";

function renderError(root, error) {
  root.querySelector("#loc").innerHTML = `
    <div class="text-danger">
      <i aria-hidden="false" class="icon icon-exclamation-circle"></i>
      ${error}
    </div>`;
}

function SearchForm(root) {
  if (!root) {
    console.log("missing element");
    return;
  }

  const { geolocation } = navigator;
  if (!geolocation) {
    renderError(root, "La géolocalisation n'est pas disponible sur votre navigateur.");
    return;
  }

  function listenToLocCheckboxChange() {
    return ({ target }) => processLocCheckbox(target, { initial: false });
  }

  function processLocCheckbox(node, options = { initial: false }) {
    if (!node.checked) {
      root.querySelector("#loc").innerText = "";
      root.querySelector("input[name=lat]").value = null;
      root.querySelector("input[name=lon]").value = null;
    } else {
      $("#geoloader").show();
      root.querySelector("#loc").innerHTML = "";
      api
        .getUserLocation()
        .then(({ lat, lon, label }) => {
          const loc = root.querySelector("#loc");
          loc.innerText = label;
          loc.setAttribute("role", "status");
          root.querySelector("input[name=lat]").value = lat;
          root.querySelector("input[name=lon]").value = lon;
          $("#geoloader").hide(); // XXX: drop jquery
          // if ongoing search, submit form with localization data
          if (!options.initial && $("#search").val().trim()) {
            node.submit();
          }
        })
        .catch((err) => {
          $("#geoloader").hide(); // XXX: drop jquery
          root.querySelector("#localize").checked = false;
          renderError(root, err);
        });
    }
  }

  $("#geoloader").hide();
  const locCheckbox = root.querySelector("#localize");
  locCheckbox.addEventListener("change", listenToLocCheckboxChange());
  setTimeout(() => {
    // Note: a timeout is required in order to reprocess the form state after navigating back
    processLocCheckbox(locCheckbox, { initial: true });
  }, 10);
}

export default SearchForm;
