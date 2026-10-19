"""Shared helpers. Key read from env RELAY_API_KEY only; never written to disk or into results."""
import os, json, datetime, time, urllib.request, urllib.parse
VERSION = "0.1.0"
DEFAULT_MODEL = os.environ.get("RELAY_MODEL", "claude-sonnet-4-5")

def cfg():
    base, key = os.environ.get("RELAY_BASE_URL"), os.environ.get("RELAY_API_KEY")
    if not base or not key:
        raise SystemExit("set RELAY_BASE_URL and RELAY_API_KEY (your own key; runs locally)")
    if os.environ.get("RELAY_CONFIRM_SPEND") != "yes":
        raise SystemExit("each check spends a few tokens on YOUR account; set RELAY_CONFIRM_SPEND=yes")
    return base.rstrip("/"), key

def _req(path, body):
    base, key = cfg()
    return urllib.request.Request(base + path, json.dumps(body).encode(), {
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})

def post(path, body):
    with urllib.request.urlopen(_req(path, body), timeout=120) as r:
        return json.load(r)

def post_stream(path, body):
    """Return (events, ttft_seconds, total_seconds). events = list of (event_name, data_dict)."""
    body = dict(body, stream=True)
    t0 = time.time(); ttft = None; events = []; name = None
    with urllib.request.urlopen(_req(path, body), timeout=120) as r:
        for raw in r:
            line = raw.decode().rstrip("\n").rstrip("\r")
            if line.startswith("event:"): name = line[6:].strip()
            elif line.startswith("data:"):
                data = json.loads(line[5:].strip())
                if ttft is None and data.get("type") == "content_block_delta": ttft = time.time() - t0
                events.append((name or data.get("type"), data))
    return events, ttft, time.time() - t0

def relay_host():
    return urllib.parse.urlparse(os.environ.get("RELAY_BASE_URL", "")).hostname or ""

def result(check, passed, detail):
    """Contains no key and no prompt text; relay identified by hostname only."""
    return {"check": check, "passed": passed, "detail": detail, "relay_host": relay_host(),
            "date": datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
            "script_version": VERSION}
