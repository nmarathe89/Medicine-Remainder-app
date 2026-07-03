import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The SSR Express server serves the built assets from `dist/` in production
// and proxies API requests. In `vite dev` mode we mirror that with the
// server.proxy config below so `fetch('/api/...')` just works.
export default defineConfig({
  plugins: [react()],
  root: 'client',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
});
