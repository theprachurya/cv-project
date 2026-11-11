import type { TrackInfo } from "../types";
import { levelText } from "../utils/risk";

const arrow = { approaching: "toward camera", receding: "away", lateral: "sideways", stationary: "still" } as const;

export default function MotionPanel({ tracks }: { tracks: TrackInfo[] }) {
  const rows = tracks.slice().sort((a, b) => b.risk_score - a.risk_score);
  return (
    <section className="rounded-lg border border-line bg-panel p-4">
      <h2 className="mb-1 font-semibold">Motion analysis</h2>
      <p className="mb-3 text-xs text-slate-500">Depth is relative (near / medium / far), not meters. Time-to-collision assumes constant closing speed.</p>
      {rows.length === 0 ? <p className="text-sm text-slate-400">No objects are being tracked right now.</p> : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400"><tr>{["ID", "Class", "Direction", "Speed (px/s)", "Motion (px/frame)", "Depth", "Time to collision", "Risk"].map((h) => <th key={h} className="py-1 pr-4 font-normal">{h}</th>)}</tr></thead>
            <tbody className="tabular-nums">
              {rows.map((t) => (
                <tr key={t.id} className="border-t border-line">
                  <td className="py-1.5 pr-4">#{t.id}</td><td className="pr-4">{t.label}</td><td className="pr-4">{arrow[t.motion]}</td>
                  <td className="pr-4">{t.speed}</td><td className="pr-4">{t.dx >= 0 ? "+" : ""}{t.dx}, {t.dy >= 0 ? "+" : ""}{t.dy}</td>
                  <td className="pr-4">{t.depth_label}</td><td className="pr-4">{t.ttc !== null ? `${t.ttc}s` : "–"}</td>
                  <td className={levelText[t.risk_level]}>{t.risk_score} {t.risk_level}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
