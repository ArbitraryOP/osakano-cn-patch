"""Build a translation chunk plan + per-chunk input files from extract/*.json.
Usage: python plan_chunks.py <basename1,basename2,...|ALL> [max_records] [max_jpchars]
Outputs:
  E:\\game\\_work\\chunk_plan.json   list of {name,start_id,end_id,n,jp_chars,in_path,out_path}
  E:\\game\\_work\\chunks\\<name>__<s>_<e>.in.json   = [{id, spans:[jp span text,...]}]
Only records with >=1 'jp' token and confidence>=0.5 are translated; others are skipped
(a no-edit reinsert re-emits their original bytes).
"""
import io, sys, json, os, glob

EXTRACT = r"E:\game\_work\extract"
CHUNKDIR = r"E:\game\_work\chunks"
PARTDIR = r"E:\game\_work\translated_parts"
OUT = r"E:\game\_work\chunk_plan.json"
os.makedirs(CHUNKDIR, exist_ok=True)
os.makedirs(PARTDIR, exist_ok=True)

def jp_spans(rec):
    return [t["s"] for t in rec["tokens"] if t["t"] == "jp"]

# Font-name fragments must NOT be translated (engine uses them as GDI face names).
FONT_FRAGS = ("ゴシック", "明朝", "ゴチ", "ＭＳ", "ゴシツク")

def is_font_record(rec):
    sp = jp_spans(rec)
    if not sp:
        return False
    return any(any(f in s for f in FONT_FRAGS) for s in sp)

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "ALL"
    max_recs = int(sys.argv[2]) if len(sys.argv) > 2 else 45
    max_chars = int(sys.argv[3]) if len(sys.argv) > 3 else 1800
    if arg.upper() == "ALL":
        names = sorted(os.path.splitext(os.path.basename(f))[0]
                       for f in glob.glob(os.path.join(EXTRACT, "*.json")))
    else:
        names = [n.strip() for n in arg.split(",") if n.strip()]

    plan = []
    summary = []
    for name in names:
        path = os.path.join(EXTRACT, name + ".json")
        if not os.path.exists(path):
            continue
        recs = json.load(open(path, encoding="utf-8"))
        tr = [r for r in recs if jp_spans(r) and r.get("confidence", 1.0) >= 0.5
              and not is_font_record(r)]
        if not tr:
            continue
        cur, cur_chars, fc = [], 0, 0
        def flush():
            nonlocal cur, cur_chars, fc
            if not cur:
                return
            s, e = cur[0]["id"], cur[-1]["id"]
            in_items = [{"id": r["id"], "spans": jp_spans(r)} for r in cur]
            in_path = os.path.join(CHUNKDIR, f"{name}__{s}_{e}.in.json")
            json.dump(in_items, open(in_path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=0)
            plan.append({
                "name": name, "start_id": s, "end_id": e,
                "n": len(cur), "jp_chars": cur_chars,
                "in_path": in_path,
                "out_path": os.path.join(PARTDIR, f"{name}__{s}_{e}.json"),
            })
            fc += 1
            cur, cur_chars = [], 0
        for r in tr:
            c = sum(len(x) for x in jp_spans(r))
            if cur and (len(cur) >= max_recs or cur_chars + c > max_chars):
                flush()
            cur.append(r); cur_chars += c
        flush()
        summary.append((name, len(tr), fc))

    json.dump(plan, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # compact args for the Workflow (name/start/end only)
    args = [{"name": c["name"], "start_id": c["start_id"], "end_id": c["end_id"]} for c in plan]
    json.dump(args, open(r"E:\game\_work\chunk_args.json", "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    log = io.open(r"E:\game\_work\plan_out.txt", "w", encoding="utf-8")
    for name, fr, fc in summary:
        log.write(f"  {name:14} records={fr:5} chunks={fc}\n")
    log.write(f"TOTAL records={sum(s[1] for s in summary)}, chunks={len(plan)}\n")
    log.close()
    print("done; chunks=", len(plan))

if __name__ == "__main__":
    main()
