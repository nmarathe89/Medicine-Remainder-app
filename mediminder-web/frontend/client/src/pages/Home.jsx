import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api.js';

export default function Home() {
  const [meds, setMeds] = useState([]);
  const [err, setErr] = useState('');
  const load = async () => {
    try { setMeds(await api('/api/medicines')); } catch (e) { setErr(e.message); }
  };
  useEffect(() => { load(); }, []);
  const remove = async (id) => {
    if (!window.confirm('Delete this medicine?')) return;
    await api(`/api/medicines/${id}`, { method: 'DELETE' });
    load();
  };
  return (
    <div>
      <div className="card">
        <h2>My Mediminders</h2>
        <p>You have <strong>{meds.length}</strong> active reminder{meds.length === 1 ? '' : 's'}.</p>
        <Link to="/new" className="btn">+ Add reminder</Link>
      </div>
      {err && <div className="card error">{err}</div>}
      <div className="grid">
        {meds.map(m => (
          <div key={m.id} className="tile" style={{ textAlign: 'left' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#3eb16f' }}>{m.name}</div>
            <div style={{ fontSize: 13, color: '#6b7280', margin: '4px 0' }}>
              {m.medicine_type} · {m.dosage_mg} mg
            </div>
            <div style={{ fontSize: 13 }}>Every {m.interval_hours}h · starts {m.start_time.slice(0,2)}:{m.start_time.slice(2)}</div>
            <button className="btn danger" style={{ marginTop: 10 }} onClick={() => remove(m.id)}>Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}
