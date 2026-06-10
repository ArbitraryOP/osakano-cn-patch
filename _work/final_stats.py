"""Report final translation coverage from overflow.json + the per-file extract totals."""
import json, os, glob, io, sys
sys.stdout = io.open(r"E:\game\_work\final_stats_out.txt", "w", encoding="utf-8")

EXTRACT = r"E:\game\_work\extract"
over = json.load(open(r"E:\game\_work\overflow.json", encoding="utf-8")) if os.path.exists(r"E:\game\_work\overflow.json") else {}

FONT = ("ゴシック", "明朝", "ゴチ", "ＭＳ", "ゴシツク")
def is_font(rec):
    sp = [t["s"] for t in rec["tokens"] if t["t"] == "jp"]
    return any(any(f in s for f in FONT) for s in sp)

total_tr = 0
per = []
for p in sorted(glob.glob(os.path.join(EXTRACT, "*.json"))):
    name = os.path.splitext(os.path.basename(p))[0]
    recs = json.load(open(p, encoding="utf-8"))
    tr = [r for r in recs if any(t["t"] == "jp" for t in r["tokens"])
          and r.get("confidence", 1.0) >= 0.5 and not is_font(r)]
    n = len(tr)
    if n == 0:
        continue
    ov = len(over.get(name, []))
    total_tr += n
    per.append((name, n, ov))

tot_ov = sum(x[2] for x in per)
done = total_tr - tot_ov
print(f"Translatable records (excl. font/UNSURE): {total_tr}")
print(f"Translated to Chinese: {done}  ({100*done/total_tr:.2f}%)")
print(f"Residual Japanese (un-fittable): {tot_ov}  ({100*tot_ov/total_tr:.2f}%)")
print()
print(f"{'file':14} {'translatable':>12} {'zh':>7} {'jp_left':>8}")
for name, n, ov in per:
    print(f"{name:14} {n:12} {n-ov:7} {ov:8}")
print("done")
