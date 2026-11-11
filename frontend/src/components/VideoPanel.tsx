import { useRef } from "react";
import { Camera, Loader2, Pause, Play, RotateCcw, Square, Upload } from "lucide-react";
import type { useAnalysis } from "../hooks/useAnalysis";
import type { RuntimeSettings } from "../types";
import { levelBg, levelText } from "../utils/risk";

type A = ReturnType<typeof useAnalysis>;
const btn = "flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm hover:border-accent disabled:opacity-40 disabled:hover:border-line";
const VIEWS: { id: RuntimeSettings["view"]; label: string }[] = [
  { id: "detection", label: "Detection" }, { id: "flow", label: "Optical flow" }, { id: "depth", label: "Depth map" },
];

export default function VideoPanel({ a, view, setView }: { a: A; view: RuntimeSettings["view"]; setView: (v: RuntimeSettings["view"]) => void }) {
  const file = useRef<HTMLInputElement>(null);
  const st = a.state?.status ?? "idle";
  const active = st === "running" || st === "paused" || st === "loading_model";
  const risk = a.state?.overall;
  const top = a.state?.tracks.slice().sort((x, y) => y.risk_score - x.risk_score)[0];
  return (
    <section className="rounded-lg border border-line bg-panel p-4">
      <div className="mb-3 flex gap-1">
        {VIEWS.map((v) => (
          <button key={v.id} onClick={() => setView(v.id)}
            className={`rounded-md px-3 py-1 text-sm ${view === v.id ? "bg-accent text-white" : "border border-line text-slate-300 hover:border-accent"}`}>{v.label}</button>
        ))}
      </div>
      {risk && active && risk.level !== "low" && top && (
        <div role="alert" className={`mb-3 rounded-md border px-3 py-2 text-sm ${levelBg[risk.level]}`}>
          <strong className={levelText[risk.level]}>{risk.level === "high" ? "Collision warning" : "Caution"}</strong>
          {" "}· {top.label} #{top.id}: {top.reasons.join(", ") || "elevated risk score"}
        </div>
      )}
      <div className="relative flex aspect-video items-center justify-center overflow-hidden rounded-md bg-black">
        {st !== "idle" && <img key={a.streamKey} src={`/api/stream?k=${a.streamKey}`} alt="Processed video" className="h-full w-full object-contain" />}
        {st === "idle" && <p className="text-sm text-slate-400">Start the camera or upload a video to begin.</p>}
        {st === "loading_model" && <p className="absolute flex items-center gap-2 text-sm"><Loader2 className="animate-spin" size={16} />Loading models (first run downloads weights)…</p>}
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button className={btn} disabled={a.busy || active} onClick={a.startCamera}><Camera size={16} />Start camera</button>
        <button className={btn} disabled={a.busy || active} onClick={() => file.current?.click()}><Upload size={16} />Upload video</button>
        <input ref={file} type="file" accept="video/*" hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) a.uploadAndStart(f); e.target.value = ""; }} />
        <button className={btn} disabled={a.busy || st !== "running"} onClick={a.pause}><Pause size={16} />Pause</button>
        <button className={btn} disabled={a.busy || st !== "paused"} onClick={a.resume}><Play size={16} />Resume</button>
        <button className={btn} disabled={a.busy || !active} onClick={a.stop}><Square size={16} />Stop</button>
        <button className={btn} disabled={a.busy || st === "loading_model"} onClick={a.restart}><RotateCcw size={16} />Restart analysis</button>
      </div>
      {(a.error || a.state?.error) && <p className="mt-3 rounded-md border border-risk-high/50 bg-risk-high/10 p-3 text-sm">{a.error ?? a.state?.error}</p>}
    </section>
  );
}
