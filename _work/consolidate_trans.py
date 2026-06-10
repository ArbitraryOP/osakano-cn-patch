import io, sys, json
sys.stdout = io.open(r"E:\game\_work\consolidate_trans_out.txt","w",encoding="utf-8")
OUT = r"C:\Users\63532\AppData\Local\Temp\claude\E--game\24fbcc89-5d38-463c-a6d1-1b2518e914a1\tasks\wpt1k4amq.output"
res = json.load(open(OUT, encoding="utf-8"))["result"]
items = []
for key in ("transA","transB","transC","remainingScan"):
    for it in res[key]["items"]:
        off = it["file_offset_hex"]
        if not off.lower().startswith("0x"): off = "0x"+off
        items.append({"file_offset_hex":off, "jp":it["jp"], "zh":it["zh"], "src":key})
# de-dup by offset (keep first)
seen=set(); uniq=[]
for it in items:
    o=int(it["file_offset_hex"],16)
    if o in seen:
        print(f"dup offset {it['file_offset_hex']} ({it['src']}) skipped"); continue
    seen.add(o); uniq.append(it)
json.dump(uniq, open(r"E:\game\_work\pending_trans.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"wrote {len(uniq)} translation entries to pending_trans.json")
for it in uniq: print(f"  {it['file_offset_hex']:>10}  {it['src']:<13} {it['zh'][:30]!r}")
