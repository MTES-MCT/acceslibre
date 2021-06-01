import api from "../api";
import Autocomplete from "@trevoreyre/autocomplete-js";

async function getCommonResults() {
  const loc = await api.loadUserLocation({ retrieve: false });
  return [
    { id: "around_me", text: `Autour de moi ${loc ? loc.label : ""}`, icon: "street-view" },
    { id: "france_entiere", text: "France entière", icon: "france" },
  ];
}

function SearchWhere(root) {
  let preventSubmit = false;
  const input = root.querySelector("input[type=search]");
  const hiddenWhereField = root.querySelector("input[name=where]");
  const hiddenLatField = root.querySelector("input[name=lat]");
  const hiddenLonField = root.querySelector("input[name=lon]");
  const whereUrl = input.dataset.src;

  function setLatLon(loc) {
    hiddenLatField.value = loc?.lat;
    hiddenLonField.value = loc?.lon;
  }

  const autocomplete = new Autocomplete(root, {
    debounceTime: 100,

    getResultValue: (result) => result.text,

    onSubmit: async (result) => {
      if (!result) {
        return;
      }

      if (result.id === "around_me") {
        const loc = await api.loadUserLocation();
        if (!loc) {
          alert("Impossible de récupérer votre localisation ; vérifiez les autorisations de votre navigateur");
          setLatLon(null);
          input.value = "";
        } else {
          setLatLon(loc);
          input.value = `Autour de moi ${loc.label}`;
        }
      } else {
        setLatLon(null);
      }

      hiddenWhereField.value = result.id;
      preventSubmit = true;
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
      const commonResults = await getCommonResults();
      if (input.length < 1) {
        return commonResults;
      }
      const res = await fetch(`${whereUrl}?q=${input}`);
      const { results } = await res.json();
      return commonResults.concat(results);
    },
  });

  // Prevent global form submission when an entry is selected
  // @see https://github.com/trevoreyre/autocomplete/issues/45#issuecomment-617216849
  autocomplete.input.addEventListener("keydown", (event) => {
    const { key } = event;
    if (preventSubmit && key == "Enter") {
      event.preventDefault();
      preventSubmit = false;
    }
  });
  return autocomplete;
}

export default SearchWhere;
