import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "../services/api";
import type { AnalysisState } from "../types";

/** Live state arrives over a WebSocket (/ws/state); control actions are REST calls. */
export function useAnalysis() {
  const [state, setState] = useState<AnalysisState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [streamKey, setStreamKey] = useState(0);
  const last = useRef<{ source: "webcam" | "video"; filename?: string } | null>(null);

  useEffect(() => {
    let ws: WebSocket | null = null, timer: number, closed = false;
    const connect = () => {
      ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/state`);
      ws.onmessage = (e) => setState(JSON.parse(e.data));
      ws.onclose = () => { if (!closed) timer = window.setTimeout(connect, 1500); };
    };
    connect();
    return () => { closed = true; clearTimeout(timer); ws?.close(); };
  }, []);

  const run = useCallback(async (fn: () => Promise<unknown>, restartStream = false) => {
    setBusy(true); setError(null);
    try { await fn(); if (restartStream) setStreamKey((k) => k + 1); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }, []);

  return {
    state, error, busy, streamKey,
    startCamera: () => run(() => { last.current = { source: "webcam" }; return api.startAnalysis("webcam"); }, true),
    uploadAndStart: (file: File) => run(async () => {
      const { filename } = await api.uploadVideo(file);
      last.current = { source: "video", filename };
      await api.startAnalysis("video", filename);
    }, true),
    restart: () => last.current
      ? run(() => api.startAnalysis(last.current!.source, last.current!.filename), true)
      : setError("Nothing to restart yet. Start the camera or upload a video."),
    stop: () => run(api.stopAnalysis), pause: () => run(api.pauseAnalysis), resume: () => run(api.resumeAnalysis),
  };
}
