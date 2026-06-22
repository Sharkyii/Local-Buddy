import { useEffect, useState } from "react";
import { createSession, getOrCreateUserId } from "./api.js";
import ChatWindow from "./ChatWindow.jsx";

// Hardcoded for now — there's no "list cities" repository method yet.
const CITIES = [
  { id: "ahmedabad", label: "Ahmedabad" },
  { id: "mumbai", label: "Mumbai" },
  { id: "gwalior", label: "Gwalior" },
  { id: "bangalore", label: "Bangalore" },
];

const userId = getOrCreateUserId();

export default function App() {
  const [cityId, setCityId] = useState(CITIES[0].id);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const storedKey = `localbuddy_session_${cityId}`;
    const stored = localStorage.getItem(storedKey);
    if (stored) {
      setSessionId(stored);
      return;
    }
    createSession(cityId, userId)
      .then((id) => {
        localStorage.setItem(storedKey, id);
        setSessionId(id);
      })
      .catch((e) => setError(e.message));
  }, [cityId]);

  return (
    <div className="app">
      <header>
        <h1>Local Buddy</h1>
        <select value={cityId} onChange={(e) => setCityId(e.target.value)}>
          {CITIES.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>
      </header>
      {error && <div className="error">{error}</div>}
      {sessionId && <ChatWindow sessionId={sessionId} />}
    </div>
  );
}
