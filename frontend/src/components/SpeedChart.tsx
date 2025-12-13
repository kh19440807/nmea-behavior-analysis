import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { Sample } from "@/lib/types";

type Props = { samples: Sample[] };

export default function SpeedChart({ samples }: Props) {
  const data = samples.map((s, i) => ({
    i,
    t: s.t,
    speed: s.speed_mps ?? null,
  }));

  return (
    <div className="rounded-2xl shadow p-4 border">
      <div className="font-semibold mb-2">Speed (m/s)</div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="i" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="speed" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
