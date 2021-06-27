import api from "../api";
import dom from "../dom";
import Autocomplete from "@trevoreyre/autocomplete-js";

const AROUND_ME = "Autour de moi";
const FRANCE_ENTIERE = "France entière";

async function getCommonResults(loc) {
  return [
    { id: "around_me", text: `${AROUND_ME} ${loc?.label || ""}`, icon: "street-view" },
    { id: "france_entiere", text: FRANCE_ENTIERE, icon: "france" },
  ];
}

function SearchWhere(root) {
  const input = root.querySelector("input[type=search]");
  const a11yGeolocBtn = document.querySelector(".get-geoloc-btn");
  const hiddenLatField = root.querySelector("input[name=lat]");
  const hiddenLonField = root.querySelector("input[name=lon]");

  function setLatLon(loc) {
    hiddenLatField.value = loc?.lat || "";
    hiddenLonField.value = loc?.lon || "";
  }

  function setSearchValue(label) {
    input.value = label;
  }

  const autocomplete = new Autocomplete(root, {
    debounceTime: 100,

    getResultValue: ({ text }) => text,

    onSubmit: async (result) => {
      if (!result) {
        return;
      }

      if (result.lat && result.lon) {
        setLatLon(result);
      } else if (result.text.startsWith(AROUND_ME)) {
        if (api.hasPermission("geolocation") !== "granted") {
          a11yGeolocBtn.focus();
        }
        input.form.addEventListener("submit", dom.preventDefault);
        const loc = await api.loadUserLocation();
        input.form.removeEventListener("submit", dom.preventDefault);
        if (!loc) {
          console.warn("Impossible de récupérer votre localisation ; vérifiez les autorisations de votre navigateur");
          setLatLon(null);
          setSearchValue("");
        } else {
          input.focus();
          setLatLon(loc);
          setSearchValue(`${AROUND_ME} ${loc.label}`);
        }
      } else {
        setLatLon(null);
      }
    },

    renderResult: ({ text, context, icon }, props) => {
      const active = props["aria-selected"] ? "active" : "";
      return `
        <li class="list-group-item a4a-autocomplete-result ${active}" ${props}>
          ${icon ? `<i aria-hidden="true" class="icon icon-${icon}"></i>` : ""}
          ${text}
          ${context ? `<small class="text-muted text-truncate">${context}</small>` : ""}
        </li>
      `;
    },

    search: async (input) => {
      const loc = await api.loadUserLocation({ retrieve: false });
      const commonResults = await getCommonResults(loc);
      if (input.length < 1 || input === FRANCE_ENTIERE || input.startsWith(AROUND_ME)) {
        return commonResults;
      }
      const { results } = await api.searchLocation(input, loc);
      return commonResults.concat(results);
    },
  });

  // Invalidate lat/lon on every key stroke in the search input, except when user tabs
  // out of the field or selects and entry by pressing the Enter key.
  autocomplete.input.addEventListener("keydown", (event) => {
    if (event.key != "Tab" && event.key != "Enter") {
      setLatLon(null);
    }
  });

  // Prevent global form submission when an autocomplete entry is selected by pressing Enter,
  // which usually triggers form submit when a form input has the focus.
  let submittable;

  const observer = new MutationObserver((mutations) => {
    const exp = mutations.filter(({ attributeName }) => attributeName == "aria-expanded")[0];
    setTimeout(() => {
      try {
        submittable = exp.target.getAttribute("aria-expanded") !== "true";
      } catch (e) {}
    }, 0);
  });
  observer.observe(input, { attributeOldValue: true });

  input.form.addEventListener("submit", (event) => {
    if (!submittable) {
      event.preventDefault();
    }
  });

  return autocomplete;
}

export default SearchWhere;
