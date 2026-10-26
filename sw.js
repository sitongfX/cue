// Makes Cue installable and keeps the app shell available offline.
// Never caches API calls (Gemini etc.) or any user data.
const CACHE = "cue-shell-v19";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icon.svg"];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== self.location.origin) return;
  // Network first so updates appear immediately; fall back to the cached shell offline.
  e.respondWith(fetch(e.request).then((resp) => {
    const copy = resp.clone();
    if (resp.ok) caches.open(CACHE).then((c) => c.put(e.request, copy));
    return resp;
  }).catch(() => caches.match(e.request).then((r) => r || caches.match("./index.html"))));
});
