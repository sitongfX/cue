// Cue desktop (Electron). Loads the same Cue web app from bundled files and adds what a browser can't do:
//   * system audio without a share picker (Windows loopback; macOS uses the native system picker once)
//   * an always-on-top floating window
//   * content protection: the Cue window is hidden from screen sharing and recordings
const { app, BrowserWindow, session, desktopCapturer, ipcMain, shell, protocol, net, systemPreferences } = require("electron");
const path = require("path");
const { pathToFileURL } = require("url");

const SMOKE = process.argv.includes("--smoke");
const APP_DIR = path.join(__dirname, "app");

// Serve the app from app://cue/ so it gets a stable, secure origin (IndexedDB, mic, CORS).
protocol.registerSchemesAsPrivileged([
  { scheme: "app", privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true, stream: true } }
]);

let win = null;
let overlay = false;
let normalBounds = null;

function createWindow() {
  win = new BrowserWindow({
    width: 1280, height: 860, minWidth: 360, minHeight: 420,
    backgroundColor: "#0d0e0c", title: "Cue", show: !SMOKE,
    webPreferences: { preload: path.join(__dirname, "preload.js"), contextIsolation: true, sandbox: true, nodeIntegration: false }
  });
  win.setContentProtection(true);
  win.loadURL("app://cue/index.html");

  // Links open in the default browser; the app itself never navigates away.
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https:\/\//.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => { if (!url.startsWith("app://cue/")) e.preventDefault(); });

  if (SMOKE) {
    win.webContents.on("did-finish-load", async () => {
      const r = await win.webContents.executeJavaScript(
        "JSON.stringify({ title: document.title, desktop: Boolean(window.cueDesktop), start: Boolean(document.getElementById('btnReadyStart')), addTab: document.getElementById('btnAddTab').querySelector('span').textContent })");
      console.log("SMOKE " + r);
      app.exit(JSON.parse(r).desktop ? 0 : 1);
    });
    setTimeout(() => { console.log("SMOKE timeout"); app.exit(2); }, 20000);
  }
}

function setOverlay(on) {
  if (!win) return;
  overlay = on;
  if (on) {
    normalBounds = win.getBounds();
    win.setAlwaysOnTop(true, "floating");
    win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
    win.setBounds({ width: 440, height: 560, x: normalBounds.x + normalBounds.width - 460, y: normalBounds.y + 40 });
  } else {
    win.setAlwaysOnTop(false);
    win.setVisibleOnAllWorkspaces(false);
    if (normalBounds) win.setBounds(normalBounds);
  }
  win.webContents.send("cue:overlay", on);
}

app.whenReady().then(async () => {
  protocol.handle("app", (req) => {
    const u = new URL(req.url);
    const rel = decodeURIComponent(u.pathname).replace(/^\/+/, "") || "index.html";
    const file = path.normalize(path.join(APP_DIR, rel));
    if (!file.startsWith(APP_DIR)) return new Response("Not found", { status: 404 });
    return net.fetch(pathToFileURL(file).toString());
  });

  const ses = session.defaultSession;
  ses.setPermissionRequestHandler((wc, permission, callback) => {
    callback(["media", "display-capture", "clipboard-sanitized-write", "notifications", "fullscreen"].includes(permission));
  });
  ses.setPermissionCheckHandler((wc, permission) => ["media", "display-capture", "clipboard-sanitized-write"].includes(permission));

  // getDisplayMedia() from the app = "give me the computer's sound". Windows: loopback audio directly.
  // macOS: Chromium's ScreenCaptureKit path needs the native system picker for audio, so we use it.
  ses.setDisplayMediaRequestHandler((request, callback) => {
    desktopCapturer.getSources({ types: ["screen"] }).then((sources) => {
      callback({ video: sources[0], audio: process.platform === "win32" ? "loopback" : undefined });
    }).catch(() => callback({}));
  }, { useSystemPicker: process.platform === "darwin" });

  if (process.platform === "darwin") {
    try { await systemPreferences.askForMediaAccess("microphone"); } catch (_) {}
  }

  ipcMain.handle("cue:overlay", () => { setOverlay(!overlay); return overlay; });
  ipcMain.handle("cue:protect", (e, on) => { if (win) win.setContentProtection(Boolean(on)); return Boolean(on); });

  createWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
