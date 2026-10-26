"""Tests for cue-server with a fake Gemini upstream (no network, no real key)."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))


class FakeGemini(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(n) or b"{}")
        FakeGemini.calls.append((self.path, self.headers.get("x-goog-api-key"), body))
        if "streamGenerateContent" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for piece in ["价格按年", "订阅。\n• 八五折"]:
                chunk = {"candidates": [{"content": {"parts": [{"text": piece}]}}]}
                self.wfile.write(("data: " + json.dumps(chunk, ensure_ascii=False) + "\r\n\r\n").encode())
                self.wfile.flush()
            return
        if "batchEmbedContents" in self.path:
            out = {"embeddings": [{"values": [0.1, 0.2, 0.3]} for _ in body["requests"]]}
        elif ":generateContent" in self.path:
            out = {"candidates": [{"content": {"parts": [{"text": "你好世界"}]}}]}
        elif "auth_tokens" in self.path:
            out = {"name": "auth_tokens/fake123", "expireTime": "2099-01-01T00:00:00Z"}
        else:
            self.send_response(404); self.end_headers(); return
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake = ThreadingHTTPServer(("127.0.0.1", 0), FakeGemini)
        threading.Thread(target=cls.fake.serve_forever, daemon=True).start()
        cls.port = free_port()
        cls.data = tempfile.mkdtemp()
        env = dict(os.environ, GEMINI_API_KEY="test-key", CUE_INVITES="alice:cue_testinvite000001",
                   UPSTREAM="http://127.0.0.1:%d" % cls.fake.server_address[1], PORT=str(cls.port),
                   HOST="127.0.0.1", DATA_DIR=cls.data, RATE_PER_MIN="8",
                   ALLOWED_ORIGINS="https://sitongfx.github.io,app://cue")
        cls.proc = subprocess.Popen([sys.executable, os.path.join(HERE, "server.py")], env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for _ in range(50):
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/v1/health" % cls.port, timeout=1); break
            except Exception:
                time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.proc.kill()
        cls.fake.shutdown()

    def req(self, path, body=None, token="cue_testinvite000001", origin=None):
        headers = {"Content-Type": "application/json"}
        if token: headers["Authorization"] = "Bearer " + token
        if origin: headers["Origin"] = origin
        r = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, path),
                                   data=None if body is None else json.dumps(body).encode(), headers=headers,
                                   method="GET" if body is None else "POST")
        return urllib.request.urlopen(r, timeout=5)

    def test_01_health_authed(self):
        j = json.load(self.req("/v1/health"))
        self.assertTrue(j["ok"] and j["authed"] and j["configured"])
        j = json.load(self.req("/v1/health", token="wrong"))
        self.assertFalse(j["authed"])

    def test_02_bad_invite_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.req("/v1/chat", {"user": "hi"}, token="cue_nope_nope_nope")
        self.assertEqual(cm.exception.code, 401)

    def test_03_chat_streams_and_hides_key(self):
        r = self.req("/v1/chat", {"system": "s", "user": "价格？", "model": "evil-model"}, origin="https://sitongfx.github.io")
        self.assertEqual(r.headers["Access-Control-Allow-Origin"], "https://sitongfx.github.io")
        text = r.read().decode()
        deltas = [json.loads(l[6:])["t"] for l in text.split("\n") if l.startswith("data: {")]
        self.assertEqual("".join(deltas), "价格按年订阅。\n• 八五折")
        self.assertIn("[DONE]", text)
        path, key, body = [c for c in FakeGemini.calls if "stream" in c[0]][-1]
        self.assertIn("gemini-3.5-flash-lite", path)           # unknown models are replaced
        self.assertEqual(key, "test-key")                        # key only goes upstream
        self.assertEqual(body["generationConfig"]["thinkingConfig"]["thinkingLevel"], "minimal")
        self.assertNotIn("test-key", text)

    def test_04_cors_unknown_origin(self):
        r = self.req("/v1/health", origin="https://evil.example")
        self.assertIsNone(r.headers.get("Access-Control-Allow-Origin"))

    def test_05_embed(self):
        j = json.load(self.req("/v1/embed", {"texts": ["a", "b"], "task": "RETRIEVAL_QUERY"}))
        self.assertEqual(len(j["vectors"]), 2)

    def test_05b_transcribe(self):
        j = json.load(self.req("/v1/transcribe", {"audio": "UklGRg==", "hint": "Cue"}))
        self.assertEqual(j["text"], "你好世界")
        j = json.load(self.req("/v1/transcribe", {"audio": "GkXfow==", "mime": "audio/webm", "instruction": "label speakers", "long": True}))
        path, key, body = [c for c in FakeGemini.calls if ":generateContent" in c[0]][-1]
        self.assertEqual(body["contents"][0]["parts"][0]["inlineData"]["mimeType"], "audio/webm")
        self.assertEqual(body["contents"][0]["parts"][1]["text"], "label speakers")
        self.assertEqual(body["generationConfig"]["maxOutputTokens"], 8192)

    def test_06_live_token(self):
        j = json.load(self.req("/v1/live-token", {}))
        self.assertEqual(j["token"], "auth_tokens/fake123")
        self.assertIn("BidiGenerateContentConstrained", j["wsUrl"])

    def test_07_contribute_requires_consent_and_strips_text(self):
        with self.assertRaises(urllib.error.HTTPError):
            self.req("/v1/contribute", {"rows": [{"f": [1, 2], "kept": True}]})
        j = json.load(self.req("/v1/contribute", {"consent": True, "rows": [
            {"f": [1, 2, 999999999], "kept": True, "lang": "zh", "len": 12, "text": "secret words"}]}))
        self.assertEqual(j["saved"], 1)
        files = os.listdir(self.data)
        content = open(os.path.join(self.data, files[0])).read()
        self.assertNotIn("secret", content)
        self.assertNotIn("alice", content)
        row = json.loads(content.strip().split("\n")[-1])
        self.assertEqual(row["f"], [1, 2])

    def test_08_rate_limit(self):
        codes = []
        for _ in range(8):
            try:
                self.req("/v1/embed", {"texts": ["x"]}); codes.append(200)
            except urllib.error.HTTPError as e:
                codes.append(e.code)
        self.assertIn(429, codes)

    def test_09_body_limit(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.req("/v1/chat", {"user": "x" * 300000}, token="cue_testinvite000001")
        self.assertIn(cm.exception.code, (400, 429))


if __name__ == "__main__":
    unittest.main(verbosity=1)
