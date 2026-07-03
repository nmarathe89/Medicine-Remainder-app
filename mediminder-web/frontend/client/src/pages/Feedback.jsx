import React, { useEffect, useState } from 'react';
import { api } from '../lib/api.js';

export default function Feedback() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ sentiment: 'positive', message: '' });
  const [err, setErr] = useState('');
  const load = async () => { try { setItems(await api('/api/feedback/mine')); } catch (e) { setErr(e.message); } };
  useEffect(() => { load(); }, []);
  const submit = async (e) => {
    e.preventDefault();
    setErr('');
    try {
      await api('/api/feedback', { method: 'POST', body: form });
      setForm({ sentiment: 'positive', message: '' });
      load();
    } catch (e) { setErr(e.message); }
  };
  return (
    <div>
      <div className="card">
        <h2>Send feedback</h2>
        <form onSubmit={submit}>
          <div className="form-group"><label>Sentiment</label>
            <select value={form.sentiment} onChange={e => setForm({ ...form, sentiment: e.target.value })}>
              <option value="positive">Positive</option>
              <option value="negative">Negative</option>
            </select></div>
          <div className="form-group"><label>Message</label>
            <textarea rows={3} value={form.message} onChange={e => setForm({ ...form, message: e.target.value })} required /></div>
          {err && <div className="error">{err}</div>}
          <button className="btn" type="submit">Submit</button>
        </form>
      </div>
      <div className="card">
        <h3>My feedback</h3>
        <ul>{items.map(i => <li key={i.id}><strong>{i.sentiment}</strong> — {i.message}</li>)}</ul>
      </div>
    </div>
  );
}
