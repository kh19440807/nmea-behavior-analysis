"use client";

import { MapContainer, TileLayer, Polyline } from "react-leaflet";
import type { Sample } from "@/lib/types";

type Props = { samples: Sample[] };

export default function TrackMap({ samples }: Props) {
  const pts = samples
    .filter((s) => typeof s.lat === "number" && typeof s.lon === "number")
    .map((s) => [s.lat as number, s.lon as number] as [number, number]);

  if (pts.length < 2) {
    return (
      <div className="rounded-2xl shadow p-4 border">
        <div className="font-semibold mb-2">Track</div>
        <div className="text-sm text-gray-500">Not enough valid lat/lon samples.</div>
      </div>
    );
  }

  const center = pts[Math.floor(pts.length / 2)];

  return (
    <div className="rounded-2xl shadow p-4 border">
      <div className="font-semibold mb-2">Track</div>
      <div className="h-72">
        <MapContainer center={center} zoom={15} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Polyline positions={pts} />
        </MapContainer>
      </div>
    </div>
  );
}
