// Icons
import './icons/style.css'

// Leaflet and plugins
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
// Note: parcel is very picky about imported file extensions: you
// MUST omit the .css suffix IF there's a similary named .js file.
// Here leaflet.locatecontrol/dist/L.Control.Locate.min.js exists
// so we MUST skip the file extension.
import 'leaflet.locatecontrol/dist/L.Control.Locate.mapbox.min.css'
import 'leaflet-gesture-handling/dist/leaflet-gesture-handling.css'

// Acceslibre own styles
import './scss/style.scss'

// DSFR
import '@gouvfr/dsfr/dist/dsfr/dsfr.css'
import '@gouvfr/dsfr/dist/utility/icons/icons.css'
import './scss/style-dsfr.scss'
