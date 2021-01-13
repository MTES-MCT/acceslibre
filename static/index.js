import 'core-js/stable';
import 'regenerator-runtime/runtime';

import './js/jquery';

import 'devbridge-autocomplete';
import 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.locatecontrol';
import 'leaflet-center-cross';
import 'chart.js';
import 'sentry';

import('./js/app').then();

import './icons/styles.css'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import 'leaflet.locatecontrol/dist/L.Control.Locate.min.css'

import './vendor/selectWoo-1.0.8/css/select2.min.css'
import './vendor/selectWoo-1.0.8/css/select2-bootstrap4.min.css'
import './scss/style.scss';

console.log('toto', $, $().autocomplete)

if (module.hot) {
    module.hot.accept()
}