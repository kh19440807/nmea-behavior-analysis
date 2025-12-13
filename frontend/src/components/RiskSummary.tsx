type Props = { score: number };

function riskLabel(score: number) {
  if (score >= 0.8) return { label: "HIGH", cls: "bg-red-600 text-white" };
  if (score >= 0.4) return { label: "MED", cls: "bg-yellow-500 text-black" };
  return { label: "LOW", cls: "bg-green-600 text-white" };
}

export default function RiskSummary({ score }: Props) {
  const pct = Math.round(score * 100);
  const r = riskLabel(score);

  return (
    <div className="rounded-2xl shadow p-4 border flex items-center justify-between">
      <div>
        <div className="text-sm text-gray-500">Conclusion</div>
        <div className="text-2xl font-semibold">
          Spoofing risk: {pct}%{" "}
          <span className={`ml-2 px-2 py-1 rounded-lg text-sm ${r.cls}`}>
            {r.label}
          </span>
        </div>
        <div className="text-sm text-gray-500 mt-1">
          (Probability from ML model trained on MARSIM)
        </div>
      </div>
    </div>
  );
}
