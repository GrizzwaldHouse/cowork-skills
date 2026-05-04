// main.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Electron main process for Agentic OS dashboard.
//   Owns the BrowserWindow lifecycle, IPC handler registration, and
//   platform-specific quit behaviour. The renderer is fully sandboxed —
//   only the contextBridge surface in preload.js is exposed to renderer code.

'use strict';

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('node:path');

// devMode — true when launched with `electron . --dev`
// Used to open DevTools automatically for development sessions.
const devMode = process.argv.includes('--dev');

// win — module-level reference to the main BrowserWindow.
// Kept here so the activate handler can check if a window already exists
// without having to call BrowserWindow.getAllWindows() everywhere.
let win = null;

// createWindow — creates and configures the main dashboard BrowserWindow.
// Purpose: Instantiate a 1100×780 frameless, transparent window with a
//   secure renderer context (contextIsolation on, nodeIntegration off).
// Params: none
// Returns: void
// Notes: -webkit-app-region: drag on the titlebar element (in renderer CSS)
//   handles window dragging since frame: false removes the OS titlebar.
function createWindow() {
  win = new BrowserWindow({
    width: 1100,
    height: 780,
    frame: false,
    transparent: true,
    resizable: true,
    webPreferences: {
      // preload runs in the renderer process but with Node access,
      // allowing it to call ipcRenderer without exposing it to page scripts.
      preload: path.join(__dirname, 'preload.js'),
      // contextIsolation prevents renderer scripts from accessing the
      // preload's Node/Electron scope — critical security boundary.
      contextIsolation: true,
      // nodeIntegration: false means renderer JS cannot require() Node modules.
      nodeIntegration: false,
      // sandbox: false is required here so the preload script itself can
      // use require('electron') to access ipcRenderer and contextBridge.
      // The renderer remains sandboxed via contextIsolation.
      sandbox: false,
    },
  });

  // Load the dashboard HTML shell from the renderer directory.
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // Open DevTools automatically in dev mode for debugging renderer state.
  if (devMode) {
    win.webContents.openDevTools({ mode: 'detach' });
  }

  // Clear the module-level reference when the window is closed so the
  // activate handler knows to create a new one.
  win.on('closed', () => {
    win = null;
  });
}

// registerIpcHandlers — loads and registers all main-process IPC channel
//   handlers from src/ipc-handlers.js.
// Purpose: Decouple IPC logic from the BrowserWindow lifecycle. Each handler
//   file exports a function that receives ipcMain and registers its channels.
// Params: none
// Returns: void
// Notes: Distinguishes MODULE_NOT_FOUND (expected before Phase D) from genuine
//   runtime errors in ipc-handlers.js. A missing module is a warning; any other
//   error is re-thrown so it surfaces in the terminal rather than silently
//   leaving the app with zero IPC channels and no diagnostic.
function registerIpcHandlers() {
  try {
    const register = require('./src/ipc-handlers');
    register(ipcMain);
  } catch (e) {
    if (e.code === 'MODULE_NOT_FOUND') {
      // Expected before Phase D — ipc-handlers.js has not been created yet.
      console.warn('[agentic-os] ipc-handlers not yet available — IPC surface degraded');
    } else {
      // A real error inside ipc-handlers.js (syntax error, runtime throw, etc.).
      // Re-throw so it appears in the terminal instead of being silently swallowed.
      throw e;
    }
  }
}

// app.whenReady — entry point after Electron has finished initialising.
// Registers IPC handlers first so channels exist before any renderer request,
// then opens the dashboard window.
app.whenReady().then(() => {
  registerIpcHandlers();
  createWindow();
});

// window-all-closed — quit the app when all windows are closed on non-macOS
//   platforms. On macOS, apps conventionally stay in the Dock until Cmd+Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// activate — re-create the window when the Dock icon is clicked on macOS and
//   no windows are currently open. No-op on Windows/Linux (windows are never
//   hidden without being closed on those platforms).
app.on('activate', () => {
  if (win === null) {
    createWindow();
  }
});
