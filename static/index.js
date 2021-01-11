import 'core-js/stable';
import 'regenerator-runtime/runtime';

import jquery from 'jquery';
window.$ = window.jQuery = jquery;
import 'devbridge-autocomplete';

import 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.locatecontrol';
import 'leaflet-center-cross';
import 'chart.js';
import 'sentry';

import './js/app';

import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import 'leaflet.locatecontrol/dist/L.Control.Locate.min.css'
import './scss/style.scss';
import './icons/styles.css'

if (module.hot) {
    module.hot.accept()
}

console.log("hello world !");
