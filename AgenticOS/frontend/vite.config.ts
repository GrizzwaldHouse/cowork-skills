// vite.config.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Vite build and dev-server configuration. Mirrors the FastAPI port
//          constants from AgenticOS/config.py so the proxy targets the same
//          process the backend binds to. Mirrored values are documented as
//          must-stay-in-sync; src/config.ts is the runtime equivalent.

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// Mirror of AgenticOS/config.py WEBSOCKET_PORT / REST_PORT. Kept here because
// vite.config.ts cannot import from the Python module; if the Python constant
// changes, this value MUST be updated in lockstep with src/config.ts.
const FASTAPI_PORT = 7842;
const FASTAPI_HTTP_BASE = `http://127.0.0.1:${FASTAPI_PORT}`;
const FASTAPI_WS_BASE = `ws://127.0.0.1:${FASTAPI_PORT}`;

// Vite dev-server port. Listed in AgenticOS/config.py CORS_ORIGINS so the
// FastAPI server already accepts cross-origin requests from this address.
const VITE_DEV_PORT = 5173;

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      // @ aliases src/. Component trees go several levels deep and relative
      // imports get noisy fast. Tests reach across the alias too.
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: VITE_DEV_PORT,
    strictPort: true,
    proxy: {
      // REST endpoints live directly under root paths /approve, /research,
      // /review on the FastAPI side. We expose them under /api in the dev
      // server so production (same-origin) and dev (cross-origin) share the
      // same client code path.
      '/api': {
        target: FASTAPI_HTTP_BASE,
        changeOrigin: true,
        rewrite: (incoming) => incoming.replace(/^\/api/, ''),
      },
      // WebSocket frame stream from the state bus. ws=true is required so
      // Vite negotiates the upgrade rather than treating /ws as plain HTTP.
      '/ws': {
        target: FASTAPI_WS_BASE,
        ws: true,
        changeOrigin: true,
      },
    },
  },

  build: {
    // FastAPI mounts AgenticOS/frontend/dist at FRONTEND_MOUNT_PATH (/app).
    // emptyOutDir keeps stale chunks from accumulating between builds.
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
    target: 'es2022',
  },

  test: {
    // jsdom gives us window/document for component tests; node would not.
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/main.tsx', 'src/**/*.css'],
    },
  },
});
