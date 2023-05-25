import api from "../api";
import dom from "../dom";
import Autocomplete from "@trevoreyre/autocomplete-js";


async function getCommonResults(loc) {
  const AROUND_ME = gettext("Autour de moi");
  const FRANCE_ENTIERE = gettext("France entière");
  return [
    { id: "around_me", text: `${AROUND_ME} ${loc?.label || ""}`, icon: "street-view" },
    { id: "france_entiere", text: FRANCE_ENTIERE, icon: "france" },
  ];
}

function SearchWhere(root) {
  const AROUND_ME = gettext("Autour de moi");
  const FRANCE_ENTIERE = gettext("France entière");
  const input = root.querySelector("input[name=where]");
  const a11yGeolocBtn = document.querySelector(".get-geoloc-btn");
  const hiddens = {
    lat: root.querySelector("input[name=lat]"),
    lon: root.querySelector("input[name=lon]"),
    code: root.querySelector("input[name=code]"),
  };
  input.addEventListener('input', activate_submit_btn, false);
  activate_submit_btn(event = false, force = false)



  function activate_submit_btn(event, force = false) {
    if (hiddens.code.value.length == 0) {
      input.form.querySelector("button[type=submit]").setAttribute('disabled', '');
    };
    if (force || hiddens.code.value) {
      input.form.querySelector("button[type=submit]").removeAttribute('disabled');
    };
  }

  function setSearchData(loc) {
    hiddens.lat.value = loc?.lat || "";
    hiddens.lon.value = loc?.lon || "";
    hiddens.code.value = loc?.code || "";
  }

  function setSearchValue(label) {
    input.value = label;
  }

  function setGeoLoading(loading) {
    if (loading) {
      input.type = "text";
      input.form.addEventListener("submit", dom.preventDefault);
      dom.addClass(input, "disabled", "loading");
    } else {
      input.type = "search";
      input.form.removeEventListener("submit", dom.preventDefault);
      dom.removeClass(input, "disabled", "loading");
    }
  }

  const autocomplete = new Autocomplete(root, {
    debounceTime: 100,

    getResultValue: ({ text }) => text,

    onSubmit: async (result) => {
      if (!result) {
        return;
      }
      activate_submit_btn(event = false, force = true);
      if (result.lat && result.lon) {
        setSearchData(result);
      } else if (result.text.startsWith(AROUND_ME)) {
        if (await api.hasPermission("geolocation") !== "granted") {
          a11yGeolocBtn.focus();
        }
        setGeoLoading(true);
        const loc = await api.loadUserLocation({ retrieve: true });
        setGeoLoading(false);
        if (!loc) {
          console.warn("Impossible de récupérer votre localisation ; vérifiez les autorisations de votre navigateur");
          setSearchData(null);
          setSearchValue("");
          input.focus();
        } else {
          setSearchData(loc);
          setSearchValue(`${AROUND_ME} ${loc.label}`);
          input.form.querySelector("button[type=submit]").focus();
        }
      } else {
        setSearchData(null);
      }
    },

    renderResult: ({ text, context, icon }, props) => {
      const active = props["aria-selected"] ? "active" : "";
      return `
        <li class="list-group-item a4a-autocomplete-result ${active}" ${props}>
          ${icon ? `<i aria-hidden="true" class="icon icon-${icon}"></i>` : ""}
          ${text}
          ${context ? `<small class="text-truncate">${context}</small>` : ""}
        </li>
      `;
    },

    search: async (input) => {
      const loc = await api.loadUserLocation({ retrieve: false });
      const commonResults = await getCommonResults(loc);
      if (input.length <= 2 || input === FRANCE_ENTIERE || input.startsWith(AROUND_ME)) {
        return commonResults;
      }
      var { results } = await api.searchLocation(input, loc, 'municipality');
      if (results.length) {
        return results;
      }

      var { results } = await api.searchLocation(input, loc);
      return results;
    },
  });

  // Invalidate lat/lon on every key stroke in the search input, except when user tabs
  // out of the field or selects and entry by pressing the Enter key.
  autocomplete.input.addEventListener("keydown", (event) => {
    if (event.key != "Tab" && event.key != "Enter") {
      setSearchData(null);
    }
  });

  autocomplete.input.addEventListener("keydown", (event) => {
    if (event.key != "Tab" && event.key != "Enter") {
      setSearchData(null);
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
      } catch (e) { }
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
