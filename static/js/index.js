// Polyfills
import "core-js/stable";
import "mutationobserver-shim";
import "regenerator-runtime/runtime";
import "url-search-params-polyfill";
import "whatwg-fetch";

// jQuery and selectWoo are very special beasts
// https://stackoverflow.com/a/47984928
// https://stackoverflow.com/a/49722514
import jquery from "jquery";
window.$ = window.jQuery = jquery;
import select2 from "../vendor/selectWoo-1.0.8/js/select2.full.min";
select2(window.$);
import("../vendor/selectWoo-1.0.8/js/i18n/fr.js").then();

import "leaflet";
import "leaflet.markercluster";
import "leaflet.locatecontrol";
import "leaflet-center-cross";
import "chart.js";

// Bootstrap
import * as bootstrap from 'bootstrap';

// Sentry
import * as Sentry from "@sentry/browser";
import { Integrations } from "@sentry/tracing";
window.Sentry = Sentry;
window.SentryIntegrations = Integrations;

// app modules
import dom from "./dom";
import geo from "./geo";
import ui from "./ui";
import api from "./api"

// Initializations
dom.ready(() => {
  dom.mountOne("#app-map", geo.AppMap);
  dom.mountOne("#id_code_insee", ui.CommuneSearch);
  dom.mountOne("#localisation-map", ui.LocalisationMap);
  dom.mountOne("#map-height-toggle-link", ui.MapExpander);
  dom.mountOne(".a4a-conditional-form", ui.ConditionalForm);
  dom.mountAll(".search-where-field", ui.SearchWhere);
  dom.mountAll(".asteriskField", ui.AsteriskField);
  dom.mountAll(".a4a-geo-link", ui.GeoLink);
  dom.mountAll(".get-geoloc-btn", ui.GetGeolocBtn);
});

// expose general namespaced lib for usage within pages
window.a4a = {
  dom,
  geo,
};

function update_map(event, query){
  var mapDomEl = document.querySelector(".a4a-localisation-map");
  mapDomEl.style.opacity = 0.3;
  api.getCoordinate(query).then(function(response){
    var result = response.results[0];

    if (mapDomEl !== undefined) {
       mapDomEl._leaflet_id = null;
    }
    const map = geo.createMap(mapDomEl, { scrollWheelZoom: false });
    map.setView(
      {
        lat: result.lat,
        lon: result.lon,
      },
      18
    );

  }).then(function(response){
    mapDomEl.style.opacity = 1;
  });
};

window.onload = function() {
    var src = document.getElementById("id_email"),
        dst = document.getElementById("id_username");

    var numero = document.getElementById("id_numero");
    var voie = document.getElementById("id_voie");
    var lieu_dit = document.getElementById("id_lieu_dit");
    var code_postal = document.getElementById("id_code_postal");
    var ville = document.getElementById("id_commune");

    if(numero){
      numero.addEventListener("change", function (event) {
        var query = numero.value + " " + voie.value + " " + lieu_dit.value + " " + code_postal.value + " " + ville.value;
        update_map(event, query);
        });

      voie.addEventListener("change", function (event) {
        var query = numero.value + " " + voie.value + " " + lieu_dit.value + " " + code_postal.value + " " + ville.value;
        update_map(event, query);
        });

      lieu_dit.addEventListener("change", function (event) {
        var query = numero.value + " " + voie.value + " " + lieu_dit.value + " " + code_postal.value + " " + ville.value;
        update_map(event, query);
        });

      code_postal.addEventListener("change", function (event) {
        var query = numero.value + " " + voie.value + " " + lieu_dit.value + " " + code_postal.value + " " + ville.value;
        update_map(event, query);
        });

      ville.addEventListener("change", function (event) {
        var query = numero.value + " " + voie.value + " " + lieu_dit.value + " " + code_postal.value + " " + ville.value;
        update_map(event, query);
        });
    }


    if (src && dst) {
    src.addEventListener('input', function() {
        dst.value = src.value.split('@')[0];
    });
    }

};
