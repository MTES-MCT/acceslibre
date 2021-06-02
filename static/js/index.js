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
import "leaflet";
import "leaflet.markercluster";
import "leaflet.locatecontrol";
import "leaflet-center-cross";
import "chart.js";

// Sentry
import * as Sentry from "@sentry/browser";
import { Integrations } from "@sentry/tracing";
window.Sentry = Sentry;
window.SentryIntegrations = Integrations;

// app modules
import dom from "./dom";
import geo from "./geo";

import AsteriskField from "./ui/AsteriskField";
import ConditionalForm from "./ui/ConditionalForm.js";
import GeoLink from "./ui/GeoLink.js";
import MapExpander from "./ui/MapExpander";
import SearchWhere from "./ui/SearchWhere";

// Initializations
dom.ready(() => {
  dom.mountOne("#app-map", geo.AppMap);
  dom.mountOne("#map-height-toggle-link", MapExpander);
  dom.mountOne(".a4a-conditional-form", ConditionalForm);
  dom.mountAll(".search-where-field", SearchWhere);
  dom.mountAll(".asteriskField", AsteriskField);
  dom.mountAll(".a4a-geo-link", GeoLink);
});

// expose general namespaced lib for usage within pages
window.a4a = {
  dom,
  geo,
};
