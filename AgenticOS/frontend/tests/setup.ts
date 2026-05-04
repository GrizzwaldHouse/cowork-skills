// setup.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Vitest global setup. Imports @testing-library/jest-dom matchers
//          so every test file has toBeInTheDocument(), toBeDisabled(), and
//          siblings without re-importing them per file.

import '@testing-library/jest-dom/vitest';
