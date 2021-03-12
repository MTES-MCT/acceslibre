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
  const { features } = await reverseGeocode({ lat, lon }, { type: "street" });
  let label;
  try {
    label = `(${features[0].properties.label})`;
  } catch (_) {
    label = `(${lat}, ${lon})`;
  }
  return { lat, lon, label };
}

async function reverseGeocode({ lat, lon }, options = {}) {
  let url = `https://api-adresse.data.gouv.fr/reverse/?lon=${lon}&lat=${lat}`;
  if (options.type) {
    url += `&type=${options.type}`;
  }
  const res = await fetch(url);
  return await res.json();
}

export default {
  getUserLocation,
  reverseGeocode,
};
