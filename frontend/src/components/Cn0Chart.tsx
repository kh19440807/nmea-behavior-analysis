import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { Sample } from "@/lib/types";

type Props = { samples: Sample[] };

export default function Cn0Chart({ samples }: Props) {
  const data = samples.map((s, i) => ({
    i,
    t: s.t,
    cn0_mean: s.cn0_mean_dbhz ?? null,
    cn0_min: s.cn0_min_dbhz ?? null,
    cn0_max: s.cn0_max_dbhz ?? null,
  }));

  return (
    <div className="rounded-2xl shadow p-4 border">
      <div className="font-semibold mb-2">C/N0 (dB-Hz)</div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="i" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="cn0_mean" dot={false} />
            <Line type="monotone" dataKey="cn0_min" dot={false} />
            <Line type="monotone" dataKey="cn0_max" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="text-xs text-gray-500 mt-2">
        Note: per-satellite C/N0 is not available yet; this shows mean/min/max from NMEA-derived aggregates.
      </div>
    </div>
  );
}
