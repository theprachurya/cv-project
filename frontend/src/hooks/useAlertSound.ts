import { useEffect, useRef, useState } from "react";
import type { Alert, Level } from "../types";

const RANK: Record<Level, number> = { low: 0, medium: 1, high: 2 };

/** Plays a short beep (Web Audio, no files) for alerts at or above the chosen severity. */
export function useAlertSound(alerts: Alert[]) {
  const [enabled, setEnabled] = useState(false);
  const [minSeverity, setMinSeverity] = useState<Level>("medium");
  const seen = useRef(0);
  const ctx = useRef<AudioContext | null>(null);

  useEffect(() => {
    const newest = alerts.reduce((m, a) => Math.max(m, a.id), 0);
    if (seen.current === 0 && newest) seen.current = newest - alerts.filter((a) => a.id > 0).length;
    const fresh = alerts.filter((a) => a.id > seen.current && RANK[a.severity] >= RANK[minSeverity]);
    if (newest > seen.current) seen.current = newest;
    if (!enabled || fresh.length === 0) return;
    ctx.current ??= new AudioContext();
    const c = ctx.current, o = c.createOscillator(), g = c.createGain();
    const high = fresh.some((a) => a.severity === "high");
    o.frequency.value = high ? 880 : 520; o.connect(g); g.connect(c.destination);
    g.gain.setValueAtTime(0.15, c.currentTime); g.gain.exponentialRampToValueAtTime(0.001, c.currentTime + (high ? 0.5 : 0.25));
    o.start(); o.stop(c.currentTime + 0.5);
  }, [alerts, enabled, minSeverity]);

  return { enabled, setEnabled, minSeverity, setMinSeverity };
}
