"""Daily randomized capability prompts (fixed public cases get hardcoded). Tasks are generated from a local random seed with known answers:
arithmetic chain and needle-in-haystack. Only pass/fail + seed hash are reported; prompts stay local.
TODO: random JSON-schema tool-call task."""
import random, secrets, string, hashlib, json
from common import post, result, DEFAULT_MODEL

def gen(seed=None):
    seed = seed or secrets.token_hex(8); rnd = random.Random(seed)
    n = [rnd.randint(10, 99) for _ in range(5)]
    arith = {"kind": "arith", "prompt": f"Compute (({n[0]}*{n[1]})+{n[2]})-{n[3]}*{n[4]}. Answer with the integer only.",
             "answer": str(n[0] * n[1] + n[2] - n[3] * n[4])}
    needle = "".join(rnd.choices(string.ascii_uppercase, k=10))
    hay = ["".join(rnd.choices(string.ascii_lowercase, k=8)) for _ in range(2000)]
    hay.insert(rnd.randrange(len(hay)), f"SECRET={needle}")
    nih = {"kind": "needle", "prompt": " ".join(hay) + "\nWhat is SECRET? Reply with the value only.", "answer": needle}
    return {"seed_hash": hashlib.sha256(seed.encode()).hexdigest()[:16], "tasks": [arith, nih]}

def grade(task, text): return task["answer"] in (text or "").replace(",", "")

def run(model=DEFAULT_MODEL, seed=None):
    g = gen(seed); out = {}
    for t in g["tasks"]:
        r = post("/v1/messages", {"model": model, "max_tokens": 64, "messages": [{"role": "user", "content": t["prompt"]}]})
        text = "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")
        out[t["kind"]] = grade(t, text)
    return result("daily_prompts", all(out.values()), {"seed_hash": g["seed_hash"], "tasks": out})
if __name__ == "__main__": print(json.dumps(run()))
