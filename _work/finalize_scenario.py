"""Finalize the scenario: merge Phase-2b fixes -> rebuild built/ -> convert any
remaining untranslated SHIFT-JIS runs to GBK (equal-length, makes them render as
readable Japanese incl. the ？？？ speaker-name) -> repack scenario.lax.
Run AFTER the scenario-complete workflow writes defect_out/dout_*.json.
Usage: python finalize_scenario.py [--no-convert]
"""
import io, sys, json, os, glob, re, shutil
sys.path.insert(0, r"E:\game\_work\agentB")
sys.path.insert(0, r"E:\game\_work\agentA")
import te_text
sys.stdout = io.open(r"E:\game\_work\finalize_out.txt", "w", encoding="utf-8")
W=r"E:\game\_work"; TRDIR=f"{W}\\translated"; UNP=f"{W}\\unpacked"; BUILT=f"{W}\\built"; DOUT=f"{W}\\defect_out"
KANA=re.compile('[぀-ゟ゠-ヿ]')

def merge_phase2b():
    applied=0; tes=set(); bad=0
    for f in sorted(glob.glob(f"{DOUT}\\dout_*.json")):
        try: recs=json.load(open(f,encoding="utf-8"))
        except Exception as e: print(f"  [bad json] {os.path.basename(f)}: {e}"); bad+=1; continue
        bt={}
        for r in recs:
            try: bt.setdefault(r["te"],{})[int(r["id"])]=r["zh_spans"]
            except Exception: pass
        for te,idmap in bt.items():
            trf=f"{TRDIR}\\{te}.json"
            if not os.path.exists(trf): continue
            tr=json.load(open(trf,encoding="utf-8")); trd={r["id"]:r for r in tr}
            for rid,zh in idmap.items():
                if not isinstance(zh,list): continue
                trd[rid]={"id":rid,"zh_spans":zh}
            json.dump(sorted(trd.values(),key=lambda r:r["id"]), open(trf,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
            applied+=len(idmap); tes.add(te)
    print(f"merge_phase2b: applied {applied} records across {len(tes)} te files ({bad} bad files)")

def build_all():
    # ensure built/ has every original entry
    os.makedirs(BUILT, exist_ok=True)
    for src in glob.glob(f"{UNP}\\*"):
        dst=os.path.join(BUILT, os.path.basename(src))
        if not os.path.exists(dst): shutil.copy(src,dst)
    overflow={}
    for trf in sorted(glob.glob(f"{TRDIR}\\*.json")):
        te=os.path.splitext(os.path.basename(trf))[0]
        src=f"{UNP}\\{te}.te"
        if not os.path.exists(src): continue
        data=bytearray(open(src,"rb").read())
        records=te_text.extract(src)
        tr={r["id"]:r for r in json.load(open(trf,encoding="utf-8"))}
        rm=[]
        for idx,rec in enumerate(records):
            item=tr.get(idx)
            if item is None: continue
            spans=item.get("zh_spans",[]) or []
            tokens=rec["tokens"]; orig_raw=bytes.fromhex(rec["raw_bytes_hex"])
            jp_idx=[k for k,t in enumerate(tokens) if t["t"]=="jp"]
            jp_map={}
            for n,k in enumerate(jp_idx):
                if n<len(spans) and spans[n] is not None: jp_map[k]=spans[n]
            if not jp_map: continue
            try:
                new=te_text.build_run_bytes(orig_raw,tokens,jp_map,target_codec="cp936",rec_id=idx)
                data[rec["offset"]:rec["offset"]+len(new)]=new
            except ValueError: rm.append(idx)
        open(f"{BUILT}\\{te}.te","wb").write(data)
        if rm: overflow[te]=rm
    json.dump(overflow, open(f"{W}\\overflow2.json","w",encoding="utf-8"), ensure_ascii=False)
    print(f"build_all: rebuilt; residual overflow records={sum(len(v) for v in overflow.values())}")

def convert_untranslated():
    """Convert NUL-terminated data-section runs that are still byte-identical to the
    original (untranslated SHIFT-JIS) into GBK, equal-length, so they render as
    readable Japanese (kana/kanji/？ all exist in GB2312). Conservative: only runs
    whose cp932 decode is all-printable and contains a >=U+3000 char."""
    conv=0; kept=0
    for te_te in sorted(glob.glob(f"{BUILT}\\*.te")):
        te=os.path.splitext(os.path.basename(te_te))[0]
        srcp=f"{UNP}\\{te}.te"
        if not os.path.exists(srcp): continue
        orig=open(srcp,"rb").read(); built=bytearray(open(te_te,"rb").read())
        try: lo=te_text.parse_header(orig)["text_start"]
        except Exception: continue
        i=lo; n=len(built)
        while i<n:
            j=built.find(b"\x00", i)
            if j<0: break
            run=bytes(built[i:j])
            if 2<=len(run)<=300 and j<=len(orig) and run==orig[i:j]:
                try:
                    s=run.decode("cp932")
                    if all(ord(c)>=0x20 for c in s) and any(ord(c)>=0x3000 for c in s):
                        g=s.encode("cp936")
                        if len(g)==len(run):
                            built[i:j]=g; conv+=1
                        else: kept+=1
                except Exception: pass
            i=j+1
        open(te_te,"wb").write(built)
    print(f"convert_untranslated: converted {conv} runs to GBK; kept {kept} (len-mismatch/unencodable)")

def repack():
    import lax
    tmpl=r"E:\game\jp\scenario.lax.jp.bak"
    out=r"E:\game\_work\build\scenario.lax"
    r=lax.repack(BUILT, out, tmpl)
    print(f"repack: -> {out} ({r['size']} bytes, {r['count']} entries)")
    shutil.copy(out, r"E:\game\jp\scenario.lax")
    print("synced -> E:\\game\\jp\\scenario.lax")

if __name__=="__main__":
    merge_phase2b()
    build_all()
    if "--no-convert" not in sys.argv:
        convert_untranslated()
    repack()
    print("FINALIZE DONE")
