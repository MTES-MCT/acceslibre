import api from "../api";
import dom from "../dom";

function SearchForm(root) {
  const { geolocation } = navigator;

  function renderError(error) {
    root.querySelector("#loc").innerHTML = `
      <div class="text-danger">
        <i aria-hidden="false" class="icon icon-exclamation-circle"></i>
        ${error}
      </div>`;
  }

  if (!geolocation) {
    renderError("La géolocalisation n'est pas disponible sur votre navigateur.");
    return;
  }

  function setLocationStatus(label, lat, lon) {
    const loc = root.querySelector("#loc");
    loc.innerText = label;
    loc.setAttribute("role", "status");
    root.querySelector("input[name=lat]").value = lat;
    root.querySelector("input[name=lon]").value = lon;
  }

  function listenToLocCheckboxChange() {
    return ({ target }) => processLocCheckbox(target, { initial: false });
  }

  async function processLocCheckbox(node, options = { initial: false }) {
    root.querySelector("#loc").innerHTML = "";
    if (!node.checked) {
      setLocationStatus("", null, null);
    } else {
      dom.show(root.querySelector("#geoloader"));
      try {
        const { lat, lon, label } = await api.getUserLocation();
        setLocationStatus(label, lat, lon);
        dom.hide(root.querySelector("#geoloader"));
        // if ongoing search, submit form with localization data
        const where = root.querySelector("[name=where]").value.trim();
        const what = root.querySelector("[name=what]").value.trim();
        if (!options.initial && (where || what)) {
          root.submit();
        }
      } catch (err) {
        setLocationStatus("", null, null);
        dom.hide(root.querySelector("#geoloader"));
        root.querySelector("#localize").checked = false;
        renderError(err);
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
