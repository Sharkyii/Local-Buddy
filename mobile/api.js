// React Native port of frontend/src/api.js — same fetch-based calls, just
// localStorage -> AsyncStorage (async) and no live geolocation yet (would
// need expo-location; left as a follow-up, not part of this scaffold).
//
// API_BASE: 127.0.0.1 only resolves to the host machine from an iOS
// simulator. Android emulator needs 10.0.2.2; a physical device (Expo Go)
// needs the host machine's actual LAN IP (e.g. 192.168.1.x) instead.
const API_BASE = "http://127.0.0.1:8000";

import AsyncStorage from "@react-native-async-storage/async-storage";

const USER_ID_KEY = "localbuddy_user_id";

function randomId() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

export async function getOrCreateUserId() {
  let userId = await AsyncStorage.getItem(USER_ID_KEY);
  if (!userId) {
    userId = randomId();
    await AsyncStorage.setItem(USER_ID_KEY, userId);
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

export async function sendMessage(sessionId, message) {
  // No live geolocation yet in this scaffold — lat/lng always null, so
  // distance-based ranking just doesn't activate (same as the web app
  // before a location is granted). Add expo-location here to wire it up.
  const response = await fetch(`${API_BASE}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, lat: null, lng: null }),
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
