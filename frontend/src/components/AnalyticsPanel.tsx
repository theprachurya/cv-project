import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Summary } from "../types";
import { levelHex } from "../utils/risk";

const ax = { stroke: "#64748b", fontSize: 12 };
const tip = { contentStyle: { background: "#111826", border: "1px solid #1f2a3d", borderRadius: 6 } };

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="rounded-md border border-line p-3"><h3 className="mb-2 text-sm text-slate-300">{title}</h3><div className="h-44">{children}</div></div>;
}

export default function AnalyticsPanel({ s }: { s: Summary }) {
  const risk = (["low", "medium", "high"] as const).map((k) => ({ name: k, value: s.risk_distribution?.[k] ?? 0 }));
  const classes = Object.entries(s.by_label ?? {}).map(([name, value]) => ({ name, value }));
  const timeline = s.timeline ?? [];
  const motion = Object.entries(s.motion_distribution ?? {});
  return (
    <section className="rounded-lg border border-line bg-panel p-4">
      <h2 className="mb-3 font-semibold">Analytics</h2>
      <div className="grid gap-3 md:grid-cols-3">
        <Card title="Risk distribution (% of frames)">
          <ResponsiveContainer><BarChart data={risk}><CartesianGrid stroke="#1f2a3d" vertical={false} /><XAxis dataKey="name" {...ax} /><YAxis {...ax} /><Tooltip {...tip} />
            <Bar dataKey="value" radius={[3, 3, 0, 0]}>{risk.map((r) => <Cell key={r.name} fill={levelHex[r.name]} />)}</Bar></BarChart></ResponsiveContainer>
        </Card>
        <Card title="Unique objects by class">
          {classes.length ? <ResponsiveContainer><BarChart data={classes}><CartesianGrid stroke="#1f2a3d" vertical={false} /><XAxis dataKey="name" {...ax} /><YAxis allowDecimals={false} {...ax} /><Tooltip {...tip} />
            <Bar dataKey="value" fill="#3b82f6" radius={[3, 3, 0, 0]} /></BarChart></ResponsiveContainer> : <p className="text-sm text-slate-400">No data yet.</p>}
        </Card>
        <Card title="Risk score over time">
          {timeline.length ? <ResponsiveContainer><LineChart data={timeline}><CartesianGrid stroke="#1f2a3d" /><XAxis dataKey="t" unit="s" {...ax} /><YAxis domain={[0, 100]} {...ax} /><Tooltip {...tip} />
            <Line type="monotone" dataKey="score" stroke="#3b82f6" dot={false} strokeWidth={2} /></LineChart></ResponsiveContainer> : <p className="text-sm text-slate-400">No data yet.</p>}
        </Card>
      </div>
      <dl className="mt-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2 lg:grid-cols-4">
        {([["Average detection confidence", `${Math.round((s.avg_confidence ?? 0) * 100)}%`], ["Alerts generated", s.total_alerts ?? 0],
          ["High-risk events", s.high_risk_events ?? 0], ["Left / right alerts", `${s.left_alerts ?? 0} / ${s.right_alerts ?? 0}`],
          ...motion.map(([k, v]) => [`Motion: ${k}`, `${v} object-frames`])] as [string, string | number][]).map(([k, v]) => (
          <div key={k} className="flex justify-between gap-3"><dt className="text-slate-400">{k}</dt><dd className="tabular-nums">{v}</dd></div>))}
      </dl>
    </section>
  );
}
