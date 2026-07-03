import React, { useEffect, useState } from 'react';
import { Link, Navigate, Route, Routes, useNavigate } from 'react-router-dom';

import { clearAuth, currentUser, wsUrl } from './lib/api.js';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import AdminLogin from './pages/AdminLogin.jsx';
import Home from './pages/Home.jsx';
import NewMedicine from './pages/NewMedicine.jsx';
import History from './pages/History.jsx';
import Feedback from './pages/Feedback.jsx';
import AdminDashboard from './pages/AdminDashboard.jsx';

function RequireAuth({ children, adminOnly = false }) {
  const user = currentUser();
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && !user.isAdmin) return <Navigate to="/" replace />;
  return children;
}

function Toast({ message, onClose }) {
  useEffect(() => {
    if (!message) return;
    const id = setTimeout(onClose, 6000);
    return () => clearTimeout(id);
  }, [message, onClose]);
  if (!message) return null;
  return <div className="toast">{message}</div>;
}

function NavBar({ onLogout }) {
  const user = currentUser();
  const nav = useNavigate();
  if (!user) return null;
  const logout = () => {
    clearAuth();
    onLogout?.();
    nav('/login');
  };
  return (
    <div className="nav">
      <strong>Mediminder</strong>
      <div>
        {user.isAdmin ? (
          <Link to="/admin">Dashboard</Link>
        ) : (
          <>
            <Link to="/">Home</Link>
            <Link to="/new">Add</Link>
            <Link to="/history">History</Link>
            <Link to="/feedback">Feedback</Link>
          </>
        )}
        <button onClick={logout}>Logout ({user.username})</button>
      </div>
    </div>
  );
}

export default function App() {
  const [toast, setToast] = useState(null);
  const [user, setUser] = useState(() => currentUser());

  // Live alert toaster. Runs whenever a signed-in user is present; reconnects
  // when the user changes.
  useEffect(() => {
    if (!user || user.isAdmin) return;
    let socket;
    let cancelled = false;
    const connect = () => {
      socket = new WebSocket(wsUrl(`/ws/alerts?token=${encodeURIComponent(user.token)}`));
      socket.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if (data.type === 'alert') {
            setToast(`Time to take: ${data.medicine_name}`);
            if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
              new Notification('Mediminder', { body: `Time to take: ${data.medicine_name}` });
            }
          }
        } catch (_) { /* ignore */ }
      };
      socket.onclose = () => {
        if (!cancelled) setTimeout(connect, 3000);
      };
    };
    connect();
    // Ask permission once, non-blocking.
    if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
      Notification.requestPermission().catch(() => {});
    }
    return () => { cancelled = true; socket?.close(); };
  }, [user?.token]);

  const onAuthChanged = () => setUser(currentUser());

  return (
    <>
      <NavBar onLogout={onAuthChanged} />
      <div className="container">
        <Routes>
          <Route path="/login" element={<Login onAuth={onAuthChanged} />} />
          <Route path="/register" element={<Register onAuth={onAuthChanged} />} />
          <Route path="/admin/login" element={<AdminLogin onAuth={onAuthChanged} />} />

          <Route path="/" element={<RequireAuth><Home /></RequireAuth>} />
          <Route path="/new" element={<RequireAuth><NewMedicine /></RequireAuth>} />
          <Route path="/history" element={<RequireAuth><History /></RequireAuth>} />
          <Route path="/feedback" element={<RequireAuth><Feedback /></RequireAuth>} />

          <Route path="/admin" element={<RequireAuth adminOnly><AdminDashboard /></RequireAuth>} />
        </Routes>
      </div>
      <Toast message={toast} onClose={() => setToast(null)} />
    </>
  );
}
