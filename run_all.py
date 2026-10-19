"""Run all checks locally and write result.json (no key, no prompts) for optional voluntary submission."""
import json, check_signature, check_format, check_billing, daily_prompts, check_speed_repeat
def main(path="result.json"):
    out = []
    names = {check_signature: "signature", check_format: "format", check_billing: "billing",
             daily_prompts: "daily_prompts", check_speed_repeat: "speed_repeat"}
    from common import result
    for m, name in names.items():
        try: out.append(m.run())
        except SystemExit: raise
        except Exception as e:
            r = result(name, None, {}); r["error"] = type(e).__name__; out.append(r)
    with open(path, "w") as f: json.dump(out, f, ensure_ascii=False, indent=1)
    return out
if __name__ == "__main__":
    import validate_result
    errs = validate_result.validate(main())
    print("wrote result.json —", "schema OK" if not errs else "SCHEMA ERRORS: " + "; ".join(errs))
    print("review it before any voluntary submission (GitHub issue template, results only, never keys)")
