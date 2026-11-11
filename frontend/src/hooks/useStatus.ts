import { useEffect, useState } from "react";
import { getStatus } from "../services/api";
import type { SystemStatus } from "../types";

export function useStatus(intervalMs = 3000) {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try { const s = await getStatus(); if (alive) { setStatus(s); setError(null); } }
      catch (e) { if (alive) { setStatus(null); setError((e as Error).message); } }
    };
    poll();
    const id = setInterval(poll, intervalMs);
    return () => { alive = false; clearInterval(id); };
  }, [intervalMs]);
  return { status, error };
}
