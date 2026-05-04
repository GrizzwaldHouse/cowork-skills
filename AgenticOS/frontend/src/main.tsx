// main.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: React entry point. Imports global styles in order
//          (tokens -> reset -> typography) so that custom properties
//          exist before consumers reference them. Mounts <App /> into
//          the #root div declared in index.html. StrictMode is on so
//          double-effects surface during development.

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

// Style imports must come before App so CSS variables resolve. Order:
// 1) tokens (custom properties), 2) reset (element defaults),
// 3) typography (body fonts), then components own their CSS.
import '@/styles/tokens.css';
import '@/styles/reset.css';
import '@/styles/typography.css';

import App from '@/App';

// Locate the mount point. Throwing early is preferred over rendering
// into a null root because the latter silently does nothing.
const rootElement = document.getElementById('root');
if (rootElement === null) {
  throw new Error('Root element #root not found in index.html');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
