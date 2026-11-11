import type { Level } from "../types";

export const levelText: Record<string, string> = { low: "text-risk-low", medium: "text-risk-med", high: "text-risk-high", clear: "text-slate-400" };
export const levelBg: Record<string, string> = { low: "bg-risk-low/15 border-risk-low/40", medium: "bg-risk-med/15 border-risk-med/40", high: "bg-risk-high/15 border-risk-high/40", clear: "bg-white/5 border-line" };
export const levelHex: Record<Level, string> = { low: "#22c55e", medium: "#eab308", high: "#ef4444" };
export const fmtTime = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
