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
import SearchForm from "./ui/SearchForm";
import a11y from "./ui/a11y.js";
import ConditionalForm from "./ui/ConditionalForm.js";

// Initializations
dom.ready(() => {
  geo.handleGeoLinks(dom.findAll(".a4a-geo-link"));
  a11y.improveRequiredFieldsA11y();

  // Conditional forms
  const conditionalForm = document.querySelector(".a4a-conditional-form");
  if (conditionalForm) {
    ConditionalForm(conditionalForm);
  }

  // Global search form
  const searchForm = document.querySelector("form#search-form");
  if (searchForm) {
    SearchForm(searchForm);
  }

  // App autocomplete
  const appAutocomplete = document.querySelector("#app-autocomplete");
  if (appAutocomplete) {
    AppAutocomplete(appAutocomplete);
  }
});

// expose general namespaced lib for usage withing pages
window.a4a = {
  dom,
  geo,
};
