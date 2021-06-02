function decodeJson(json) {
  try {
    return JSON.parse(atob(json));
  } catch (e) {
    return null;
  }
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
  const {
    coords: { latitude: lat, longitude: lon },
    timestamp,
  } = await getCurrentPosition(options);
  const { features } = await reverseGeocode({ lat, lon }, { type: "street" });
  let label;
  try {
    label = `(${features[0].properties.label})`;
  } catch (_) {
    label = `(${lat}, ${lon})`;
  }
  return saveUserLocation({ lat, lon, label, timestamp });
}

async function loadUserLocation(options = {}) {
  const { ttl, retrieve } = { ttl: 5 * 60000, retrieve: true, ...options };
  try {
    const loc = decodeJson(sessionStorage["a4a-loc"] || "null");
    if (!loc || (loc.timestamp && new Date().getTime() - loc.timestamp > ttl)) {
      if (retrieve) {
        return await getUserLocation();
      } else {
        return loc;
      }
    } else {
      return loc;
    }
  } catch (e) {
    console.error(e);
  }
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
