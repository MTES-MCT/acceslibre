import api from '../api'

function GetGeolocBtn(root) {
  root.addEventListener('click', async (event) => {
    await api.getUserLocation()
  })
}

export default GetGeolocBtn
