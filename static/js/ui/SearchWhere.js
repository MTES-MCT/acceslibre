import Autocomplete from "@trevoreyre/autocomplete-js";

function SearchWhere(root) {
  let canSubmit = false;
  const hiddenField = root.querySelector("input[type=hidden]");
  const whereUrl = root.querySelector("input[type=search]").dataset.src;
  const autocomplete = new Autocomplete(root, {
    debounceTime: 100,

    getResultValue: (result) => result.text,

    onSubmit: (result) => {
      if (result) {
        hiddenField.value = result.id;
        canSubmit = true;
      }
    },

    renderResult: (result, props) => {
      const active = props["aria-selected"] ? "active" : "";
      return `
        <li class="list-group-item a4a-slightly-smaller px-3 py-2 ${active}" ${props}>
          ${result.text}
        </li>
      `;
    },

    search: async (input) => {
      if (input.length < 1) {
        return [];
      }
      const res = await fetch(`${whereUrl}?q=${input}`);
      const json = await res.json();
      return [
        { id: "around_me", text: "Autour de moi" },
        { id: "france_entiere", text: "France entière" },
      ].concat(json.results);
    },
  });

  // Prevent global form submission when an entry is selected
  // @see https://github.com/trevoreyre/autocomplete/issues/45#issuecomment-617216849
  autocomplete.input.addEventListener("keydown", (event) => {
    const { key } = event;
    if (canSubmit && key == "Enter") {
      event.preventDefault();
      canSubmit = false;
    }
  });
  return autocomplete;
}

export default SearchWhere;
