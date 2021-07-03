import api from "../api";

function GetGeolocBtn(root) {
  root.addEventListener("click", async (event) => {
    await api.loadUserLocation({ retrieve: true });
  });
}

export default GetGeolocBtn;
