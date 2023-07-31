// Polyfills
import 'core-js/stable'
import 'mutationobserver-shim'
import 'regenerator-runtime/runtime'
import '@gouvfr/dsfr/dist/dsfr/dsfr.module.min.js'

// jQuery and selectWoo are very special beasts
// https://stackoverflow.com/a/47984928
// https://stackoverflow.com/a/49722514
import jquery from 'jquery'
window.$ = window.jQuery = jquery
import select2 from '../vendor/selectWoo-1.0.8/js/select2.full.min'
select2(window.$)
import('../vendor/selectWoo-1.0.8/js/i18n/fr.js').then()

import 'leaflet'
import 'leaflet.markercluster'
import 'leaflet.locatecontrol'
import 'leaflet-center-cross'
import Chart from 'chart.js/auto'
window.Chart = Chart

import { Crisp } from 'crisp-sdk-web'
Crisp.configure('600aff6d-b1eb-414c-a186-233177221bbf')

// Bootstrap
import * as bootstrap from 'bootstrap'

// Sentry
import * as Sentry from '@sentry/browser'
import { Integrations } from '@sentry/tracing'
import '@gouvfr/dsfr/dist/dsfr/dsfr.module.min.js'
window.Sentry = Sentry
window.SentryIntegrations = Integrations

// app modules
import dom from './dom'
import geo from './geo'
import ui from './ui'
import api from './api'

// Initializations
dom.ready(() => {
  dom.mountOne('#app-map', geo.AppMap)
  dom.mountOne('#localisation-map', ui.LocalisationMap)
  dom.mountOne('#map-height-toggle-link', ui.MapExpander)
  dom.mountOne('.a4a-conditional-form', ui.ConditionalForm)
  dom.mountAll('.search-where-field', ui.SearchWhere)
  dom.mountAll('.asteriskField', ui.AsteriskField)
  dom.mountAll('.a4a-geo-link', ui.GeoLink)
  dom.mountAll('.get-geoloc-btn', ui.GetGeolocBtn)
  dom.mountAll('.a4a-label-tag', ui.LabelTag)
  dom.mountOne('#no_activity', ui.NewActivity)
  dom.mountOne('select#activite', ui.ActivitySelect)
})

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
}

// TODO move me to another place ?
document.addEventListener('groupLabelClicked', function (event) {
  let equipmentsGroup = event.detail.source
  let children = equipmentsGroup.getAttribute('data-children').split(',')
  let needRefresh = false
  children.forEach(function (child) {
    if (child) {
      let parent = document.querySelector(`#${child}`).parentNode
      parent.classList.toggle('hidden')
      let inputFilter = parent.querySelector('input')
      inputFilter.checked = !inputFilter.checked
      needRefresh = true
    }
  })

  if (needRefresh) {
    document.dispatchEvent(new Event('filterAdded'))
  }

  // TODO
  // Refresh the api accordingly
})
