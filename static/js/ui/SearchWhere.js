import api from "../api";
import dom from "../dom";
import Autocomplete from "@trevoreyre/autocomplete-js";

async function getCommonResults(loc) {
  return [
    { id: "around_me", text: `Autour de moi ${loc?.label || ""}`, icon: "street-view" },
    { id: "france_entiere", text: "France entière", icon: "france" },
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

    getResultValue: (result) => result.text,

    onSubmit: async (result) => {
      if (!result) {
        return;
      }

      if (result.lat && result.lon) {
        setLatLon(result);
      } else if (result.id === "around_me") {
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
          setSearchValue(`Autour de moi ${loc.label}`);
        }
      } else {
        setLatLon(null);
      }

      input.select();
    },

    renderResult: ({ text, icon }, props) => {
      const active = props["aria-selected"] ? "active" : "";
      return `
        <li class="list-group-item a4a-autocomplete-result ${active}" ${props}>
          ${icon ? `<i aria-hidden="true" class="icon icon-${icon}"></i>` : ""}
          ${text}
        </li>
      `;
    },

    search: async (input) => {
      const loc = await api.loadUserLocation({ retrieve: false });
      const commonResults = await getCommonResults(loc);
      if (input.length < 1) {
        return commonResults;
      }
      const { results } = await api.searchLocation(input, loc);
      return commonResults.concat(results);
    },
  });

  autocomplete.input.addEventListener("keydown", (event) => {
    // Prevent global form submission when an entry is selected
    // @see https://github.com/trevoreyre/autocomplete/issues/45#issuecomment-617216849
    if (event.key == "Enter") {
      event.preventDefault();
    } else if (event.key != "Tab") {
      setLatLon(null);
    }
  });

  return autocomplete;
}

export default SearchWhere;
