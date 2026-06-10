import io, sys, json, os, re
sys.stdout = io.open(r"E:\game\_work\build_defect_out.txt","w",encoding="utf-8")
W=r"E:\game\_work"
KANA=re.compile('[぀-ゟ゠-ヿ]')
def cp932(s):
    try: return len(s.encode("cp932"))
    except: return None
def cp936ok(s):
    try: s.encode("cp936"); return True
    except: return False

defects=json.load(open(os.path.join(W,"defects.json"),encoding="utf-8"))
overflow=json.load(open(os.path.join(W,"overflow.json"),encoding="utf-8"))
# unify: te -> set(ids)
uni={}
for te,ids in defects.items(): uni.setdefault(te,set()).update(ids)
for te,ids in overflow.items(): uni.setdefault(te,set()).update(ids)

OUT=os.path.join(W,"defect_chunks"); os.makedirs(OUT,exist_ok=True)
# clear old
for f in os.listdir(OUT):
    if f.endswith(".json"): os.remove(os.path.join(OUT,f))
manifest=[]; total=0; cur=[]; cn=0; CHUNK=10
def flush():
    global cn,cur
    if not cur: return
    name=f"dchunk_{cn:02d}.json"
    json.dump(cur,open(os.path.join(OUT,name),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    manifest.append({"file":name,"count":len(cur)}); cn+=1; cur=[]

for te in sorted(uni):
    exf=os.path.join(W,"extract",f"{te}.json"); trf=os.path.join(W,"translated",f"{te}.json")
    if not os.path.exists(exf) or not os.path.exists(trf): continue
    ex={r["id"]:r for r in json.load(open(exf,encoding="utf-8"))}
    tr={r["id"]:r for r in json.load(open(trf,encoding="utf-8"))}
    for rid in sorted(uni[te]):
        rec=ex.get(rid)
        if rec is None: continue
        jptoks=[t["s"] for t in rec["tokens"] if t["t"]=="jp"]
        if not jptoks: continue
        budgets=[cp932(s) for s in jptoks]
        cur_zh=(tr.get(rid) or {}).get("zh_spans")
        issues=[]
        if cur_zh is None: issues.append("untranslated")
        else:
            if len(cur_zh)!=len(jptoks): issues.append(f"span-count {len(cur_zh)}vs{len(jptoks)}")
            if any(KANA.search(s) for s in cur_zh): issues.append("kana-remains")
            if any(not cp936ok(s) for s in cur_zh): issues.append("non-gbk-char")
            if cur_zh and all(cp936ok(s) for s in cur_zh):
                tot=sum(len(s.encode('cp936')) for s in cur_zh)
                if tot>sum(b for b in budgets if b): issues.append(f"overflow +{tot-sum(b for b in budgets if b)}B")
        cur.append({
            "te":te,"id":rid,"full_jp":rec["jp"],
            "jp_spans":jptoks,"span_budgets_cp932":budgets,"total_budget_cp932":sum(b for b in budgets if b),
            "current_zh_spans":cur_zh,"issues":issues,
            "ctx_prev":(ex.get(rid-1) or {}).get("jp","")[:50],
            "ctx_next":(ex.get(rid+1) or {}).get("jp","")[:50],
        })
        total+=1
        if len(cur)>=CHUNK: flush()
flush()
json.dump(manifest,open(os.path.join(OUT,"manifest.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"unified {total} records into {cn} chunks")
print("manifest:", len(manifest), "chunks")
