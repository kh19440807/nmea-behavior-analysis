"use client";

import { MapContainer, Polyline, TileLayer } from "react-leaflet";

type Sample = {
  t: string;
  lat: number | null;
  lon: number | null;
  speed_mps: number | null;
  cn0_mean_dbhz: number | null;
  cn0_min_dbhz: number | null;
  cn0_max_dbhz: number | null;
  anomaly_flags?: string[];
};

export default function TrackMapClient({ samples }: { samples: Sample[] }) {
  const pts = samples
    .filter((s) => typeof s.lat === "number" && typeof s.lon === "number")
    .map((s) => [s.lat as number, s.lon as number] as [number, number]);

  if (pts.length < 2) {
    return (
      <div className="rounded-2xl shadow p-4 border bg-white">
        <div className="font-semibold mb-2">Track</div>
        <div className="text-sm text-gray-500">
          Not enough valid lat/lon samples.
        </div>
      </div>
    );
  }

  const center = pts[Math.floor(pts.length / 2)];

  return (
    <div className="rounded-2xl shadow p-4 border bg-white">
      <div className="font-semibold mb-2">Track</div>
      <div className="h-72 rounded-lg overflow-hidden">
        <MapContainer center={center} zoom={15} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Polyline positions={pts} />
        </MapContainer>
      </div>
    </div>
  );
}
