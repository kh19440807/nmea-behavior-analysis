// frontend/src/app/page.tsx
"use client";
import dynamic from "next/dynamic";

const TrackMap = dynamic(() => import("@/components/TrackMapClient"), {
  ssr: false,
});


import { useMemo, useState } from "react";
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

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

type AnalyzeResponse = {
  meta: {
    file_name: string;
    analyzed_at: string;
    duration_sec: number;
    sample_count: number;
    gnss_systems: string[];
  };
  summary: {
    total_anomalies: number;
    spoofing_suspected_count: number;
    jamming_suspected_count: number;
    has_spoofing_suspected: boolean;
    has_jamming_suspected: boolean;
  };
  track: { samples: Sample[] };
  anomalies: any[];
  satellite_stats: any[];
  ephemeris_consistency: any;

  // ★ backend から返るようになった
  spoofing_score?: number | null;
};

function riskLabel(score: number) {
  if (score >= 0.8) return { label: "HIGH", cls: "bg-red-600 text-white" };
  if (score >= 0.4) return { label: "MED", cls: "bg-yellow-500 text-black" };
  return { label: "LOW", cls: "bg-green-600 text-white" };
}

function RiskSummary({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const r = riskLabel(score);

  return (
    <div className="rounded-2xl shadow p-4 border flex items-center justify-between bg-white">
      <div>
        <div className="text-sm text-gray-500">Conclusion</div>
        <div className="text-2xl font-semibold">
          Spoofing risk: {pct}%{" "}
          <span className={`ml-2 px-2 py-1 rounded-lg text-sm ${r.cls}`}>
            {r.label}
          </span>
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Probability from ML model (trained/evaluated on MARSIM dataset).
        </div>
      </div>
    </div>
  );
}

function Cn0Chart({ samples }: { samples: Sample[] }) {
  const data = useMemo(
    () =>
      samples.map((s, i) => ({
        i,
        cn0_mean: s.cn0_mean_dbhz ?? null,
        cn0_min: s.cn0_min_dbhz ?? null,
        cn0_max: s.cn0_max_dbhz ?? null,
      })),
    [samples]
  );

  return (
    <div className="rounded-2xl shadow p-4 border bg-white">
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
        This chart uses mean/min/max C/N0 aggregated from NMEA-derived fields.
      </div>
    </div>
  );
}

function SpeedChart({ samples }: { samples: Sample[] }) {
  const data = useMemo(
    () =>
      samples.map((s, i) => ({
        i,
        speed: s.speed_mps ?? null,
      })),
    [samples]
  );

  return (
    <div className="rounded-2xl shadow p-4 border bg-white">
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

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) {
      setError("NMEAログファイルを選択してください");
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data: AnalyzeResponse = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(`解析に失敗しました: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const samples = result?.track?.samples ?? [];
  const spoofingScore =
    typeof result?.spoofing_score === "number" ? result.spoofing_score : null;

  return (
    <main className="min-h-screen bg-slate-100 flex flex-col items-center py-10">
      <div className="w-full max-w-5xl space-y-6">
        <div className="bg-white rounded-xl shadow p-6 space-y-6">
          <h1 className="text-2xl font-bold">GNSS Anomaly Detector (MVP)</h1>

          <div className="space-y-3">
            <label className="block text-sm font-medium">
              NMEAログファイルをアップロード
            </label>
            <input
              type="file"
              accept=".nmea,.txt,.log"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm"
            />
            <button
              onClick={handleUpload}
              disabled={loading}
              className="px-4 py-2 rounded bg-blue-600 text-white text-sm font-semibold disabled:opacity-50"
            >
              {loading ? "解析中..." : "解析する"}
            </button>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        </div>

        {result && spoofingScore != null && (
          <RiskSummary score={spoofingScore} />
        )}

        {result && (
          <div className="bg-white rounded-xl shadow p-6 space-y-6">
            <h2 className="text-lg font-semibold">解析結果サマリー</h2>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="p-3 rounded bg-slate-50 border">
                <div className="text-xs text-slate-500">ファイル名</div>
                <div className="font-mono text-xs">{result.meta.file_name}</div>
              </div>

              <div className="p-3 rounded bg-slate-50 border">
                <div className="text-xs text-slate-500">総異常数（ルール）</div>
                <div className="text-lg font-bold">{result.summary.total_anomalies}</div>
              </div>

              <div className="p-3 rounded bg-slate-50 border">
                <div className="text-xs text-slate-500">スプーフィング疑い（ルール）</div>
                <div className="text-lg font-bold">
                  {result.summary.spoofing_suspected_count}
                </div>
              </div>

              <div className="p-3 rounded bg-slate-50 border">
                <div className="text-xs text-slate-500">ジャミング疑い（ルール）</div>
                <div className="text-lg font-bold">
                  {result.summary.jamming_suspected_count}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Cn0Chart samples={samples} />
              <SpeedChart samples={samples} />
            </div>

            <TrackMap samples={samples} />

            <details className="mt-4">
              <summary className="cursor-pointer text-sm text-blue-600">
                生JSONを見る（デバッグ用）
              </summary>
              <pre className="mt-2 text-xs bg-slate-900 text-slate-100 p-3 rounded overflow-x-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </main>
  );
}
