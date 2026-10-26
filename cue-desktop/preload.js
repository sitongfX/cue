// Exposes a tiny, explicit API to the Cue page. No Node.js access is given to web content.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("cueDesktop", {
  platform: process.platform,
  toggleOverlay: () => ipcRenderer.invoke("cue:overlay"),
  setProtect: (on) => ipcRenderer.invoke("cue:protect", Boolean(on)),
  onOverlay: (cb) => ipcRenderer.on("cue:overlay", (_e, on) => cb(Boolean(on)))
});
