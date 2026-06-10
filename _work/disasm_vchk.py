import sys, io, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\vchk_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
pe = pefile.PE(EXE, fast_load=True); pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
base = pe.OPTIONAL_HEADER.ImageBase; raw = open(EXE,'rb').read()
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
    b=raw[o:o+64]; end=b.find(b'\x00')
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
            s=str_at(v)
            if s: out.append(f'"{s}"')
    return '  ; '+' '.join(out) if out else ''
o=va2off(0x440790)
for ins in md.disasm(raw[o:o+0x190], 0x440790):
    print(f"  0x{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{ann(ins)}")
print("done")
