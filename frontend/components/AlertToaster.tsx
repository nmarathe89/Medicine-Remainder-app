"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";

// Polls the backend for due alerts and shows them as in-browser toasts.
// This is the "notification" mechanism (no email/SMS): the browser itself
// surfaces reminders. Poll interval kept short for demo responsiveness.
const POLL_MS = 15000;

interface DueAlert {
  id: number;
  medicine_name: string;
  scheduled_at: string;
}

export default function AlertToaster({ onChange }: { onChange?: () => void }) {
  const [alerts, setAlerts] = useState<DueAlert[]>([]);

  async function poll() {
    const token = getToken();
    if (!token) return;
    try {
      const due = await api.dueAlerts(token);
      setAlerts(due);
      // A new alert may have just fired -> let the dashboard refresh its lists.
      onChange?.();
    } catch {
      /* ignore transient errors */
    }
  }

  useEffect(() => {
    poll();
    const t = setInterval(poll, POLL_MS);
    return () => clearInterval(t);
  }, []);

  async function ack(id: number, action: "taken" | "skipped") {
    const token = getToken();
    if (!token) return;
    await api.ackAlert(token, id, action);
    setAlerts((prev) => prev.filter((a) => a.id !== id));
    onChange?.();
  }

  if (alerts.length === 0) return null;

  return (
    <div className="toaster">
      {alerts.map((a) => (
        <div className="toast" key={a.id}>
          <div className="title">💊 Time for {a.medicine_name}</div>
          <div style={{ fontSize: 13, color: "#6b7280" }}>
            Scheduled {new Date(a.scheduled_at).toLocaleTimeString()}
          </div>
          <div className="toast-actions">
            <button className="btn" onClick={() => ack(a.id, "taken")}>
              Taken
            </button>
            <button className="btn ghost" onClick={() => ack(a.id, "skipped")}>
              Skip
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
