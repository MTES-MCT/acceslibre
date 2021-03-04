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
import forms from "./forms";
import geo from "./geo";
import search from "./search";

import "./app";

// general DOM-dependent initializations
window.addEventListener("DOMContentLoaded", () => {
  // geo
  geo.handleGeoLinks();
  // forms
  forms.a11y.improveRequiredFieldsA11y();
  forms.conditional.run({
    fieldSelectorPrefix: ".field-",
    inputNamePrefix: "",
  });
});

// expose general namespaced lib for use withing pages
window.a4a = {
  geo,
  forms,
  search,
};
