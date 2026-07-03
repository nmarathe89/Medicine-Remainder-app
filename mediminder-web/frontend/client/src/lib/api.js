// Thin wrapper over fetch that adds the JWT header and unwraps JSON errors.
// The API base URL is injected into `window.__CONFIG__` by the SSR server;
// during `vite dev` it stays empty and the vite proxy handles /api and /ws.

function baseUrl() {
  if (typeof window !== 'undefined' && window.__CONFIG__?.apiBaseUrl) {
    return window.__CONFIG__.apiBaseUrl;
  }
  return '';
}

function token() {
  return typeof window !== 'undefined' ? window.localStorage.getItem('token') : null;
}

export function saveAuth({ access_token, is_admin, username, user_id }) {
  window.localStorage.setItem('token', access_token);
  window.localStorage.setItem('is_admin', is_admin ? '1' : '0');
  window.localStorage.setItem('username', username);
  window.localStorage.setItem('user_id', String(user_id));
}

export function clearAuth() {
  ['token', 'is_admin', 'username', 'user_id'].forEach(k => window.localStorage.removeItem(k));
}

export function currentUser() {
  if (typeof window === 'undefined') return null;
  const tok = window.localStorage.getItem('token');
  if (!tok) return null;
  return {
    token: tok,
    username: window.localStorage.getItem('username') || '',
    isAdmin: window.localStorage.getItem('is_admin') === '1',
    userId: Number(window.localStorage.getItem('user_id') || 0),
  };
}

export async function api(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) {
    const tok = token();
    if (tok) headers['Authorization'] = `Bearer ${tok}`;
  }
  const res = await fetch(baseUrl() + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.detail || `HTTP ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

export function wsUrl(pathWithQuery) {
  const configured = typeof window !== 'undefined' ? window.__CONFIG__?.wsBaseUrl : '';
  if (configured) return configured + pathWithQuery;
  // Default: derive from current location, swapping http(s) for ws(s).
  if (typeof window === 'undefined') return '';
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${pathWithQuery}`;
}
