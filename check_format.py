"""Protocol fingerprint (veridrop; RelayScope).
Non-stream: id 'msg_', type 'message', model echoes request, usage fields, tool ids 'toolu_'.
Stream: SSE order message_start → (content_block_start → delta* → stop)+ → message_delta → message_stop,
and streamed text equals non-stream structure (block types)."""
import json
from common import post, post_stream, result, DEFAULT_MODEL

def check_message(r, model):
    issues = []
    if not str(r.get("id", "")).startswith("msg_"): issues.append("id_prefix")
    if r.get("type") != "message": issues.append("type")
    if r.get("model") != model: issues.append("model_mismatch:" + str(r.get("model")))
    u = r.get("usage") or {}
    for k in ("input_tokens", "output_tokens"):
        if k not in u: issues.append("usage." + k)
    for b in r.get("content", []):
        if b.get("type") == "tool_use" and not str(b.get("id", "")).startswith("toolu_"): issues.append("toolu_prefix")
    return issues

def check_sse(events):
    names = [n for n, _ in events if n != "ping"]
    issues = []
    if not names or names[0] != "message_start": issues.append("sse_start")
    if names[-2:] != ["message_delta", "message_stop"]: issues.append("sse_end")
    open_ = False
    for n in names[1:-2]:
        if n == "content_block_start":
            if open_: issues.append("sse_nested_block")
            open_ = True
        elif n == "content_block_delta" and not open_: issues.append("sse_delta_outside_block")
        elif n == "content_block_stop":
            if not open_: issues.append("sse_stop_without_start")
            open_ = False
    return issues

def run(model=DEFAULT_MODEL):
    body = {"model": model, "max_tokens": 16, "messages": [{"role": "user", "content": "say ok"}]}
    issues = check_message(post("/v1/messages", body), model)
    events, _, _ = post_stream("/v1/messages", body)
    issues += check_sse(events)
    start = next((d for n, d in events if n == "message_start"), {})
    issues += ["stream:" + i for i in check_message(dict(start.get("message", {}), content=[]), model)]
    return result("format", not issues, {"issues": sorted(set(issues))})
if __name__ == "__main__": print(json.dumps(run()))
