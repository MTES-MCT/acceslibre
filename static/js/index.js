import 'core-js/stable';
import 'regenerator-runtime/runtime';

// https://stackoverflow.com/a/47984928
import './jquery';

import 'devbridge-autocomplete';
import 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.locatecontrol';
import 'leaflet-center-cross';
import 'chart.js';
import 'sentry';

import './app';

// https://stackoverflow.com/a/49722514
import('../vendor/selectWoo-1.0.8/js/select2.full.min').then(async (select2) => {
    select2($);
    await import('../vendor/selectWoo-1.0.8/js/i18n/fr.js');
})
