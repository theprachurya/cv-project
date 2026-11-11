import { useState } from "react";
import VideoPanel from "../components/VideoPanel";
import RiskPanel from "../components/RiskPanel";
import MotionPanel from "../components/MotionPanel";
import AnalyticsPanel from "../components/AnalyticsPanel";
import AlertsPanel from "../components/AlertsPanel";
import SettingsPanel from "../components/SettingsPanel";
import { putSettings } from "../services/api";
import { useAlertSound } from "../hooks/useAlertSound";
import type { useAnalysis } from "../hooks/useAnalysis";
import type { RuntimeSettings } from "../types";

export default function Dashboard({ a }: { a: ReturnType<typeof useAnalysis> }) {
  const [settings, setSettings] = useState<RuntimeSettings | null>(null);
  const alerts = a.state?.alerts ?? [];
  const sound = useAlertSound(alerts);
  const setView = (view: RuntimeSettings["view"]) => { if (settings) { const n = { ...settings, view }; setSettings(n); putSettings(n).catch(() => {}); } };
  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <VideoPanel a={a} view={settings?.view ?? "detection"} setView={setView} />
        <RiskPanel s={a.state} />
      </div>
      <MotionPanel tracks={a.state?.tracks ?? []} />
      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <AlertsPanel alerts={alerts} total={a.state?.alert_count ?? 0} />
        <SettingsPanel value={settings} onChange={setSettings} sound={sound} />
      </div>
      <AnalyticsPanel s={a.state?.summary ?? {}} />
    </div>
  );
}
