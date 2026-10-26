#!/usr/bin/env python3
"""Cue server: a small backend for the Cue web/desktop app.

What it does
  * Keeps the Gemini API key on the server. Users sign in with an invite code instead of their own key.
  * POST /v1/chat          streams an answer (Server-Sent Events) from Gemini
  * POST /v1/embed         batch embeddings for meaning-based search
  * POST /v1/transcribe    transcribes a short WAV clip (fallback when streaming recognition can't connect)
  * POST /v1/live-token    mints a short-lived, single-use token for Gemini Live speech recognition,
                           so the browser can stream audio directly without ever seeing the API key
  * POST /v1/contribute    opt-in, anonymous training rows (hashed features + label, never text or audio)
  * GET  /v1/health        liveness + whether the invite code is valid

Standard library only. Configure with environment variables:
  GEMINI_API_KEY   (required) Gemini API key; on Cloud Run, mount it from Secret Manager
  CUE_INVITES      comma-separated "name:code" pairs, e.g. "alice:cue_abc123,bob:cue_def456"
  ALLOWED_ORIGINS  comma-separated origins allowed by CORS (default: GitHub Pages site + desktop app)
  HOST / PORT      bind address (default 127.0.0.1:8787; the container sets HOST=0.0.0.0, PORT=8080)
  DATA_DIR         where opt-in contributions are appended as JSONL (default ./data)
  RATE_PER_MIN     requests per minute per invite (default 60)
  DAILY_CAP        requests per day per invite (default 3000)
  UPSTREAM         Gemini API base URL (tests point this at a fake server)

Nothing the user says is logged: request logs contain only the invite name, the route and the status.
"""
import datetime
import hmac
import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = os.environ.get("UPSTREAM", "https://generativelanguage.googleapis.com").rstrip("/")
CHAT_MODELS = {"gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-flash-lite-latest"}
DEFAULT_CHAT_MODEL = "gemini-3.5-flash-lite"
EMBED_MODEL = "gemini-embedding-001"
LIVE_WS = ("wss://generativelanguage.googleapis.com/ws/"
           "google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContentConstrained")
MAX_BODY = 256 * 1024
MAX_AUDIO_BODY = 8 * 1024 * 1024   # a 5-minute Opus recording is about 1.6 MB as base64
STT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_ORIGINS = "https://sitongfx.github.io,app://cue"


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


class Config:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.invites = {}
        for pair in os.environ.get("CUE_INVITES", "").split(","):
            pair = pair.strip()
            if ":" in pair:
                name, code = pair.split(":", 1)
                if name.strip() and len(code.strip()) >= 12:
                    self.invites[code.strip()] = name.strip()
        self.origins = {o.strip() for o in os.environ.get("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()}
        self.rate_per_min = _env_int("RATE_PER_MIN", 60)
        self.daily_cap = _env_int("DAILY_CAP", 3000)
        self.data_dir = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))


CFG = Config()


class RateLimiter:
    """Per-invite sliding one-minute window plus a daily cap (in memory; resets on restart)."""

    def __init__(self):
        self.lock = threading.Lock()
        self.minute = {}
        self.day = {}

    def allow(self, who):
        now = time.time()
        today = datetime.date.today().isoformat()
        with self.lock:
            q = [t for t in self.minute.get(who, []) if now - t < 60]
            d_key = (who, today)
            if len(q) >= CFG.rate_per_min or self.day.get(d_key, 0) >= CFG.daily_cap:
                self.minute[who] = q
                return False
            q.append(now)
            self.minute[who] = q
            self.day[d_key] = self.day.get(d_key, 0) + 1
            return True


LIMITER = RateLimiter()
CONTRIB_LOCK = threading.Lock()


def upstream_request(path, payload, timeout=60):
    req = urllib.request.Request(
        UPSTREAM + path, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": CFG.api_key})
    return urllib.request.urlopen(req, timeout=timeout)


def upstream_error_message(err):
    try:
        body = json.loads(err.read().decode("utf-8", "replace"))
        return str(body.get("error", {}).get("message", ""))[:200]
    except Exception:
        return ""


class Handler(BaseHTTPRequestHandler):
    server_version = "CueServer/1.0"
    protocol_version = "HTTP/1.1"

    # ---------- helpers ----------
    def log_message(self, fmt, *args):  # route + status only; never request bodies
        pass

    def _log(self, status, who="-"):
        print("%s %s %s %d" % (datetime.datetime.now().isoformat(timespec="seconds"), who, self.path.split("?")[0], status), flush=True)

    def _cors(self):
        origin = self.headers.get("Origin", "")
        if origin and origin in CFG.origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Max-Age", "600")
            if self.headers.get("Access-Control-Request-Private-Network") == "true":
                self.send_header("Access-Control-Allow-Private-Network", "true")  # local testing from a page

    def _json(self, status, obj, who="-"):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)
        self._log(status, who)

    def _who(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        code = auth[7:].strip()
        for known, name in CFG.invites.items():
            if hmac.compare_digest(known.encode(), code.encode()):
                return name
        return None

    def _body(self, limit=MAX_BODY):
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if n <= 0 or n > limit:
            return None
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def _guard(self, limit=MAX_BODY):
        """Common checks for authenticated POST routes. Returns (who, body) or (None, None) after replying."""
        who = self._who()
        if not who:
            self._json(401, {"error": "invalid invite code"})
            return None, None
        if not CFG.api_key:
            self._json(503, {"error": "server has no Gemini API key configured"}, who)
            return None, None
        if not LIMITER.allow(who):
            self._json(429, {"error": "rate limit reached, try again shortly"}, who)
            return None, None
        body = self._body(limit)
        if not isinstance(body, dict):
            self._json(400, {"error": "invalid JSON body"}, who)
            return None, None
        return who, body

    # ---------- routes ----------
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/v1/health":
            who = self._who()
            self._json(200, {"ok": True, "authed": bool(who), "configured": bool(CFG.api_key),
                             "chatModel": DEFAULT_CHAT_MODEL}, who or "-")
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        route = self.path.split("?")[0]
        handlers = {"/v1/chat": self.chat, "/v1/embed": self.embed, "/v1/transcribe": self.transcribe,
                    "/v1/live-token": self.live_token, "/v1/contribute": self.contribute}
        fn = handlers.get(route)
        if not fn:
            self._json(404, {"error": "not found"})
            return
        who, body = self._guard(MAX_AUDIO_BODY if route == "/v1/transcribe" else MAX_BODY)
        if who:
            fn(who, body)

    def chat(self, who, body):
        system = str(body.get("system", ""))[:20000]
        user = str(body.get("user", ""))[:60000]
        model = body.get("model") if body.get("model") in CHAT_MODELS else DEFAULT_CHAT_MODEL
        if not user:
            self._json(400, {"error": "empty prompt"}, who)
            return
        payload = {
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"thinkingConfig": {"thinkingLevel": "minimal"},
                                 "maxOutputTokens": max(16, min(2048, int(body.get("maxTokens") or 1024)))},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        try:
            up = upstream_request("/v1beta/models/%s:streamGenerateContent?alt=sse" % model, payload)
        except urllib.error.HTTPError as e:
            self._json(502, {"error": "Gemini %d: %s" % (e.code, upstream_error_message(e))}, who)
            return
        except (urllib.error.URLError, TimeoutError) as e:
            self._json(502, {"error": "Gemini unreachable: %s" % e}, who)
            return
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            for raw in up:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                try:
                    chunk = json.loads(line[5:].strip())
                except ValueError:
                    continue
                for cand in chunk.get("candidates", []) or []:
                    for part in (cand.get("content") or {}).get("parts", []) or []:
                        text = part.get("text")
                        if text and not part.get("thought"):
                            self.wfile.write(("data: " + json.dumps({"t": text}, ensure_ascii=False) + "\n\n").encode("utf-8"))
                            self.wfile.flush()
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            self._log(200, who)
        except (BrokenPipeError, ConnectionResetError):
            self._log(499, who)  # the client moved on (e.g. a newer question interrupted)
        finally:
            up.close()

    def embed(self, who, body):
        texts = body.get("texts")
        task = body.get("task") if body.get("task") in ("RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT") else "RETRIEVAL_DOCUMENT"
        if not isinstance(texts, list) or not texts or len(texts) > 100:
            self._json(400, {"error": "texts must be a list of 1-100 strings"}, who)
            return
        payload = {"requests": [{"model": "models/" + EMBED_MODEL, "content": {"parts": [{"text": str(t)[:6000]}]},
                                 "taskType": task, "outputDimensionality": 256} for t in texts]}
        try:
            with upstream_request("/v1beta/models/%s:batchEmbedContents" % EMBED_MODEL, payload, timeout=30) as up:
                data = json.loads(up.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            self._json(502, {"error": "Gemini %d: %s" % (e.code, upstream_error_message(e))}, who)
            return
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            self._json(502, {"error": "embedding failed: %s" % e}, who)
            return
        self._json(200, {"vectors": [e.get("values", []) for e in data.get("embeddings", [])]}, who)

    def transcribe(self, who, body):
        audio = body.get("audio")
        if not isinstance(audio, str) or not audio:
            self._json(400, {"error": "audio (base64 WAV) required"}, who)
            return
        hint = str(body.get("hint", ""))[:400]
        mime = body.get("mime") if body.get("mime") in ("audio/wav", "audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg") else "audio/wav"
        instruction = str(body.get("instruction", ""))[:2000] or (
            "Transcribe the speech in this audio verbatim, in the language(s) actually spoken. Never translate. "
            "Output only the transcript, or nothing if there is no clear speech." + ("\nWords that may appear: " + hint if hint else ""))
        long_clip = bool(body.get("long"))
        payload = {"contents": [{"role": "user", "parts": [
            {"inlineData": {"mimeType": mime, "data": audio}}, {"text": instruction}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 8192 if long_clip else 400,
                                 "thinkingConfig": {"thinkingLevel": "minimal"}}}
        try:
            with upstream_request("/v1beta/models/%s:generateContent" % STT_MODEL, payload, timeout=150 if long_clip else 20) as up:
                data = json.loads(up.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            self._json(502, {"error": "Gemini %d: %s" % (e.code, upstream_error_message(e))}, who)
            return
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            self._json(502, {"error": "transcription failed: %s" % e}, who)
            return
        parts = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts")) or []
        self._json(200, {"text": "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()}, who)

    def live_token(self, who, body):
        now = datetime.datetime.now(datetime.timezone.utc)
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        payload = {"uses": 1,
                   "expireTime": (now + datetime.timedelta(minutes=30)).strftime(fmt),
                   "newSessionExpireTime": (now + datetime.timedelta(minutes=1)).strftime(fmt)}
        try:
            with upstream_request("/v1alpha/auth_tokens", payload, timeout=20) as up:
                data = json.loads(up.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            self._json(502, {"error": "Gemini %d: %s" % (e.code, upstream_error_message(e))}, who)
            return
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            self._json(502, {"error": "token failed: %s" % e}, who)
            return
        self._json(200, {"token": data.get("name", ""), "wsUrl": LIVE_WS, "expireTime": data.get("expireTime")}, who)

    def contribute(self, who, body):
        if body.get("consent") is not True:
            self._json(400, {"error": "consent required"}, who)
            return
        rows = body.get("rows")
        if not isinstance(rows, list) or not rows or len(rows) > 200:
            self._json(400, {"error": "rows must be a list of 1-200 items"}, who)
            return
        clean = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            feats = [int(x) for x in (r.get("f") or [])[:200] if isinstance(x, int) and 0 <= x < (1 << 20)]
            if not feats:
                continue
            clean.append({"f": feats, "y": 1 if r.get("kept") else 0,
                          "lang": "zh" if r.get("lang") == "zh" else "en",
                          "len": max(0, min(400, int(r.get("len") or 0)))})
        if not clean:
            self._json(400, {"error": "no valid rows"}, who)
            return
        os.makedirs(CFG.data_dir, exist_ok=True)
        path = os.path.join(CFG.data_dir, "contrib-%s.jsonl" % datetime.date.today().isoformat())
        # The contributor is stored as a one-way hash so rows can be de-duplicated but not attributed.
        src = hmac.new(CFG.api_key.encode(), who.encode(), "sha256").hexdigest()[:12]
        with CONTRIB_LOCK, open(path, "a", encoding="utf-8") as f:
            for r in clean:
                r["src"] = src
                f.write(json.dumps(r) + "\n")
        self._json(200, {"ok": True, "saved": len(clean)}, who)


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = _env_int("PORT", 8787)
    if not CFG.api_key:
        print("WARNING: GEMINI_API_KEY is not set; AI routes will return 503.", flush=True)
    if not CFG.invites:
        print("WARNING: CUE_INVITES is empty; nobody can sign in.", flush=True)
    srv = ThreadingHTTPServer((host, port), Handler)
    srv.daemon_threads = True
    print("Cue server on http://%s:%d (origins: %s)" % (host, port, ", ".join(sorted(CFG.origins))), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
