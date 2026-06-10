"""Generate repair chunk inputs for records that overflowed (reverted to JP).
Reads overflow.json (written by integrate.py) + extract/<name>.json.
For each overflow record, emits its jp spans with a strict per-span char budget
 = floor(cp932_byte_len / 2)  (each Chinese char costs 2 GBK bytes).
Writes chunks/repair_<name>__<s>_<e>.in.json = [{id, spans:[{jp, max}]}]
and chunk_args.json (compact) for the repair workflow.
"""
import json, os, io

EXTRACT = r"E:\game\_work\extract"
CHUNKDIR = r"E:\game\_work\chunks"
OVER = r"E:\game\_work\overflow.json"
os.makedirs(CHUNKDIR, exist_ok=True)

def jp_spans(rec):
    return [t["s"] for t in rec["tokens"] if t["t"] == "jp"]

def main():
    overflow = json.load(open(OVER, encoding="utf-8")) if os.path.exists(OVER) else {}
    args = []
    total = 0
    MAXN = 80
    for name, ids in overflow.items():
        recs = {r["id"]: r for r in json.load(open(os.path.join(EXTRACT, name + ".json"), encoding="utf-8"))}
        allitems = []
        for rid in sorted(set(ids)):
            rec = recs.get(rid)
            if not rec:
                continue
            spans = []
            for t in rec["tokens"]:
                if t["t"] == "jp":
                    blen = len(t["s"].encode("cp932", "replace"))
                    spans.append({"jp": t["s"], "max": max(1, blen // 2)})
            if spans:
                allitems.append({"id": rid, "spans": spans})
        # split into chunks of <= MAXN
        for c in range(0, len(allitems), MAXN):
            items = allitems[c:c + MAXN]
            s, e = items[0]["id"], items[-1]["id"]
            path = os.path.join(CHUNKDIR, f"repair_{name}__{s}_{e}.in.json")
            json.dump(items, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
            args.append({"name": "repair_" + name, "start_id": s, "end_id": e, "tgt": name})
            total += len(items)
    json.dump(args, open(r"E:\game\_work\repair_args.json", "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    log = io.open(r"E:\game\_work\repair_plan_out.txt", "w", encoding="utf-8")
    log.write(f"repair files: {len(args)}, records: {total}\n")
    for a in args:
        log.write(f"  {a['name']} {a['start_id']}-{a['end_id']}\n")
    log.close()
    print(f"repair plan: {len(args)} files, {total} records")

if __name__ == "__main__":
    main()
