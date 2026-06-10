import io, sys
sys.stdout = io.open(r"E:\game\_work\decode_err_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
raw = open(EXE, "rb").read()

def is_kana_kanji(s):
    return any('぀'<=c<='ヿ' or '一'<=c<='鿿' for c in s)

# rebuild the same candidate list, then show GBK-misread (what shows on a CN system)
i=0; N=len(raw); cands=[]
while i<N:
    j=raw.find(b"\x00", i)
    if j<0: break
    run=raw[i:j]
    if 4<=len(run)<=220:
        try:
            s=run.decode("cp932")
            if is_kana_kanji(s) and ("\n" in s or s.endswith("？") or "はい" in s or "ＯＳ" in s):
                # GBK misread = encode original bytes, decode cp936
                gbk = run.decode("cp936","replace")
                cands.append((i,s,gbk))
        except Exception:
            pass
    i=j+1

# the on-screen body started with these GBK chars:
needle = "借"
for off,s,gbk in cands:
    mark = "  <<<<< MATCH" if gbk.startswith(needle) or needle in gbk[:4] else ""
    print(f"0x{off:06X}")
    print(f"   JP : {s.replace(chr(10),' / ')}")
    print(f"   GBK: {gbk.replace(chr(10),' / ')}{mark}")
    print()
