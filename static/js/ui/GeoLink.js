import geo from "../geo";

function GeoLink(root) {
  root.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const pk = parseInt(root.dataset?.erpId, 10);
    if (pk) geo.openMarkerPopup(pk);
  });
}

export default GeoLink;
