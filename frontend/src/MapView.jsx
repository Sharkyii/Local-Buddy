import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const API_BASE = "http://127.0.0.1:8000";

// One color per marker type, so density/coverage is visible at a glance.
const COLORS = {
  place: "#e8b339",
  restaurant: "#e85d4a",
  hotel: "#4a90e8",
  area: "#7a4ae8",
};

export default function MapView({ cityId }) {
  const [markers, setMarkers] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/map/markers?city_id=${cityId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load markers (${res.status})`);
        return res.json();
      })
      .then(setMarkers)
      .catch((e) => setError(e.message));
  }, [cityId]);

  if (error) return <div className="error">{error}</div>;
  if (markers.length === 0) return <div className="map-loading">Loading map…</div>;

  // Center on the average of the (few, manually-curated, city-representative) area
  // markers rather than markers[0] — an arbitrary OSM-collected place can be way out
  // on the city's edge (or beyond it) and would otherwise open the map off-center.
  const areas = markers.filter((m) => m.type === "area");
  const centerSource = areas.length > 0 ? areas : markers;
  const center = [
    centerSource.reduce((sum, m) => sum + m.lat, 0) / centerSource.length,
    centerSource.reduce((sum, m) => sum + m.lng, 0) / centerSource.length,
  ];

  return (
    <div className="map-view">
      <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {markers.map((m, i) => (
          <CircleMarker
            key={i}
            center={[m.lat, m.lng]}
            radius={m.type === "area" ? 10 : 6}
            pathOptions={{ color: COLORS[m.type] || "#999", fillOpacity: 0.8 }}
          >
            <Popup>
              <strong>{m.name}</strong>
              <br />
              {m.type}
              {m.category ? ` — ${m.category}` : ""}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
      <div className="map-legend">
        {Object.entries(COLORS).map(([type, color]) => (
          <span key={type} className="legend-item">
            <span className="legend-dot" style={{ background: color }} />
            {type}
          </span>
        ))}
      </div>
    </div>
  );
}
