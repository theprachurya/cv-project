import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { getSessionAlerts, getSessionDetections, getSessions, reportUrl } from "../services/api";
import type { Alert, DetectionEvent, SessionRow } from "../types";
import { fmtTime, levelText } from "../utils/risk";

export default function History() {
  const [rows, setRows] = useState<SessionRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<{ id: number; alerts: Alert[] } | null>(null);
  const [detectionRows, setDetectionRows] = useState<{ id: number; rows: DetectionEvent[] } | null>(null);
  useEffect(() => { getSessions().then(setRows).catch((e) => setErr(e.message)); }, []);
  if (err) return <p className="text-sm text-risk-high">{err}</p>;
  if (!rows) return <p className="text-sm text-slate-400">Loading sessions…</p>;
  if (!rows.length) return <p className="text-sm text-slate-400">No analysis sessions yet. Run an analysis from the dashboard.</p>;
  return (
    <section className="rounded-lg border border-line bg-panel p-4">
      <h2 className="mb-3 font-semibold">Past analysis sessions</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400"><tr>{["#", "Source", "Started", "Status", "Frames", "Objects", "Alerts", "High risk", ""].map((h) => <th key={h} className="py-1 pr-4 font-normal">{h}</th>)}</tr></thead>
          <tbody className="tabular-nums">
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-line">
                <td className="py-1.5 pr-4">{r.id}</td><td className="pr-4">{r.filename ?? r.source}</td><td className="pr-4">{new Date(r.started_at + "Z").toLocaleString()}</td>
                <td className="pr-4">{r.status}</td><td className="pr-4">{r.frames_processed}</td><td className="pr-4">{r.unique_objects}</td><td className="pr-4">{r.total_alerts}</td><td className="pr-4">{r.high_risk_events}</td>
                <td className="flex gap-2 py-1">
                  <button className="rounded border border-line px-2 py-1 text-xs hover:border-accent" onClick={() => getSessionAlerts(r.id).then((alerts) => setOpen({ id: r.id, alerts })).catch((e) => setErr(e.message))}>View alerts</button>
                  <button className="rounded border border-line px-2 py-1 text-xs hover:border-accent" onClick={() => getSessionDetections(r.id).then((rows) => setDetectionRows({ id: r.id, rows })).catch((e) => setErr(e.message))}>View detections</button>
                  {r.status !== "running" && <a className="flex items-center gap-1 rounded border border-line px-2 py-1 text-xs hover:border-accent" href={reportUrl(r.id)}><Download size={13} />PDF report</a>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {open && (
        <div className="mt-4 border-t border-line pt-3">
          <h3 className="mb-2 text-sm text-slate-300">Alerts for session {open.id}</h3>
          {open.alerts.length === 0 ? <p className="text-sm text-slate-400">This session generated no alerts.</p> : (
            <ul className="space-y-1 text-sm">{open.alerts.map((a) => <li key={a.id}><span className={levelText[a.severity]}>{a.type}</span> · {fmtTime(a.video_time)} · {a.reason}</li>)}</ul>)}
        </div>
      )}
      {detectionRows && (
        <div className="mt-4 border-t border-line pt-3">
          <h3 className="mb-2 text-sm text-slate-300">Latest detections for session {detectionRows.id} (up to 50)</h3>
          {detectionRows.rows.length === 0 ? <p className="text-sm text-slate-400">This session recorded no detections.</p> : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="text-slate-400"><tr>{["Video time", "Frame", "Object", "Confidence", "Motion", "Nearness", "Risk"].map((h) => <th key={h} className="py-1 pr-4 font-normal">{h}</th>)}</tr></thead>
                <tbody>{detectionRows.rows.map((d) => <tr key={d.id} className="border-t border-line">
                  <td className="py-1 pr-4">{fmtTime(d.video_time)}</td><td className="pr-4">{d.frame}</td>
                  <td className="pr-4">{d.label} #{d.track_id}</td><td className="pr-4">{Math.round(d.confidence * 100)}%</td>
                  <td className="pr-4">{d.motion}</td><td className="pr-4">{Math.round(d.proximity * 100)}%</td>
                  <td className={levelText[d.risk_level]}>{d.risk_level} ({d.risk_score})</td>
                </tr>)}</tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
