import type { AnalysisState, Side } from "../types";
import { levelBg, levelText } from "../utils/risk";

function SideBox({ name, s }: { name: string; s: Side }) {
  return (
    <div className={`rounded-md border p-3 ${levelBg[s.level]}`}>
      <div className="text-xs text-slate-400">{name} zone</div>
      <div className={`font-semibold ${levelText[s.level]}`}>{s.level === "clear" ? "Clear" : s.level === "low" ? "Vehicle present" : `${name.toUpperCase()} ALERT`}</div>
      {s.ids.length > 0 && <div className="text-xs text-slate-400">Objects {s.ids.map((i) => `#${i}`).join(", ")}</div>}
    </div>
  );
}

export default function RiskPanel({ s }: { s: AnalysisState | null }) {
  const lvl = s?.overall.level ?? "low";
  const counts = s?.counts ?? {};
  const rows: [string, number][] = [
    ["Vehicles (unique)", (s?.summary.vehicles ?? 0)], ["Pedestrians (unique)", counts.pedestrian ?? 0],
    ["Tracked now", s?.objects_in_frame ?? 0], ["Unique objects", s?.unique_objects ?? 0],
  ];
  return (
    <section className="space-y-3 rounded-lg border border-line bg-panel p-4">
      <h2 className="font-semibold">Road safety risk</h2>
      <div className={`rounded-md border p-4 ${levelBg[lvl]}`}>
        <div className="text-xs text-slate-400">Overall risk</div>
        <div className="flex items-baseline gap-2"><span className={`text-4xl font-semibold tabular-nums ${levelText[lvl]}`}>{s?.overall.score ?? 0}</span>
          <span className="text-sm text-slate-300">/100 · {lvl}</span></div>
        <div className="mt-1 text-xs text-slate-400">{s?.alert_count ?? 0} alerts this session · {s?.fps ?? 0} fps · depth: {s?.depth_backend ?? "–"}</div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <SideBox name="Left" s={s?.blind_spots.left ?? { level: "clear", ids: [] }} />
        <SideBox name="Right" s={s?.blind_spots.right ?? { level: "clear", ids: [] }} />
      </div>
      <dl className="space-y-1.5 text-sm">
        {rows.map(([k, v]) => <div key={k} className="flex justify-between"><dt className="text-slate-400">{k}</dt><dd className="tabular-nums">{v}</dd></div>)}
      </dl>
    </section>
  );
}
