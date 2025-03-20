import '@gouvfr/dsfr/dist/dsfr/dsfr.module.min.js'

import 'leaflet'
import 'leaflet.markercluster'
import 'leaflet.locatecontrol'
import 'leaflet-center-cross'
import { GestureHandling } from 'leaflet-gesture-handling'

// Bootstrap
import * as bootstrap from 'bootstrap'

// Sentry
import * as Sentry from '@sentry/browser'
import { Integrations } from '@sentry/tracing'
window.Sentry = Sentry
window.SentryIntegrations = Integrations

// app modules
import dom from './js/dom'
import geo from './js/geo'
import ui from './js/ui'
import cloneFilter from './js/ui/CloneFilter'
import Autocomplete from './js/ui/AutocompleteActivity'
import PickAnswerAndSubmit from './js/ui/PickAnswerAndSubmit'
import StoreFilters from './js/ui/StoreFilters'

import posthog from 'posthog-js'

posthog.init('phc_1EAzdaH4YiBLDU8MMGqPk6BjaJF0gvoE3rZH5UQ4IkZ', {
  api_host: 'https://eu.i.posthog.com',
  person_profiles: 'always',
})

// Initializations
dom.ready(() => {
  dom.mountOne('#app-map', geo.AppMap)
  dom.mountOne('.contrib-container', ui.ContribPagination)
  dom.mountOne('.contrib-container', ui.FormContribEditNotification)
  dom.mountOne('#contrib-edit-form', ui.FormContribDirtyChecker)
  dom.mountOne('#localisation-map', ui.LocalisationMap)
  dom.mountOne('#map-height-toggle-link', ui.MapExpander)
  dom.mountOne('.a4a-conditional-form', ui.ConditionalForm)
  dom.mountAll('.search-where-field', ui.SearchWhere)
  dom.mountAll('.asteriskField', ui.AsteriskField)
  dom.mountAll('.a4a-geo-link', ui.GeoLink)
  dom.mountAll('.get-geoloc-btn', ui.GetGeolocBtn)
  dom.mountOne('#export-results-btn', ui.ExportResultsBtn)
  dom.mountOne('#erp-address', ui.SyncInputsWithElement)
  dom.mountAll('.half-progress', ui.ProgressBar)
  dom.mountAll('.a4a-label-tag', ui.LabelTag)
  dom.mountAll('.a4a-clone-filter', cloneFilter.cloneFilter)
  dom.mountOne('#clone-filter-submit', cloneFilter.cloneFilterSubmit)
  dom.mountOne('#no_activity', ui.NewActivity)
  dom.mountOne('#unsure-and-submit', ui.PickAnswerAndSubmit)
  dom.mountOne('#filter-controller', ui.filterData)
  dom.mountAll('.text-expander', ui.TextExpander)
})

ui.StoreFilters()

// expose general namespaced lib for usage within pages
window.a4a = {
  dom,
  geo,
}

window.onload = function () {
  var src = document.getElementById('id_email'),
    dst = document.getElementById('id_username')

  if (src && dst) {
    src.addEventListener('input', function () {
      dst.value = src.value.split('@')[0]
    })
  }

  ui.listenToLabelEvents()
  ui.LoadFilters()
}
