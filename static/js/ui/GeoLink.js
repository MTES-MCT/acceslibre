import geo from "../geo";

function GeoLink(root) {
  root.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const pk = parseInt(root.dataset?.erpId, 10);
    console.log("Clicked somewhere");
    console.log(pk);
    if (pk) geo.openMarkerPopup(pk);
  });
}

export default GeoLink;
