// Express SSR server for the Mediminder React app.
//
// Responsibilities:
//   1. Serve the static Vite bundle from ../dist.
//   2. Inject runtime config (API base URL, WS base URL) into every HTML
//      response via window.__CONFIG__, so the SAME image can point at
//      localhost:8000 or the Cloud Run backend URL without a rebuild.
//   3. Proxy /api and /ws to the backend, keeping the browser same-origin.

import express from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createProxyMiddleware } from 'http-proxy-middleware';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_DIR = path.resolve(__dirname, '..', 'dist');
const PORT = Number(process.env.PORT || 3000);
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
// Runtime config exposed to the client via window.__CONFIG__. Empty strings
// mean "same origin" (i.e. proxied through this Express server). If you want
// the browser to talk directly to a different origin, set these envs.
const PUBLIC_API_BASE = process.env.PUBLIC_API_BASE || '';
const PUBLIC_WS_BASE = process.env.PUBLIC_WS_BASE || '';

const app = express();

// Health check for Cloud Run / docker-compose.
app.get('/healthz', (_req, res) => res.json({ status: 'ok' }));

// Proxy backend calls. `app.use('/api', ...)` strips the mount prefix in
// Express, so we put the prefix back with pathRewrite: prepending it means
// the backend receives the full `/api/...` path it expects. Same treatment
// for the WebSocket path.
app.use(
  '/api',
  createProxyMiddleware({
    target: BACKEND_URL,
    changeOrigin: true,
    pathRewrite: (path) => `/api${path}`,
  })
);
// WebSocket proxy. We keep a reference so we can pass the HTTP upgrade
// event straight to the middleware — Express itself never routes upgrades
// through app.use. On the upgrade path the middleware sees the ORIGINAL
// url (`/ws/alerts?token=...`), not a stripped one, so we do NOT use
// pathRewrite here — that would double-prefix the path to `/ws/ws/alerts`.
const wsProxy = createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  ws: true,
  logger: console,
});
app.use('/ws', wsProxy);

// Serve static assets (JS bundle, CSS, /styles.css from client/public).
if (fs.existsSync(DIST_DIR)) {
  app.use(express.static(DIST_DIR, { index: false, maxAge: '1h' }));
}

// SSR: read the built index.html, inject runtime config, send it back. The
// React app is a single-page app, so any unknown path serves the shell.
const indexHtmlPath = path.join(DIST_DIR, 'index.html');
let indexTemplate = '';
try {
  indexTemplate = fs.readFileSync(indexHtmlPath, 'utf8');
} catch (e) {
  console.warn(`[warn] ${indexHtmlPath} not found; run \`npm run build\` first.`);
  indexTemplate =
    '<!doctype html><html><body><h1>Mediminder SSR</h1>' +
    '<p>Frontend bundle missing. Run <code>npm run build</code>.</p></body></html>';
}

app.get('*', (req, res) => {
  const config = JSON.stringify({
    apiBaseUrl: PUBLIC_API_BASE,
    wsBaseUrl: PUBLIC_WS_BASE,
    renderedAt: new Date().toISOString(),
    path: req.path,
  });
  const html = indexTemplate.replace(
    /window\.__CONFIG__ = window\.__CONFIG__ \|\| \{[^}]*\};?/,
    `window.__CONFIG__ = ${config};`
  );
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.send(html);
});

const server = app.listen(PORT, () => {
  console.log(`Mediminder SSR listening on :${PORT} (backend=${BACKEND_URL})`);
});

// Wire WebSocket upgrades to the proxy. Without this the browser's
// `new WebSocket('/ws/alerts?token=…')` returns 400, because Express never
// routes upgrade events through app.use middleware — the raw HTTP server
// has to hand them off explicitly. The .upgrade method comes from
// http-proxy-middleware ≥ 3.
server.on('upgrade', (req, socket, head) => {
  if (!req.url?.startsWith('/ws')) return;
  if (typeof wsProxy.upgrade === 'function') {
    wsProxy.upgrade(req, socket, head);
  } else {
    // Older API surface — the middleware attaches a `.on('upgrade')` handler
    // to whatever it's mounted on. Call the internal proxy if exposed.
    wsProxy(req, socket, head);
  }
});
