// Cue · Meeting Audio — background service worker.
// Click the toolbar icon on your meeting tab: the extension creates a capture stream id for that tab,
// scoped to the Cue tab, and hands it to Cue. Cue then opens the audio with getUserMedia.
// The stream id is single-use and only the Cue tab can redeem it. No audio passes through the extension.

async function cueTabId() {
  const { cueTab } = await chrome.storage.session.get("cueTab");
  if (cueTab) {
    try { await chrome.tabs.get(cueTab); return cueTab; } catch (_) { /* tab closed */ }
  }
  return null;
}

function badge(text, color, title) {
  chrome.action.setBadgeText({ text: text });
  if (color) chrome.action.setBadgeBackgroundColor({ color: color });
  if (title) chrome.action.setTitle({ title: title });
}

chrome.runtime.onMessage.addListener(function (msg, sender) {
  if (!sender.tab) return;
  if (msg && msg.type === "register") {
    chrome.storage.session.set({ cueTab: sender.tab.id });
  } else if (msg && msg.type === "stopped") {
    badge("", null, "Cue: send this tab's sound to Cue");
  }
});

chrome.action.onClicked.addListener(async function (tab) {
  const cue = await cueTabId();
  if (!cue) {
    badge("!", "#f0866e", "Open Cue first, then come back to this tab and click again.");
    chrome.tabs.create({ url: "https://sitongfx.github.io/cue/" });
    return;
  }
  if (tab.id === cue) {
    chrome.tabs.sendMessage(cue, { type: "cue-ext-error", reason: "self" });
    return;
  }
  try {
    const streamId = await chrome.tabCapture.getMediaStreamId({ targetTabId: tab.id, consumerTabId: cue });
    await chrome.tabs.sendMessage(cue, { type: "cue-ext-stream", streamId: streamId, title: tab.title || "" });
    badge("ON", "#c9e36f", "Cue is listening to this tab. Click again to reconnect.");
  } catch (e) {
    chrome.tabs.sendMessage(cue, { type: "cue-ext-error", reason: String((e && e.message) || e) }).catch(function () {});
    badge("!", "#f0866e", "Couldn't capture this tab: " + String((e && e.message) || e));
  }
});
