"""Local mock of the Anthropic Messages API (shape per docs.anthropic.com Messages + streaming docs)
with adulterated variants, selected by URL prefix: http://127.0.0.1:PORT/<variant>/v1/messages
Variants: honest, nosig, forgedsig, inflated, wrongmodel, nocache, slow, repeat, badformat.
Token counting is a whitespace-word approximation (mock only). Never contacts any real API."""
import json, re, time, random, string, hashlib, hmac, base64, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
VARIANTS = {"honest", "nosig", "forgedsig", "inflated", "wrongmodel", "nocache", "slow", "repeat", "badformat"}
SECRET = b"mock-only-secret"
WORDS = "fox owl otter heron lynx badger crane wolf seal hare moth kestrel river moss stone dusk".split()

def ntok(s): return len(str(s).split())
def text_of(c): return c if isinstance(c, str) else " ".join(b.get("text", "") for b in c if isinstance(b, dict))

def answer(prompt, variant):
    if variant == "wrongmodel": return "42"
    m = re.search(r"Compute \(\((\d+)\*(\d+)\)\+(\d+)\)-(\d+)\*(\d+)", prompt)
    if m:
        a, b, c, d, e = map(int, m.groups()); return str(a * b + c - d * e)
    m = re.search(r"SECRET=([A-Z]+)", prompt)
    if m: return m.group(1)
    if "17*23" in prompt: return "391"
    if "story" in prompt:
        if variant == "repeat": return " ".join(WORDS * 3)
        return " ".join(random.choice(WORDS) for _ in range(40 if variant == "slow" else 100))
    return "ok"

class State:
    cache = set(); lock = threading.Lock(); calls = {}  # (variant, stream) -> count

def build(variant, body):
    model = body.get("model", "")
    sys_text = text_of(body.get("system", ""))
    cached = isinstance(body.get("system"), list) and any(b.get("cache_control") for b in body["system"])
    msgs = body.get("messages", [])
    msg_tokens = sum(ntok(text_of(m.get("content", ""))) for m in msgs)
    sys_tokens = ntok(sys_text)
    usage = {"input_tokens": sys_tokens + msg_tokens, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    if cached and variant != "nocache":
        key = hashlib.sha256(sys_text.encode()).hexdigest()
        with State.lock:
            hit = key in State.cache; State.cache.add(key)
        usage["input_tokens"] = msg_tokens
        usage["cache_read_input_tokens" if hit else "cache_creation_input_tokens"] = sys_tokens
    if variant == "inflated":  # over-report every input bucket by 30%
        for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
            usage[k] = int(usage[k] * 1.3)
    last = text_of(msgs[-1]["content"]) if msgs else ""
    text = answer(last, variant)
    content = []
    if body.get("thinking", {}).get("type") == "enabled" and variant != "nosig":
        thought = "Let me compute this."
        if variant == "forgedsig": sig = "fake-signature"
        else: sig = base64.b64encode(b"".join(hmac.new(SECRET, thought.encode() + bytes([i]), "sha256").digest() for i in range(8))).decode()
        content.append({"type": "thinking", "thinking": thought, "signature": sig})
    content.append({"type": "text", "text": text})
    usage["output_tokens"] = ntok(text) + (5 if len(content) > 1 else 0)
    rid = ("chatcmpl-" if variant == "badformat" else "msg_") + "".join(random.choices(string.ascii_letters + string.digits, k=24))
    return {"id": rid, "type": "message", "role": "assistant",
            "model": "claude-3-5-haiku-20241022" if variant == "wrongmodel" else model,
            "content": content, "stop_reason": "end_turn", "stop_sequence": None, "usage": usage}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        parts = self.path.strip("/").split("/", 1)
        if len(parts) < 2 or parts[0] not in VARIANTS or parts[1] != "v1/messages":
            self.send_response(404); self.end_headers(); return
        variant = parts[0]
        if not self.headers.get("x-api-key"):
            self.send_response(401); self.end_headers(); return
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        with State.lock:
            k = (variant, bool(body.get("stream"))); State.calls[k] = State.calls.get(k, 0) + 1
        msg = build(variant, body)
        delay = 0.1 if variant == "slow" else 0.004
        if not body.get("stream"):
            time.sleep(delay * msg["usage"]["output_tokens"])
            out = json.dumps(msg).encode()
            self.send_response(200); self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(out))); self.end_headers(); self.wfile.write(out); return
        self.send_response(200); self.send_header("content-type", "text/event-stream"); self.end_headers()
        def ev(name, data):
            self.wfile.write(f"event: {name}\ndata: {json.dumps(data)}\n\n".encode()); self.wfile.flush()
        start = dict(msg, content=[], stop_reason=None, usage=dict(msg["usage"], output_tokens=1))
        if variant != "badformat": ev("message_start", {"type": "message_start", "message": start})
        ev("ping", {"type": "ping"})
        for i, b in enumerate(msg["content"]):
            if b["type"] == "thinking":
                ev("content_block_start", {"type": "content_block_start", "index": i, "content_block": {"type": "thinking", "thinking": ""}})
                ev("content_block_delta", {"type": "content_block_delta", "index": i, "delta": {"type": "thinking_delta", "thinking": b["thinking"]}})
                ev("content_block_delta", {"type": "content_block_delta", "index": i, "delta": {"type": "signature_delta", "signature": b["signature"]}})
            else:
                ev("content_block_start", {"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}})
                for w in b["text"].split(" "):
                    time.sleep(delay)
                    ev("content_block_delta", {"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": w + " "}})
            ev("content_block_stop", {"type": "content_block_stop", "index": i})
        ev("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                             "usage": {"output_tokens": msg["usage"]["output_tokens"]}})
        ev("message_stop", {"type": "message_stop"})

def serve(port=0):
    s = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s
if __name__ == "__main__":
    s = serve(8787); print("mock on http://127.0.0.1:8787/<variant>/v1/messages"); threading.Event().wait()
