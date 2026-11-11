import { useState } from "react";
import Header from "./components/Header";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import { useStatus } from "./hooks/useStatus";
import { useAnalysis } from "./hooks/useAnalysis";

export default function App() {
  const { status, error } = useStatus();
  const analysis = useAnalysis();
  const [tab, setTab] = useState<"dashboard" | "history">("dashboard");
  return (
    <div className="min-h-screen">
      <Header status={status} />
      <nav className="flex gap-1 border-b border-line px-6 pt-3">
        {(["dashboard", "history"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`rounded-t-md px-4 py-2 text-sm capitalize ${tab === t ? "bg-panel text-white" : "text-slate-400 hover:text-white"}`}>{t}</button>
        ))}
      </nav>
      <main className="mx-auto max-w-7xl space-y-4 p-6">
        {error && <p className="rounded-md border border-risk-high/50 bg-risk-high/10 p-4 text-sm">Cannot reach the backend. Start it with <code>uvicorn app.main:app --reload</code> in <code>backend/</code>.</p>}
        {tab === "dashboard" ? <Dashboard a={analysis} /> : <History />}
        <p className="pt-2 text-xs text-slate-500">Driver-assistance simulation for education. Not a certified safety system.</p>
      </main>
    </div>
  );
}
