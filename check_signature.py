"""Thinking-signature check (method per veridrop (github.com/canarybyte/veridrop)).
Real Anthropic thinking blocks carry an opaque server-generated `signature`.
Step 1 (heuristic): thinking block present, signature non-empty, base64-like, >= MIN_SIG_LEN chars.
Step 2 (optional, strongest): if OFFICIAL_ANTHROPIC_KEY is set, replay the thinking block to the official
API (costs a few tokens on the user's own official account); Anthropic rejects forged signatures.
Limitation: proves only this request; mixed routing needs repeated sampling. MIN_SIG_LEN is an
unverified assumption to calibrate against official responses."""
import json, os, re, urllib.request, urllib.error
from common import post, result, DEFAULT_MODEL
MIN_SIG_LEN = 100
B64 = re.compile(r"^[A-Za-z0-9+/=_-]+$")

def sig_looks_valid(s):
    return isinstance(s, str) and len(s) >= MIN_SIG_LEN and bool(B64.match(s))

def official_replay(model, prompt, msg):
    key = os.environ.get("OFFICIAL_ANTHROPIC_KEY")
    if not key: return None
    body = {"model": model, "max_tokens": 1100, "thinking": {"type": "enabled", "budget_tokens": 1024},
            "messages": [{"role": "user", "content": prompt},
                         {"role": "assistant", "content": msg["content"]},
                         {"role": "user", "content": "ok"}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", json.dumps(body).encode(),
        {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try: urllib.request.urlopen(req, timeout=120); return True
    except urllib.error.HTTPError as e: return False if e.code == 400 else None

def run(model=DEFAULT_MODEL):
    prompt = "What is 17*23? Think briefly."
    r = post("/v1/messages", {"model": model, "max_tokens": 2048,
        "thinking": {"type": "enabled", "budget_tokens": 1024},
        "messages": [{"role": "user", "content": prompt}]})
    sigs = [b.get("signature") for b in r.get("content", []) if b.get("type") == "thinking"]
    heuristic = bool(sigs) and all(sig_looks_valid(s) for s in sigs)
    replay = official_replay(model, prompt, r) if heuristic else None
    passed = heuristic and replay is not False
    return result("signature", passed, {"thinking_blocks": len(sigs), "heuristic_ok": heuristic,
                  "official_replay": replay})
if __name__ == "__main__": print(json.dumps(run()))
