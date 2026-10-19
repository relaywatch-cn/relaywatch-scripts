"""Stdlib validator for result.json against result.schema.json rules + leak checks. Usage: python3 validate_result.py result.json"""
import json, re, sys
CHECKS = {"signature", "format", "billing", "daily_prompts", "speed_repeat"}
ALLOWED = {"check", "passed", "detail", "error", "relay_host", "date", "script_version"}
FORBIDDEN_DETAIL_KEYS = {"prompt", "text", "content", "messages", "system", "api_key", "key", "authorization", "x-api-key", "answer", "seed"}
LEAK_PATTERNS = [r"sk-ant-[A-Za-z0-9_-]+", r"sk-[A-Za-z0-9]{20,}", r"SECRET=", r"Compute \(\(", r"Write a 100-word story"]

def _walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items(): yield k; yield from _walk_keys(v)
    elif isinstance(o, list):
        for v in o: yield from _walk_keys(v)

def validate(data, secrets=()):
    errs = []
    if not isinstance(data, list) or not data: return ["top level must be a non-empty array"]
    for i, r in enumerate(data):
        if not isinstance(r, dict): errs.append(f"[{i}] not object"); continue
        for k in ("check", "passed", "relay_host", "date", "script_version"):
            if k not in r: errs.append(f"[{i}] missing {k}")
        extra = set(r) - ALLOWED
        if extra: errs.append(f"[{i}] extra fields {sorted(extra)}")
        if r.get("check") not in CHECKS: errs.append(f"[{i}] bad check {r.get('check')}")
        if r.get("passed") not in (True, False, None): errs.append(f"[{i}] passed not bool/null")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(r.get("date", ""))): errs.append(f"[{i}] bad date")
        if "detail" in r and not isinstance(r["detail"], dict): errs.append(f"[{i}] detail not object")
        bad = {k.lower() for k in _walk_keys(r.get("detail", {}))} & FORBIDDEN_DETAIL_KEYS
        if bad: errs.append(f"[{i}] forbidden detail keys {sorted(bad)}")
    s = json.dumps(data, ensure_ascii=False)
    for p in LEAK_PATTERNS:
        if re.search(p, s): errs.append(f"leak pattern {p}")
    for sec in secrets:
        if sec and sec in s: errs.append("secret value leaked")
    return errs

if __name__ == "__main__":
    e = validate(json.load(open(sys.argv[1])))
    print("OK" if not e else "\n".join(e)); sys.exit(1 if e else 0)
