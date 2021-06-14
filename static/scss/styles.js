// Icons
import "../icons/style.css";

// Leaflet and plugins
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
// Note: parcel is very picky about imported file extensions: you
// MUST omit the .css suffix IF there's a similary named .js file.
// Here leaflet.locatecontrol/dist/L.Control.Locate.min.js exists
// so we MUST skip the file extension.
import "leaflet.locatecontrol/dist/L.Control.Locate.min";

// SelectWoo
import "../vendor/selectWoo-1.0.8/css/select2.min.css";
import "../vendor/selectWoo-1.0.8/css/select2-bootstrap4.min.css";

// Acceslibre own styles
import "./style.scss";
