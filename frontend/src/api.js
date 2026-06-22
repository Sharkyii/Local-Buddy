// Plain fetch wrapper around the FastAPI chat layer — no React-specific code,
// so this file ports directly to React Native later.

const API_BASE = "http://127.0.0.1:8000";

export function getOrCreateUserId() {
  const key = "localbuddy_user_id";
  let userId = localStorage.getItem(key);
  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem(key, userId);
  }
  return userId;
}

export async function createSession(cityId, userId) {
  const response = await fetch(`${API_BASE}/chat/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ city_id: cityId, user_id: userId }),
  });
  if (!response.ok) throw new Error(`Failed to create session (${response.status})`);
  const data = await response.json();
  return data.session_id;
}

// Fresh GPS fix on every message (not cached) so distance-based results stay
// accurate if the traveler is walking around the city. Resolves to {lat:null,
// lng:null} on denial/timeout/unsupported browsers rather than rejecting —
// location is a nice-to-have, never a blocker for sending a message.
function getCurrentLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve({ lat: null, lng: null });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve({ lat: position.coords.latitude, lng: position.coords.longitude }),
      () => resolve({ lat: null, lng: null }),
      { timeout: 5000, maximumAge: 30000 },
    );
  });
}

export async function sendMessage(sessionId, message) {
  const { lat, lng } = await getCurrentLocation();
  const response = await fetch(`${API_BASE}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, lat, lng }),
  });
  if (!response.ok) throw new Error(`Failed to send message (${response.status})`);
  const data = await response.json();
  return data.reply;
}

export async function getHistory(sessionId) {
  const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}/history`);
  if (!response.ok) throw new Error(`Failed to load history (${response.status})`);
  return response.json();
}
