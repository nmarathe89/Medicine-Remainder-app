import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, saveAuth } from '../lib/api.js';

export default function Register({ onAuth }) {
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [err, setErr] = useState('');
  const nav = useNavigate();
  const submit = async (e) => {
    e.preventDefault();
    setErr('');
    try {
      const data = await api('/api/auth/register', { method: 'POST', body: form, auth: false });
      saveAuth(data);
      onAuth?.();
      nav('/');
    } catch (e) { setErr(e.message); }
  };
  return (
    <div className="card" style={{ maxWidth: 420, margin: '40px auto' }}>
      <h2>Create account</h2>
      <form onSubmit={submit}>
        <div className="form-group"><label>Username</label>
          <input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} minLength={3} required /></div>
        <div className="form-group"><label>Email</label>
          <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required /></div>
        <div className="form-group"><label>Password (min 6 chars)</label>
          <input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} minLength={6} required /></div>
        {err && <div className="error">{err}</div>}
        <button className="btn" type="submit">Register</button>
      </form>
      <p style={{ marginTop: 16, fontSize: 14 }}>Already have one? <Link to="/login">Log in</Link></p>
    </div>
  );
}
