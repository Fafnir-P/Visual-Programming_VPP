import subprocess, sys, time, json
d = sys.argv[1]
def run(a):
    t = time.perf_counter()
    p = subprocess.run([sys.executable, d + "/main.py", *a], capture_output=True, text=True)
    return dict(code=p.returncode, out=p.stdout.strip(), err=p.stderr.strip().splitlines()[-1:] , ms=round((time.perf_counter()-t)*1000,1))
r1 = run(["--customer","  ada lovelace ","--qty","3","--price","2.5"])
r1b = run(["--customer","  ada lovelace ","--qty","3","--price","2.5"])
r2 = run(["--customer","   ","--qty","1","--price","1"])
r4 = run(["--customer","x","--qty","abc","--price","1"])
c = dict(C1=r1["code"]==0 and r1["out"]=='{"customer": "Ada Lovelace", "total": "$7.50"}',
 C2=r2["code"]==1 and r2["out"]=="" and len(r2["err"])==1 and "Traceback" not in r2["err"][0] and "Error:" not in r2["err"][0][:6],
 C3=r1["out"]==r1b["out"] and r1["code"]==0,
 C4=r4["code"]==1 and r4["out"]=="" and len(r4["err"])==1 and "Traceback" not in r4["err"][0])
print(json.dumps(dict(checks=c, run_ms=[r1["ms"],r1b["ms"]], r1=r1, r2=r2, r4=r4), ensure_ascii=False))
