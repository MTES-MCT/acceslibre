async function reverseGeocode({ lat, lon }) {
  const res = await fetch(`https://api-adresse.data.gouv.fr/reverse/?lon=${lon}&lat=${lat}&type=street`);
  return await res.json();
}

function getCurrentPosition(options = { timeout: 10000 }) {
  return new Promise((resolve, reject) => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(resolve, reject, options);
    } else {
      reject("La géolocalisation n'est pas disponible sur votre navigateur.");
    }
  });
}

async function getUserLocation(options) {
  const {
    coords: { latitude: lat, longitude: lon },
  } = await getCurrentPosition(options);
  const { features } = await reverseGeocode({ lat, lon });
  let label;
  try {
    label = `(${features[0].properties.label})`;
  } catch (_) {
    label = `(${lat}, ${lon})`;
  }
  return { lat, lon, label };
}

export default {
  getUserLocation,
};
