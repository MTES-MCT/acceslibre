import api from "../api";
import dom from "../dom";

function renderError(root, error) {
  root.querySelector("#loc").innerHTML = `
    <div class="text-danger">
      <i aria-hidden="false" class="icon icon-exclamation-circle"></i>
      ${error}
    </div>`;
}

function setLocationStatus(root, label, lat, lon) {
  const loc = root.querySelector("#loc");
  loc.innerText = label;
  loc.setAttribute("role", "status");
  root.querySelector("input[name=lat]").value = lat;
  root.querySelector("input[name=lon]").value = lon;
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

  async function processLocCheckbox(node, options = { initial: false }) {
    root.querySelector("#loc").innerHTML = "";
    if (!node.checked) {
      setLocationStatus(root, "", null, null);
    } else {
      dom.show(root.querySelector("#geoloader"));
      try {
        const { lat, lon, label } = await api.getUserLocation();
        setLocationStatus(root, label, lat, lon);
        dom.hide(root.querySelector("#geoloader"));
        dom;
        // if ongoing search, submit form with localization data
        if (!options.initial && root.querySelector("#search").value.trim()) {
          node.submit();
        }
      } catch (err) {
        setLocationStatus(root, "", null, null);
        dom.hide(root.querySelector("#geoloader"));
        root.querySelector("#localize").checked = false;
        renderError(root, err);
      }
    }
  }

  dom.hide(root.querySelector("#geoloader"));
  const locCheckbox = root.querySelector("#localize");
  locCheckbox.addEventListener("change", listenToLocCheckboxChange());
  setTimeout(() => {
    // Note: a timeout is required in order to reprocess the form state after navigating back
    processLocCheckbox(locCheckbox, { initial: true });
  }, 10);
}

export default SearchForm;
