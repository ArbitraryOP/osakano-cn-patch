import sys, io, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\callers_out.txt", "w", encoding="utf-8")
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
    if 'dword ptr [0x' in ins.op_str:
        try:
            imm=int(ins.op_str.split('[')[1].split(']')[0],16)
            if imm in iat: out.append('IMP:'+iat[imm])
        except: pass
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
# find direct CALL rel32 (E8) to target
def call_sites(target):
    res=[]
    for i in range(len(tb)-5):
        if tb[i]==0xE8:
            rel=int.from_bytes(tb[i+1:i+5],'little',signed=True)
            dst=(tva+i+5+rel)&0xffffffff
            if dst==target: res.append(tva+i)
    return res
for fn in (0x458210, 0x4547e0):
    cs=call_sites(fn)
    print(f"\n##### CALL 0x{fn:08X} sites: {[hex(c) for c in cs]} #####")
    for c in cs[:6]:
        print(f"  --- caller context @0x{c:08X} ---")
        o=va2off(c-0x50)
        for ins in md.disasm(raw[o:o+0x58], c-0x50):
            m=' <==' if ins.address==c else ''
            print(f"    0x{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{ann(ins)}{m}")
print("done")
