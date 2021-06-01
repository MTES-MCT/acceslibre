function decodeJson(json) {
  return JSON.parse(atob(json));
}

function encodeJson(js) {
  return btoa(JSON.stringify(js));
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
  let loc = loadUserLocation();
  if (loc) {
    return loc;
  }
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
  loc = { lat, lon, label, timestamp: new Date().getTime() };
  saveUserLocation(loc);
  return loc;
}

function loadUserLocation(ttl = 5 * 60000) {
  try {
    let loc = decodeJson(sessionStorage["a4a-loc"] || "null");
    if (loc.timestamp && new Date().getTime() - loc.timestamp > ttl) {
      return saveUserLocation(null);
    } else {
      return loc;
    }
  } catch (e) {}
}

async function reverseGeocode({ lat, lon }, options = {}) {
  let url = `https://api-adresse.data.gouv.fr/reverse/?lon=${lon}&lat=${lat}`;
  if (options.type) {
    url += `&type=${options.type}`;
  }
  const res = await fetch(url);
  return await res.json();
}

function saveUserLocation(loc) {
  sessionStorage["a4a-loc"] = encodeJson(loc);
  return loc;
}

export default {
  getUserLocation,
  loadUserLocation,
  reverseGeocode,
  saveUserLocation,
};
