"""Token & cache billing (RelayScope cache-ratio check).
1) Token count: expected input tokens come from EXPECTED_INPUT_TOKENS (e.g. measured with the official
   count_tokens endpoint on the user's own official key) or are skipped. Flag deviation > 5%.
2) Cache: send the same cache_control-marked long system prompt twice; call 2 must report
   cache_read_input_tokens > 0 and lower billable input_tokens.
3) Actual money deducted must be compared manually in the relay dashboard (we never log in or scrape)."""
import json, os, random, string
from common import post, result, DEFAULT_MODEL
THRESH = 0.05

def deviation(expected, reported): return abs(reported - expected) / max(expected, 1)

def total_input(u):
    return (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)

def run(model=DEFAULT_MODEL, expected_input=None, system_text=None):
    if expected_input is None and os.environ.get("EXPECTED_INPUT_TOKENS"):
        expected_input = int(os.environ["EXPECTED_INPUT_TOKENS"])
    # random nonce so call 1 is never a cache hit from an earlier run
    system_text = system_text or (" ".join("".join(random.choices(string.ascii_lowercase, k=6)) for _ in range(1500)))
    body = {"model": model, "max_tokens": 8,
            "system": [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": "ok"}]}
    a = post("/v1/messages", body)["usage"]; b = post("/v1/messages", body)["usage"]
    d = {"call1_usage": a, "call2_usage": b}
    d["cache_ok"] = (b.get("cache_read_input_tokens") or 0) > 0 and (b.get("input_tokens") or 0) < (a.get("input_tokens") or 0) + (a.get("cache_creation_input_tokens") or 0)
    d["token_ok"] = None
    if expected_input:
        d["input_deviation"] = round(deviation(expected_input, total_input(a)), 4)
        d["token_ok"] = d["input_deviation"] <= THRESH
    return result("billing", d["cache_ok"] and d["token_ok"] is not False, d)
if __name__ == "__main__": print(json.dumps(run()))
