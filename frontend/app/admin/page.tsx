"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { api } from "@/lib/api";
import { clearAuth, getToken } from "@/lib/auth";

// Red-themed chart palette (primary red, muted rose, deep red, warm amber).
const COLORS = ["#d32030", "#e88b93", "#a01824", "#f0a202"];

export default function AdminDashboard() {
  const router = useRouter();
  const [users, setUsers] = useState<any>(null);
  const [feedback, setFeedback] = useState<any>(null);
  const [trend, setTrend] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/admin-login");
      return;
    }
    (async () => {
      try {
        const [u, f, t, a] = await Promise.all([
          api.adminUsers(token),
          api.adminFeedback(token),
          api.adminTrend(token),
          api.adminAlerts(token),
        ]);
        setUsers(u);
        setFeedback(f);
        setTrend(t);
        setAlerts(a);
      } catch (err: any) {
        setError(err.detail || "Failed to load stats");
        if (err.status === 401 || err.status === 403) router.push("/admin-login");
      }
    })();
  }, []);

  function logout() {
    const token = getToken();
    if (token) api.logout(token).catch(() => {});
    clearAuth();
    router.push("/");
  }

  const userPie = users
    ? [
        { name: "Active", value: users.active },
        { name: "Inactive", value: users.inactive },
      ]
    : [];
  const feedbackBar = feedback
    ? [
        { name: "Positive", value: feedback.positive },
        { name: "Negative", value: feedback.negative },
      ]
    : [];

  return (
    <>
      <div className="header">
        <h1>Admin Dashboard</h1>
        <button className="btn ghost" onClick={logout} style={{ color: "#fff", borderColor: "#fff" }}>
          Logout
        </button>
      </div>
      <div className="container">
        {error && <div className="error">{error}</div>}

        <div className="stats-row">
          <div className="card stat">
            <div className="num">{users?.total ?? "–"}</div>
            <div>Total Users</div>
          </div>
          <div className="card stat">
            <div className="num">{alerts?.total_sent ?? "–"}</div>
            <div>Alerts Sent</div>
          </div>
          <div className="card stat">
            <div className="num">{alerts?.upcoming_48h ?? "–"}</div>
            <div>Upcoming (48h)</div>
          </div>
        </div>

        <div className="card">
          <h3>Users: Active vs Inactive</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={userPie} dataKey="value" nameKey="name" outerRadius={100} label>
                {userPie.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>Feedback (last 12 months)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={feedbackBar}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value">
                {feedbackBar.map((_, i) => (
                  <Cell key={i} fill={i === 0 ? COLORS[0] : COLORS[1]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>User Trend (last 3 years, monthly signups)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 10 }} interval={2} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#d32030" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}
