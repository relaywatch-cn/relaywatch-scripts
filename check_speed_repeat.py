"""Speed & repeat checks.
Speed: streaming time-to-first-token and output tokens/s. Flag outside [MIN_TPS, MAX_TPS].
Defaults are UNVERIFIED placeholders; calibrate by measuring the official API yourself (RELAY_MIN_TPS/RELAY_MAX_TPS).
Repeat: same open-ended prompt twice at temperature=1; identical long outputs suggest canned replies."""
import json, os
from common import post_stream, result, DEFAULT_MODEL
MIN_TPS = float(os.environ.get("RELAY_MIN_TPS", 15))
MAX_TPS = float(os.environ.get("RELAY_MAX_TPS", 400))

def collect(events):
    text = "".join(d.get("delta", {}).get("text", "") for n, d in events if n == "content_block_delta")
    out_tok = next((d.get("usage", {}).get("output_tokens") for n, d in events if n == "message_delta"), 0) or 0
    return text, out_tok

def run(model=DEFAULT_MODEL):
    body = {"model": model, "max_tokens": 200, "temperature": 1,
            "messages": [{"role": "user", "content": "Write a 100-word story about a random animal."}]}
    texts, tps, ttfts = [], [], []
    for _ in range(2):
        ev, ttft, total = post_stream("/v1/messages", body)
        text, n = collect(ev); texts.append(text)
        gen_time = max(total - (ttft or 0), 1e-3)
        tps.append(round(n / gen_time, 1)); ttfts.append(round(ttft or total, 3))
    identical = texts[0] == texts[1] and len(texts[0]) > 50
    speed_ok = all(MIN_TPS <= x <= MAX_TPS for x in tps)
    return result("speed_repeat", speed_ok and not identical,
                  {"identical": identical, "tok_per_s": tps, "ttft_s": ttfts, "speed_ok": speed_ok,
                   "range_note": "unverified default range"})
if __name__ == "__main__": print(json.dumps(run()))
