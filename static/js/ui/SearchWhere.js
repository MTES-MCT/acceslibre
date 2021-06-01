import api from "../api";
import Autocomplete from "@trevoreyre/autocomplete-js";

let _loc;

function getCommonResults() {
  return [
    { id: "around_me", text: `Autour de moi ${_loc ? _loc.label : ""}`, icon: "street-view" },
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
  const autocomplete = new Autocomplete(root, {
    debounceTime: 100,

    getResultValue: (result) => result.text,

    onSubmit: async (result) => {
      if (!result) {
        return;
      }

      if (result.id === "around_me") {
        preventSubmit = true;
        if (!_loc) {
          _loc = await api.loadUserLocation();
        }
        hiddenLatField.value = _loc.lat;
        hiddenLonField.value = _loc.lon;
        input.value = `Autour de moi ${_loc.label}`;
      } else {
        hiddenLatField.value = "";
        hiddenLonField.value = "";
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
      const commonResults = getCommonResults();
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
