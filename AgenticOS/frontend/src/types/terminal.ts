// terminal.ts
// Developer: Marcus Daley
// Date: 2026-05-01
// Purpose: TypeScript mirrors for the AgenticOS terminal-control REST
//          payloads. The Python models in AgenticOS.models are canonical;
//          this file exists so the React operator panel stays typed.

export interface TerminalWindow {
  readonly hwnd: number;
  readonly pid: number;
  readonly title: string;
  readonly process_name: string;
  readonly executable: string | null;
  readonly cwd: string | null;
  readonly command_line: string | null;
  readonly is_visible: boolean;
  readonly is_agent_like: boolean;
  readonly detected_at: string;
}

export interface TerminalActionResult {
  readonly ok: boolean;
  readonly hwnd: number | null;
  readonly pid: number | null;
  readonly message: string;
}
