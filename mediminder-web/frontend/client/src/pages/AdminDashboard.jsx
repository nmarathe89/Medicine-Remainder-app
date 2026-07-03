import React, { useEffect, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart,
  Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { api } from '../lib/api.js';

const COLORS = ['#3eb16f', '#b13e3e', '#3e9cb1', '#c98e00'];

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState('');
  useEffect(() => { api('/api/admin/dashboard').then(setData).catch(e => setErr(e.message)); }, []);
  if (err) return <div className="card error">{err}</div>;
  if (!data) return <div className="card">Loading…</div>;

  const userPie = [
    { name: 'Active', value: data.users.active },
    { name: 'Inactive', value: data.users.inactive },
  ];
  const feedbackBar = [
    { name: 'Positive', value: data.feedback_last_year.positive },
    { name: 'Negative', value: data.feedback_last_year.negative },
  ];

  return (
    <div>
      <h2>Admin dashboard</h2>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))' }}>
        <div className="tile"><div className="metric">{data.users.total}</div><div className="metric-label">Total users</div></div>
        <div className="tile"><div className="metric">{data.alerts.sent_total}</div><div className="metric-label">Alerts sent so far</div></div>
        <div className="tile"><div className="metric">{data.alerts.upcoming_48h}</div><div className="metric-label">Upcoming (48h)</div></div>
      </div>

      <div className="card">
        <h3>Users: active vs inactive</h3>
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie data={userPie} dataKey="value" nameKey="name" outerRadius={90} label>
              {userPie.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Legend /><Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3>Feedback in the last year</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={feedbackBar}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip />
            <Bar dataKey="value">
              {feedbackBar.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3>User signups — last 3 years</h3>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data.user_trend_3y}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" /><YAxis allowDecimals={false} /><Tooltip />
            <Line type="monotone" dataKey="count" stroke="#3eb16f" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ fontSize: 12, color: '#6b7280' }}>Generated at {data.generated_at}</div>
    </div>
  );
}
