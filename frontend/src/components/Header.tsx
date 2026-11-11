import { useEffect, useState } from "react";
import { Car, Camera, Cpu, Server } from "lucide-react";
import type { SystemStatus } from "../types";

function Pill({ icon, label, ok }: { icon: React.ReactNode; label: string; ok: boolean }) {
  return (
    <span className="flex items-center gap-2 rounded-md border border-line px-3 py-1.5 text-sm">
      <span className={ok ? "text-risk-low" : "text-risk-high"}>{icon}</span>{label}
    </span>
  );
}

export default function Header({ status }: { status: SystemStatus | null }) {
  const cam = status?.source === "webcam" && status.processing === "running";
  const [now, setNow] = useState(new Date());
  useEffect(() => { const id = setInterval(() => setNow(new Date()), 1000); return () => clearInterval(id); }, []);
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-panel px-6 py-4">
      <div className="flex items-center gap-3">
        <Car className="text-accent" />
        <h1 className="text-lg font-semibold">Smart Road Safety &amp; Blind Spot Detection</h1>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Pill icon={<Server size={16} />} label={status ? "Backend online" : "Backend offline"} ok={!!status} />
        <Pill icon={<Camera size={16} />} label={cam ? "Camera connected" : "Camera not connected"} ok={cam} />
        <Pill icon={<Cpu size={16} />} label={status ? `Processing ${status.processing.replace("_", " ")}` : "Processing unavailable"} ok={!!status} />
        <span className="text-sm tabular-nums text-slate-400">{now.toLocaleString()}</span>
      </div>
    </header>
  );
}
