export type Level = "low" | "medium" | "high";
export type Motion = "approaching" | "receding" | "lateral" | "stationary";

export interface SystemStatus { backend: string; processing: string; model: string; conf_threshold: number; source: string | null; time: string; }

export interface TrackInfo {
  id: number; label: string; confidence: number; dx: number; dy: number; magnitude: number; speed: number;
  motion: Motion; growth: number; proximity: number; depth_label: "near" | "medium" | "far";
  ttc: number | null; risk_score: number; risk_level: Level; reasons: string[]; age: number;
}
export interface Alert {
  id: number; type: string; severity: Level; track_id: number | null; frame: number; video_time: number;
  x: number; y: number; reason: string; acknowledged: boolean; timestamp: string;
}
export interface DetectionEvent {
  id: number; session_id: number; frame: number; video_time: number; track_id: number; label: string;
  confidence: number; box: [number, number, number, number]; motion: Motion; speed: number; proximity: number;
  risk_score: number; risk_level: Level; ttc: number | null; reasons: string[];
}
export interface Side { level: "clear" | Level; ids: number[]; }
export interface Summary {
  duration_s?: number; video_seconds?: number; frames_analyzed?: number; unique_objects?: number;
  by_label?: Record<string, number>; vehicles?: number; pedestrians?: number; avg_confidence?: number;
  total_alerts?: number; alerts_by_type?: Record<string, number>; left_alerts?: number; right_alerts?: number;
  high_risk_events?: number; risk_distribution?: Record<string, number>; motion_distribution?: Record<string, number>;
  timeline?: { t: number; score: number }[];
}
export interface AnalysisState {
  status: "idle" | "loading_model" | "running" | "paused" | "ended" | "stopped" | "error";
  source: "webcam" | "video" | null; filename: string | null; session_id: number | null;
  frame: number; frame_id: number; fps: number; counts: Record<string, number>; unique_objects: number;
  objects_in_frame: number; tracks: TrackInfo[]; overall: { score: number; level: Level };
  blind_spots: { left: Side; right: Side }; alerts: Alert[]; alert_count: number; summary: Summary;
  depth_backend: string; error: string | null;
}
export interface RuntimeSettings {
  conf_threshold: number; medium_risk: number; high_risk: number; cooldown_s: number; side_frac: number;
  close_proximity: number; use_depth: boolean; depth_every: number; view: "detection" | "flow" | "depth";
}
export interface SessionRow {
  id: number; source: string; filename: string | null; status: string; started_at: string; ended_at: string | null;
  frames_processed: number; total_alerts: number; high_risk_events: number; unique_objects: number;
}
