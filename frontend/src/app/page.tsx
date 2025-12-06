// frontend/src/app/page.tsx
"use client";

import { useState } from "react";

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
  track: any;
  anomalies: any[];
  satellite_stats: any[];
  ephemeris_consistency: any;
};

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

  return (
    <main className="min-h-screen bg-slate-100 flex flex-col items-center py-10">
      <div className="w-full max-w-3xl bg-white rounded-xl shadow p-6 space-y-6">
        <h1 className="text-2xl font-bold">
          GNSS Anomaly Detector (MVP)
        </h1>

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

        {result && (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">解析結果サマリー</h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="p-3 rounded bg-slate-50 border">
                <div className="text-xs text-slate-500">ファイル名</div>
                <div className="font-mono text-xs">
                  {result.meta.file_name}
                </div>
              </div>
              <div className="p-3 rounded bg-slate-50 border">
                <div className="text-xs text-slate-500">総異常数</div>
                <div className="text-lg font-bold">
                  {result.summary.total_anomalies}
                </div>
              </div>
              <div className="p-3 rounded bg-slate-50 border">
                <div className="text-xs text-slate-500">
                  スプーフィング疑い
                </div>
                <div className="text-lg font-bold">
                  {result.summary.spoofing_suspected_count}
                </div>
              </div>
              <div className="p-3 rounded bg-slate-50 border">
                <div className="text-xs text-slate-500">
                  ジャミング疑い
                </div>
                <div className="text-lg font-bold">
                  {result.summary.jamming_suspected_count}
                </div>
              </div>
            </div>

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
