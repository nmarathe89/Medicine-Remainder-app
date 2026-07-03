import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api.js';

const TYPES = ['Bottle', 'Pill', 'Syringe', 'Tablet'];
const INTERVALS = [6, 8, 12, 24];

export default function NewMedicine() {
  const nav = useNavigate();
  const [form, setForm] = useState({
    name: '', dosage_mg: 0, medicine_type: 'Pill', interval_hours: 8, start_time: '0800',
  });
  const [err, setErr] = useState('');
  const submit = async (e) => {
    e.preventDefault();
    setErr('');
    try {
      await api('/api/medicines', {
        method: 'POST',
        body: { ...form, dosage_mg: Number(form.dosage_mg), interval_hours: Number(form.interval_hours) },
      });
      nav('/');
    } catch (e) { setErr(e.message); }
  };
  return (
    <div className="card" style={{ maxWidth: 520 }}>
      <h2>Add Mediminder</h2>
      <form onSubmit={submit}>
        <div className="form-group"><label>Medicine name *</label>
          <input maxLength={64} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /></div>
        <div className="form-group"><label>Dosage (mg)</label>
          <input type="number" min={0} max={10000} value={form.dosage_mg} onChange={e => setForm({ ...form, dosage_mg: e.target.value })} /></div>
        <div className="form-group"><label>Type</label>
          <select value={form.medicine_type} onChange={e => setForm({ ...form, medicine_type: e.target.value })}>
            {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select></div>
        <div className="form-group"><label>Remind me every N hours *</label>
          <select value={form.interval_hours} onChange={e => setForm({ ...form, interval_hours: e.target.value })}>
            {INTERVALS.map(i => <option key={i} value={i}>{i}</option>)}
          </select></div>
        <div className="form-group"><label>Start time (HH:MM)</label>
          <input pattern="^\d{2}:?\d{2}$" value={fmt(form.start_time)}
            onChange={e => setForm({ ...form, start_time: e.target.value.replace(':','') })} required /></div>
        {err && <div className="error">{err}</div>}
        <button className="btn" type="submit">Confirm</button>
      </form>
    </div>
  );
}

function fmt(s) { return s.length === 4 ? `${s.slice(0,2)}:${s.slice(2)}` : s; }
