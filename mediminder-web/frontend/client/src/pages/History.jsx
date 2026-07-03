import React, { useEffect, useState } from 'react';
import { api } from '../lib/api.js';

export default function History() {
  const [alerts, setAlerts] = useState([]);
  const [err, setErr] = useState('');
  const load = async () => {
    try { setAlerts(await api('/api/alerts?limit=100')); } catch (e) { setErr(e.message); }
  };
  useEffect(() => { load(); }, []);
  const ack = async (id, status) => {
    await api(`/api/alerts/${id}/ack`, { method: 'POST', body: { status } });
    load();
  };
  return (
    <div className="card">
      <h2>Alert history</h2>
      {err && <div className="error">{err}</div>}
      <table>
        <thead><tr><th>When</th><th>Medicine</th><th>Status</th><th></th></tr></thead>
        <tbody>
          {alerts.map(a => (
            <tr key={a.id} style={a.medicine_deleted ? { color: '#9ca3af' } : undefined}>
              <td>{new Date(a.scheduled_at).toLocaleString()}</td>
              <td>
                {a.medicine_name}
                {a.medicine_deleted && (
                  <span style={{ marginLeft: 6, fontSize: 11, background: '#eee', padding: '2px 6px', borderRadius: 4 }}>
                    deleted
                  </span>
                )}
              </td>
              <td>{a.status}</td>
              <td>
                {a.status === 'sent' && !a.medicine_deleted && (
                  <>
                    <button className="btn" style={{ padding: '4px 10px' }} onClick={() => ack(a.id, 'acknowledged')}>Took it</button>
                    {' '}
                    <button className="btn secondary" style={{ padding: '4px 10px' }} onClick={() => ack(a.id, 'skipped')}>Skip</button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
