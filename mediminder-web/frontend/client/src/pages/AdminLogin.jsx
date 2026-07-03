import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, saveAuth } from '../lib/api.js';

export default function AdminLogin({ onAuth }) {
  const [form, setForm] = useState({ username: 'admin', password: '' });
  const [err, setErr] = useState('');
  const nav = useNavigate();
  const submit = async (e) => {
    e.preventDefault();
    setErr('');
    try {
      const data = await api('/api/auth/admin/login', { method: 'POST', body: form, auth: false });
      saveAuth(data);
      onAuth?.();
      nav('/admin');
    } catch (e) { setErr(e.message); }
  };
  return (
    <div className="card" style={{ maxWidth: 420, margin: '40px auto' }}>
      <h2>Admin sign-in</h2>
      <form onSubmit={submit}>
        <div className="form-group"><label>Username</label>
          <input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required /></div>
        <div className="form-group"><label>Password</label>
          <input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required /></div>
        {err && <div className="error">{err}</div>}
        <button className="btn" type="submit">Sign in</button>
      </form>
    </div>
  );
}
