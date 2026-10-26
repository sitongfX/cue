// Cue · Meeting Audio — content script on the Cue page.
// Bridges the extension and the page with window.postMessage (same window, same origin only).
(function () {
  const VERSION = "1.0.0";
  function toPage(data) {
    data.source = "cue-ext";
    window.postMessage(data, window.location.origin === "null" ? "*" : window.location.origin);
  }
  function hello() { toPage({ type: "hello", version: VERSION }); }

  chrome.runtime.sendMessage({ type: "register" }).catch(function () {});

  chrome.runtime.onMessage.addListener(function (msg) {
    if (!msg || typeof msg.type !== "string") return;
    if (msg.type === "cue-ext-stream") toPage({ type: "stream", streamId: String(msg.streamId), title: String(msg.title || "") });
    else if (msg.type === "cue-ext-error") toPage({ type: "error", reason: String(msg.reason || "") });
  });

  window.addEventListener("message", function (ev) {
    if (ev.source !== window || !ev.data || ev.data.source !== "cue-page") return;
    if (ev.data.type === "ping") { chrome.runtime.sendMessage({ type: "register" }).catch(function () {}); hello(); }
    else if (ev.data.type === "stopped") chrome.runtime.sendMessage({ type: "stopped" }).catch(function () {});
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", hello);
  else hello();
})();
