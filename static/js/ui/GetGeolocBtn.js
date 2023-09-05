import api from '../api'

function GetGeolocBtn(root) {
  // TODO check if this is still working
  root.addEventListener('click', async (event) => {
    await api.loadUserLocation()
  })
}

export default GetGeolocBtn
