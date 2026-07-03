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

// Proxy backend calls. WebSocket upgrade for /ws is supported by the same
// middleware when ws:true is set.
app.use(
  '/api',
  createProxyMiddleware({
    target: BACKEND_URL,
    changeOrigin: true,
  })
);
app.use(
  '/ws',
  createProxyMiddleware({
    target: BACKEND_URL,
    changeOrigin: true,
    ws: true,
  })
);

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

// The proxy middleware handles the WebSocket upgrade if we forward it here.
server.on('upgrade', (req, socket, head) => {
  if (req.url?.startsWith('/ws')) {
    // Delegated to http-proxy-middleware.
  }
});
