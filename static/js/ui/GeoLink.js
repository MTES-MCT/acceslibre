import geo from "../geo";

function GeoLink(root) {
  root.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const identifier = root.dataset?.erpIdentifier;
    if (identifier) geo.openMarkerPopup(identifier);
  });
}

export default GeoLink;
