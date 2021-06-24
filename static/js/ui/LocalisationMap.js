import geo from "../geo";

function LocalisationMap(root) {
  const mapDomEl = root.querySelector(".a4a-localisation-map");
  const hiddenLat = root.querySelector("input[type=hidden][name=lat]");
  const hiddenLon = root.querySelector("input[type=hidden][name=lon]");
  const map = geo.createMap(mapDomEl, { scrollWheelZoom: false });
  map.setView(
    {
      lat: hiddenLat.value,
      lon: hiddenLon.value,
    },
    18
  );
  const control = L.control.centerCross({ show: true, position: "topright" });
  map.addControl(control);
  map.on("move", function (event) {
    const coords = event.target.getCenter();
    hiddenLat.value = coords.lat;
    hiddenLon.value = coords.lng;
  });
}

export default LocalisationMap;
