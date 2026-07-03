"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { clearAuth, getToken, getUsername } from "@/lib/auth";
import AlertToaster from "@/components/AlertToaster";

const TYPES = ["Pill", "Tablet", "Bottle", "Syringe", "None"];
const INTERVALS = [6, 8, 12, 24];

interface Medicine {
  id: number;
  name: string;
  dosage: number;
  medicine_type: string;
  interval_hours: number;
  start_time: string;
  doses_per_day: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "",
    dosage: "",
    medicine_type: "Pill",
    interval_hours: 8,
    start_time: "08:00",
  });
  const [fb, setFb] = useState({ sentiment: "positive", message: "" });
  const [fbMsg, setFbMsg] = useState("");

  async function load() {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }
    try {
      setMedicines(await api.listMedicines(token));
    } catch {
      router.push("/login");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function addMedicine(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const token = getToken()!;
    const payload = {
      name: form.name,
      dosage: form.dosage ? parseInt(form.dosage, 10) : 0,
      medicine_type: form.medicine_type,
      interval_hours: Number(form.interval_hours),
      start_time: form.start_time.replace(":", ""), // "08:00" -> "0800"
    };
    try {
      await api.createMedicine(token, payload);
      setForm({ ...form, name: "", dosage: "" });
      load();
    } catch (err: any) {
      setError(err.detail || "Could not add medicine");
    }
  }

  async function remove(id: number) {
    const token = getToken()!;
    await api.deleteMedicine(token, id);
    load();
  }

  async function sendFeedback(e: React.FormEvent) {
    e.preventDefault();
    const token = getToken()!;
    await api.submitFeedback(token, fb.sentiment, fb.message);
    setFb({ sentiment: "positive", message: "" });
    setFbMsg("Thanks for your feedback!");
    setTimeout(() => setFbMsg(""), 2500);
  }

  function logout() {
    const token = getToken();
    if (token) api.logout(token).catch(() => {});
    clearAuth();
    router.push("/");
  }

  return (
    <>
      <AlertToaster />
      <div className="header">
        <h1>Mediminder</h1>
        <div>
          <span style={{ marginRight: 12 }}>Hi, {getUsername()}</span>
          <button className="btn ghost" onClick={logout} style={{ color: "#fff", borderColor: "#fff" }}>
            Logout
          </button>
        </div>
      </div>

      <div className="container">
        <div className="card">
          <h3>Add a Mediminder</h3>
          <form onSubmit={addMedicine}>
            <label>Medicine Name *</label>
            <input value={form.name} maxLength={64} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <label>Dosage (mg, optional)</label>
            <input value={form.dosage} type="number" onChange={(e) => setForm({ ...form, dosage: e.target.value })} />
            <label>Type</label>
            <select value={form.medicine_type} onChange={(e) => setForm({ ...form, medicine_type: e.target.value })}>
              {TYPES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
            <label>Remind me every (hours) *</label>
            <select
              value={form.interval_hours}
              onChange={(e) => setForm({ ...form, interval_hours: Number(e.target.value) })}
            >
              {INTERVALS.map((i) => (
                <option key={i} value={i}>
                  {i}
                </option>
              ))}
            </select>
            <label>Start time *</label>
            <input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
            {error && <div className="error">{error}</div>}
            <button className="btn" style={{ marginTop: 16 }}>
              Confirm
            </button>
          </form>
        </div>

        <div className="card">
          <h3>Your Mediminders ({medicines.length})</h3>
          {medicines.length === 0 ? (
            <p style={{ color: "#9ca3af" }}>No medicines yet. Add one above.</p>
          ) : (
            <div className="grid">
              {medicines.map((m) => (
                <div className="card med-card" key={m.id}>
                  <div className="name">{m.name}</div>
                  <div className="sub">{m.medicine_type}</div>
                  <div className="sub">
                    Every {m.interval_hours}h · {m.doses_per_day}/day
                  </div>
                  <div className="sub">{m.dosage ? `${m.dosage} mg` : "Dosage n/a"}</div>
                  <button className="btn danger" style={{ marginTop: 10 }} onClick={() => remove(m.id)}>
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h3>Send Feedback</h3>
          <form onSubmit={sendFeedback}>
            <label>Sentiment</label>
            <select value={fb.sentiment} onChange={(e) => setFb({ ...fb, sentiment: e.target.value })}>
              <option value="positive">Positive</option>
              <option value="negative">Negative</option>
            </select>
            <label>Message</label>
            <input value={fb.message} maxLength={500} onChange={(e) => setFb({ ...fb, message: e.target.value })} />
            <button className="btn teal" style={{ marginTop: 16 }}>
              Submit
            </button>
            {fbMsg && <div style={{ color: "var(--green)", marginTop: 8 }}>{fbMsg}</div>}
          </form>
        </div>
      </div>
    </>
  );
}
