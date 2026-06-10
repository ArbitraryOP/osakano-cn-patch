import sys, io, struct, re
sys.stdout = io.open(r"E:\game\_work\te_out.txt", "w", encoding="utf-8")

def analyze(path, label):
    data = open(path,'rb').read()
    print(f"\n################ {label}: {path}  ({len(data)} bytes) ################")
    print("magic:", data[:8])
    # header dwords after magic
    hdr = struct.unpack_from('<8I', data, 8)
    print("hdr dwords @8:", [hex(x) for x in hdr])
    # find SJIS string runs (>=2 dbcs chars), report offset + the byte just before
    sjis_re = re.compile(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc])+')
    runs=[]
    for m in sjis_re.finditer(data):
        try: s=m.group().decode('cp932')
        except: continue
        if len(s)>=2:
            runs.append((m.start(), m.end(), s))
    print(f"SJIS runs: {len(runs)}")
    # show first 25 runs with context bytes
    for st,en,s in runs[:25]:
        pre = data[max(0,st-4):st].hex(' ')
        post = data[en:en+2].hex(' ')
        print(f"  off=0x{st:06X} len={en-st:3} pre=[{pre}] post=[{post}]  {s[:40]!r}")
    return data, runs

analyze(r"E:\game\幼なじみな彼女\sena\sce\system.te", "system.te")
d,runs = analyze(r"E:\game\幼なじみな彼女\sena\sce\op.te", "op.te")
analyze(r"E:\game\幼なじみな彼女\sena\sce\zakki.te", "zakki.te")

# For op.te: dump a hex+sjis window around the first few text runs to see record structure
print("\n\n===== op.te windows around first text runs =====")
import codecs
for st,en,s in runs[:6]:
    a=max(0,st-16); b=min(len(d), en+8)
    print(f"\n-- run off 0x{st:06X} {s[:30]!r} --")
    for i in range(a,b,16):
        chunk=d[i:i+16]
        hx=' '.join(f'{x:02X}' for x in chunk)
        print(f"  {i:06X}: {hx}")
print("done")
