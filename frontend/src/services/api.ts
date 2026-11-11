import type { Alert, AnalysisState, DetectionEvent, RuntimeSettings, SessionRow, SystemStatus } from "../types";

async function call<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const d = body?.detail;
    throw new Error(typeof d === "string" ? d : Array.isArray(d) ? d.map((x: { msg: string }) => x.msg).join("; ") : `Request failed (${res.status})`);
  }
  return res.json();
}
const send = <T,>(method: string, url: string, body?: unknown) =>
  call<T>(url, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });

export const getStatus = () => call<SystemStatus>("/api/status");
export const startAnalysis = (source: "webcam" | "video", filename?: string) => send<AnalysisState>("POST", "/api/analysis/start", { source, filename });
export const stopAnalysis = () => send<AnalysisState>("POST", "/api/analysis/stop");
export const pauseAnalysis = () => send<AnalysisState>("POST", "/api/analysis/pause");
export const resumeAnalysis = () => send<AnalysisState>("POST", "/api/analysis/resume");
export const uploadVideo = (file: File) => {
  const fd = new FormData(); fd.append("file", file);
  return call<{ filename: string }>("/api/videos", { method: "POST", body: fd });
};
export const getSettings = () => call<RuntimeSettings>("/api/settings");
export const putSettings = (s: RuntimeSettings) => send<RuntimeSettings>("PUT", "/api/settings", s);
export const ackAlert = (id: number) => send<{ id: number }>("PATCH", `/api/alerts/${id}/ack`);
export const getSessions = () => call<SessionRow[]>("/api/sessions");
export const getSessionAlerts = (id: number) => call<Alert[]>(`/api/alerts?session_id=${id}`);
export const getSessionDetections = (id: number, limit = 50) => call<DetectionEvent[]>(`/api/detections?session_id=${id}&limit=${limit}`);
export const reportUrl = (id: number) => `/api/sessions/${id}/report.pdf`;
