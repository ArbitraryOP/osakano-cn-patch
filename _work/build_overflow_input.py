import io, sys, json, os
sys.stdout = io.open(r"E:\game\_work\build_overflow_out.txt", "w", encoding="utf-8")
W = r"E:\game\_work"
ov = json.load(open(os.path.join(W,"overflow.json"), encoding="utf-8"))

def cp932len(s):
    try: return len(s.encode("cp932"))
    except Exception: return None
def cp936len(s):
    try: return len(s.encode("cp936"))
    except Exception: return None

OUT = os.path.join(W,"overflow_chunks")
os.makedirs(OUT, exist_ok=True)
manifest=[]; total=0; chunkno=0; CHUNK=12
cur=[]
def flush():
    global chunkno, cur
    if not cur: return
    name=f"ovchunk_{chunkno:02d}.json"
    json.dump(cur, open(os.path.join(OUT,name),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    manifest.append({"file":name,"count":len(cur)})
    chunkno+=1; cur=[]

for te, ids in ov.items():
    ex_path=os.path.join(W,"extract",f"{te}.json")
    tr_path=os.path.join(W,"translated",f"{te}.json")
    if not os.path.exists(ex_path) or not os.path.exists(tr_path):
        print(f"[skip te] {te}: missing extract/translated"); continue
    ex={r["id"]:r for r in json.load(open(ex_path,encoding="utf-8"))}
    tr={r["id"]:r for r in json.load(open(tr_path,encoding="utf-8"))}
    for rid in ids:
        rec=ex.get(rid)
        if rec is None: print(f"[skip] {te}#{rid}: no extract rec"); continue
        jp_toks=[t["s"] for t in rec["tokens"] if t["t"]=="jp"]
        budgets=[cp932len(s) for s in jp_toks]
        total_budget=sum(b for b in budgets if b)
        cur_zh=(tr.get(rid) or {}).get("zh_spans", [])
        per=[cp936len(s) for s in cur_zh]
        gbk_ok=all(p is not None for p in per)
        cur_bytes=sum(p for p in per if p) if gbk_ok else None
        # find non-GBK chars in current zh (the likely overflow cause)
        bad_chars=sorted({c for s in cur_zh for c in s if cp936len(c) is None})
        # neighbor context
        prev_jp=(ex.get(rid-1) or {}).get("jp","")
        next_jp=(ex.get(rid+1) or {}).get("jp","")
        cur.append({
            "te":te, "id":rid,
            "full_jp":rec["jp"],
            "jp_spans":jp_toks,
            "span_budgets_cp932":budgets,
            "total_budget_cp932":total_budget,
            "current_zh_spans":cur_zh,
            "current_zh_cp936_bytes":cur_bytes,
            "current_zh_gbk_ok":gbk_ok,
            "non_gbk_chars":bad_chars,
            "over_by_bytes":(cur_bytes-total_budget) if cur_bytes is not None else None,
            "context_prev_jp":prev_jp,
            "context_next_jp":next_jp,
        })
        total+=1
        if len(cur)>=CHUNK: flush()
flush()
json.dump(manifest, open(os.path.join(OUT,"manifest.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"built {total} overflow records into {chunkno} chunks under overflow_chunks/")
for m in manifest: print(" ", m)
