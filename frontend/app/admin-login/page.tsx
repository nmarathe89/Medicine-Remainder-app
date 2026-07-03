"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { saveAuth } from "@/lib/auth";

export default function AdminLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await api.adminLogin(username, password);
      saveAuth(res.access_token, res.role, res.username);
      router.push("/admin");
    } catch (err: any) {
      setError(err.detail || "Admin login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="center">
      <form className="card auth-box" onSubmit={submit}>
        <h2 style={{ color: "var(--teal)" }}>Admin Login</h2>
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <div className="error">{error}</div>}
        <button className="btn teal" style={{ width: "100%", marginTop: 16 }} disabled={busy}>
          {busy ? "Signing in..." : "Admin Login"}
        </button>
        <p style={{ color: "#9ca3af", fontSize: 13, marginTop: 12 }}>
          Seeded demo admin: <b>admin / admin123</b>
        </p>
      </form>
    </div>
  );
}
