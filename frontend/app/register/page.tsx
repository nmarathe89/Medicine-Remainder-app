"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.register(username, password);
      setOk(true);
      setTimeout(() => router.push("/login"), 800);
    } catch (err: any) {
      setError(err.detail || "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="center">
      <form className="card auth-box" onSubmit={submit}>
        <h2 style={{ color: "var(--green)" }}>Register</h2>
        <label>Username (min 3 chars)</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} />
        <label>Password (min 4 chars)</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <div className="error">{error}</div>}
        {ok && <div style={{ color: "var(--green)", marginTop: 8 }}>Registered! Redirecting…</div>}
        <button className="btn" style={{ width: "100%", marginTop: 16 }} disabled={busy}>
          {busy ? "Creating..." : "Create account"}
        </button>
        <div className="link-row">
          Already have an account? <Link href="/login">Login</Link>
        </div>
      </form>
    </div>
  );
}
