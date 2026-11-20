import json, math, os, subprocess, sys, time, datetime
B = os.path.dirname(os.path.abspath(__file__))


def run(d, *args):
    t = time.perf_counter()
    r = subprocess.run([sys.executable, os.path.join(B, d, "main.py"), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr, (time.perf_counter() - t) * 1000


def secs(d):
    f = lambda n: datetime.datetime.fromisoformat(open(os.path.join(B, d, n), encoding="utf-8-sig").read().strip())
    return (f("T1.txt") - f("T0.txt")).total_seconds()


def toks(d):
    code = len(open(os.path.join(B, d, "main.py"), encoding="utf-8").read())
    prompt = len(open(os.path.join(B, d, "prompt.txt"), encoding="utf-8-sig").read())
    return 600 + math.ceil(prompt / 4), math.ceil(code / 4)


out = {}
for d in ("run1", "run2"):
    c1 = run(d, "--customer", "  ada lovelace ", "--qty", "3", "--price", "2.5")
    c1b = run(d, "--customer", "  ada lovelace ", "--qty", "3", "--price", "2.5")
    c2 = run(d, "--customer", "   ", "--qty", "1", "--price", "1")
    c4 = run(d, "--customer", "x", "--qty", "abc", "--price", "1")
    exp = {"customer": "Ada Lovelace", "total": "$7.50"}
    chk = {
        "C1": c1[0] == 0 and json.loads(c1[1]) == exp,
        "C2": c2[0] == 1 and c2[1] == "" and len(c2[2].strip().splitlines()) == 1,
        "C3": c1[1] == c1b[1],
        "C4": c4[0] == 1 and c4[1] == "" and len(c4[2].strip().splitlines()) == 1,
    }
    i, o = toks(d)
    out[d] = dict(input_tokens_est=i, output_tokens_est=o, attempts=1, repairs=0,
                  model_step_seconds=secs(d), local_run_ms=round(c1[3], 1), checks=chk)

base = ["--customer", " bob smith ", "--email", " Bob@Example.COM ", "--phone", "(555) 123-4567",
        "--qty", "3", "--price", "19.99", "--discount-percent", "10", "--tax-percent", "8",
        "--ship-date", "2026-01-30", "--days-to-deliver", "5"]


def rep(args, key, val):
    a = list(args); a[a.index(key) + 1] = val; return a


b1 = run("big", *base)
b1b = run("big", *base)
b2 = run("big", *rep(base, "--email", "bob@examplecom"))
b3 = run("big", *rep(base, "--qty", "-1"))
exp = {"customer": "Bob Smith", "email": "bob@example.com", "phone": "5551234567",
       "subtotal": "$59.97", "discount": "$6.00", "tax": "$4.32", "total": "$58.29",
       "delivery_date": "2026-02-04"}
chk = {
    "B1": b1[0] == 0 and json.loads(b1[1]) == exp,
    "B2": b2[0] == 1 and b2[1] == "" and len(b2[2].strip().splitlines()) == 1,
    "B3": b3[0] == 1 and b3[1] == "" and len(b3[2].strip().splitlines()) == 1,
    "B4": b1[1] == b1b[1],
}
i, o = toks("big")
out["big"] = dict(input_tokens_est=i, output_tokens_est=o, attempts=1, repairs=0,
                  model_step_seconds=secs("big"), local_run_ms=round(b1[3], 1), checks=chk)
m = lambda k: (out["run1"][k] + out["run2"][k]) / 2
out["task1_medians"] = {k: m(k) for k in ("input_tokens_est", "output_tokens_est", "model_step_seconds", "local_run_ms")}
out["notes"] = ("tokens = ceil(chars/4); input = prompt.txt + fixed 600 allowance for system context. "
                "model_step_seconds = Get-Date T0..T1 around the write step, includes tool-call overhead, not pure generation. "
                "median of 2 runs = mean. local_run_ms includes Python start-up.")
json.dump(out, open(os.path.join(B, "..", "measure2_vibe.json"), "w"), indent=2)
print(json.dumps(out, indent=2)); print(b1[1], b1[2], b2[2], b3[2])
