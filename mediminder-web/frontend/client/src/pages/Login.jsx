import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, saveAuth } from '../lib/api.js';

export default function Login({ onAuth }) {
  const [form, setForm] = useState({ username: '', password: '' });
  const [err, setErr] = useState('');
  const nav = useNavigate();
  const submit = async (e) => {
    e.preventDefault();
    setErr('');
    try {
      const data = await api('/api/auth/login', { method: 'POST', body: form, auth: false });
      saveAuth(data);
      onAuth?.();
      nav(data.is_admin ? '/admin' : '/');
    } catch (e) { setErr(e.message); }
  };
  return (
    <div className="card" style={{ maxWidth: 420, margin: '40px auto' }}>
      <h2>Log in</h2>
      <form onSubmit={submit}>
        <div className="form-group"><label>Username</label>
          <input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required /></div>
        <div className="form-group"><label>Password</label>
          <input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required /></div>
        {err && <div className="error">{err}</div>}
        <button className="btn" type="submit">Log in</button>
      </form>
      <p style={{ marginTop: 16, fontSize: 14 }}>
        No account? <Link to="/register">Register</Link> · Admin? <Link to="/admin/login">Admin login</Link>
      </p>
    </div>
  );
}
