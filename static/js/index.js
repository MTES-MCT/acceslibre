import "core-js/stable";
import "regenerator-runtime/runtime";

// jQuery and selectWoo are very special beasts
// https://stackoverflow.com/a/47984928
// https://stackoverflow.com/a/49722514
import jquery, { Autocomplete } from "jquery";
window.$ = window.jQuery = jquery;
import select2 from "../vendor/selectWoo-1.0.8/js/select2.full.min";
select2(window.$);
import("../vendor/selectWoo-1.0.8/js/i18n/fr.js").then();

import "bootstrap/js/dist/collapse";
import "bootstrap/js/dist/tab";
import "devbridge-autocomplete";
import "leaflet";
import "leaflet.markercluster";
import "leaflet.locatecontrol";
import "leaflet-center-cross";
import "chart.js";
import "sentry";

// app modules
import dom from "./dom";
import geo from "./geo";

import AppAutocomplete from "./ui/AppAutocomplete";
import AsteriskField from "./ui/AsteriskField";
import ConditionalForm from "./ui/ConditionalForm.js";
import GeoLink from "./ui/GeoLink.js";
import SearchForm from "./ui/SearchForm";

// Initializations
dom.ready(() => {
  dom.mountOne("#app-autocomplete", AppAutocomplete);
  dom.mountOne("#app-map", geo.AppMap);
  dom.mountOne(".a4a-conditional-form", ConditionalForm);
  dom.mountOne("#search-form", SearchForm);
  dom.mountAll(".asteriskField", AsteriskField);
  dom.mountAll(".a4a-geo-link", GeoLink);
});

// expose general namespaced lib for usage within pages
window.a4a = {
  dom,
  geo,
};
