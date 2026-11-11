import { Check } from "lucide-react";
import { ackAlert } from "../services/api";
import type { Alert } from "../types";
import { fmtTime, levelBg, levelText } from "../utils/risk";

export default function AlertsPanel({ alerts, total }: { alerts: Alert[]; total: number }) {
  return (
    <section className="rounded-lg border border-line bg-panel p-4">
      <h2 className="mb-3 font-semibold">Alerts <span className="text-sm font-normal text-slate-400">({total} this session)</span></h2>
      {alerts.length === 0 ? <p className="text-sm text-slate-400">No alerts yet. They appear here when an object becomes a risk.</p> : (
        <ul className="max-h-96 space-y-2 overflow-y-auto">
          {alerts.map((a) => (
            <li key={a.id} className={`flex items-start justify-between gap-3 rounded-md border p-2.5 text-sm ${a.acknowledged ? "border-line opacity-60" : levelBg[a.severity]}`}>
              <div>
                <div><strong className={levelText[a.severity]}>{a.type}</strong> <span className="text-slate-400">· {a.severity} · {fmtTime(a.video_time)}{a.track_id !== null ? ` · object #${a.track_id}` : ""} · at ({Math.round(a.x)}, {Math.round(a.y)})</span></div>
                <div className="text-slate-300">{a.reason}</div>
              </div>
              {!a.acknowledged && <button onClick={() => ackAlert(a.id).catch(() => {})} className="flex shrink-0 items-center gap-1 rounded border border-line px-2 py-1 text-xs hover:border-accent"><Check size={14} />Acknowledge</button>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
