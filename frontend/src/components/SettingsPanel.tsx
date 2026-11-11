import { useEffect, useState } from "react";
import { getSettings, putSettings } from "../services/api";
import type { Level, RuntimeSettings } from "../types";

type Sound = { enabled: boolean; setEnabled: (v: boolean) => void; minSeverity: Level; setMinSeverity: (l: Level) => void };
const field = "w-24 rounded border border-line bg-bg px-2 py-1 text-sm";

export default function SettingsPanel({ value, onChange, sound }: { value: RuntimeSettings | null; onChange: (s: RuntimeSettings) => void; sound: Sound }) {
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { getSettings().then(onChange).catch((e) => setErr(e.message)); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  if (!value) return <section className="rounded-lg border border-line bg-panel p-4 text-sm text-slate-400">{err ?? "Loading settings…"}</section>;
  const set = async (patch: Partial<RuntimeSettings>) => {
    const next = { ...value, ...patch };
    onChange(next);
    try { setErr(null); onChange(await putSettings(next)); } catch (e) { setErr((e as Error).message); }
  };
  const num = (k: keyof RuntimeSettings, label: string, step = 1) => (
    <label className="flex items-center justify-between gap-3 text-sm"><span className="text-slate-300">{label}</span>
      <input type="number" step={step} className={field} value={value[k] as number} onChange={(e) => e.target.value !== "" && set({ [k]: Number(e.target.value) } as Partial<RuntimeSettings>)} /></label>
  );
  return (
    <section className="space-y-2 rounded-lg border border-line bg-panel p-4">
      <h2 className="font-semibold">Alert and detection settings</h2>
      {num("conf_threshold", "Detection confidence (0.05–0.95)", 0.05)}
      {num("medium_risk", "Medium risk from score")}
      {num("high_risk", "High risk from score")}
      {num("cooldown_s", "Alert cooldown per object (s)")}
      {num("side_frac", "Side zone width (fraction of frame)", 0.05)}
      {num("close_proximity", "Close-obstacle nearness (0–1)", 0.05)}
      <label className="flex items-center justify-between text-sm"><span className="text-slate-300">Use MiDaS depth model</span>
        <input type="checkbox" checked={value.use_depth} onChange={(e) => set({ use_depth: e.target.checked })} /></label>
      <label className="flex items-center justify-between text-sm"><span className="text-slate-300">Sound alerts</span>
        <input type="checkbox" checked={sound.enabled} onChange={(e) => sound.setEnabled(e.target.checked)} /></label>
      <label className="flex items-center justify-between text-sm"><span className="text-slate-300">Sound from severity</span>
        <select className={field} value={sound.minSeverity} onChange={(e) => sound.setMinSeverity(e.target.value as Level)}><option value="low">low</option><option value="medium">medium</option><option value="high">high</option></select></label>
      {err && <p className="text-sm text-risk-high">{err}</p>}
    </section>
  );
}
