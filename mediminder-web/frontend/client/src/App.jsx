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
  const [wsConnected, setWsConnected] = useState(false);

  // Live alert toaster.
  //
  // Runs whenever a signed-in non-admin user is present. Reconnects with
  // backoff when the socket drops. Prompts for browser Notification
  // permission on first paint so system-level notifications work.
  useEffect(() => {
    if (!user || user.isAdmin) return;
    let socket;
    let cancelled = false;
    let backoffMs = 1000;
    let heartbeat;

    const connect = () => {
      const url = wsUrl(`/ws/alerts?token=${encodeURIComponent(user.token)}`);
      // eslint-disable-next-line no-console
      console.log('[mediminder] opening WebSocket', url);
      socket = new WebSocket(url);
      socket.onopen = () => {
        setWsConnected(true);
        backoffMs = 1000;
        // Server ignores inbound frames; a periodic empty message keeps
        // some intermediaries (Cloud Run, corporate proxies) from timing
        // the connection out silently.
        heartbeat = setInterval(() => {
          try { socket.send(''); } catch (_) { /* ignore */ }
        }, 25_000);
      };
      socket.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          // eslint-disable-next-line no-console
          console.log('[mediminder] ws message', data);
          if (data.type === 'alert') {
            setToast(`Time to take: ${data.medicine_name}`);
            if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
              new Notification('Mediminder', {
                body: `Time to take: ${data.medicine_name}`,
                tag: `alert-${data.alert_id}`,
              });
            }
          }
        } catch (_) { /* ignore */ }
      };
      socket.onerror = (e) => {
        // eslint-disable-next-line no-console
        console.warn('[mediminder] ws error', e);
      };
      socket.onclose = () => {
        setWsConnected(false);
        clearInterval(heartbeat);
        if (!cancelled) {
          setTimeout(connect, backoffMs);
          backoffMs = Math.min(backoffMs * 2, 15_000);
        }
      };
    };

    connect();

    // Ask permission once, non-blocking. Must be user-gesture-triggered on
    // some browsers — if the auto-prompt is rejected, the toast still shows.
    if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
      Notification.requestPermission().catch(() => {});
    }
    return () => {
      cancelled = true;
      clearInterval(heartbeat);
      socket?.close();
    };
  }, [user?.token, user?.isAdmin]);

  // If the tab was backgrounded and returns, refresh the user snapshot so the
  // effect above re-fires and re-opens the socket if it dropped in the mean time.
  useEffect(() => {
    const onVis = () => setUser(currentUser());
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, []);

  const onAuthChanged = () => setUser(currentUser());
  const showWsBanner = !!user && !user.isAdmin && !wsConnected;

  return (
    <>
      <NavBar onLogout={onAuthChanged} />
      {showWsBanner && (
        <div style={{
          background: '#dbeafe', color: '#1e40af', padding: '6px 24px',
          fontSize: 13, borderBottom: '1px solid #93c5fd',
        }}>
          Reconnecting to the live-alerts channel…
        </div>
      )}
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
