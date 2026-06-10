import sys, io, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\voice_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
base = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE,'rb').read()
sections=[(s.Name.rstrip(b'\x00').decode('latin1'), s.PointerToRawData, s.SizeOfRawData, base+s.VirtualAddress, s.Misc_VirtualSize) for s in pe.sections]
def va2off(va):
    for n,ro,rs,va0,vs in sections:
        if va0<=va<va0+vs:
            o=ro+(va-va0)
            if o<ro+rs: return o
    return None
def off2va(off):
    for n,ro,rs,va0,vs in sections:
        if ro<=off<ro+rs: return va0+(off-ro)
    return None
iat={}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in e.imports:
        if imp.name: iat[imp.address]=imp.name.decode()
def str_at(va):
    o=va2off(va)
    if o is None: return None
    b=raw[o:o+80]; end=b.find(b'\x00')
    if end<=0: return None
    bb=b[:end]
    if all(32<=c<127 for c in bb): return bb.decode('ascii')
    try:
        s=bb.decode('cp932')
        if all(0x20<=ord(c) for c in s): return s
    except: pass
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32)
def ann(ins):
    out=[]
    for tok in ins.op_str.replace(',',' ').replace('[',' ').replace(']',' ').replace('+',' ').replace('*',' ').split():
        if tok.startswith('0x'):
            try: v=int(tok,16)
            except: continue
            if v in iat: out.append('IMP:'+iat[v])
            s=str_at(v)
            if s: out.append(f'"{s}"')
    return '  ; '+' '.join(out) if out else ''
text=[s for s in sections if s[0]=='.text'][0]
tb=raw[text[1]:text[1]+text[2]]; tva=text[3]
def find_refs(va):
    needle=va.to_bytes(4,'little'); r=[]; i=0
    while True:
        j=tb.find(needle,i)
        if j<0: break
        r.append(tva+j); i=j+1
    return r
for nm,foff in [("gr24.lax",0x8B72C),("common.lax",0x8B7E4),("scenario.lax",0x8B7F4),("voice.lax",0x8B804)]:
    va=off2va(foff); refs=find_refs(va)
    print(f"\n##### {nm} VA=0x{va:08X} refs={[hex(r) for r in refs]} #####")
for nm,foff in [("voice.lax",0x8B804)]:
    va=off2va(foff)
    for r in find_refs(va):
        print(f"\n===== voice.lax ref @0x{r:08X} (wide) =====")
        o=va2off(r-0xa0)
        for ins in md.disasm(raw[o:o+0x140], r-0xa0):
            m=' <==' if ins.address==r else ''
            print(f"  0x{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{ann(ins)}{m}")
print("done")
