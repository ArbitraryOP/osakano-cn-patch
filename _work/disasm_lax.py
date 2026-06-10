import sys, io, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

sys.stdout = io.open(r"E:\game\_work\disasm_lax_out.txt", "w", encoding="utf-8")
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
iatname={}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll=e.dll.decode()
    for imp in e.imports:
        if imp.name: iatname[imp.address]=f"{dll[:8]}!{imp.name.decode()}"
def str_at(va):
    o=va2off(va)
    if o is None: return None
    b=raw[o:o+48]; end=b.find(b'\x00')
    if end<=0: return None
    bb=b[:end]
    if all(32<=c<127 for c in bb): return bb.decode('ascii')
    try:
        s=bb.decode('cp932')
        if all(ord(c)>=0x20 for c in s): return s
    except: pass
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32)
def ann(ins):
    notes=[]
    if 'dword ptr [0x' in ins.op_str:
        try:
            imm=int(ins.op_str.split('[')[1].split(']')[0],16)
            if imm in iatname: notes.append('IMPORT '+iatname[imm])
        except: pass
    for tok in ins.op_str.replace(',',' ').replace('[',' ').replace(']',' ').replace('+',' ').replace('*',' ').split():
        if tok.startswith('0x'):
            try: v=int(tok,16)
            except: continue
            if 0x480000<=v<0x4d0000:
                s=str_at(v)
                if s: notes.append(f'"{s}"')
    return '  ; '+' '.join(notes) if notes else ''
def disasm(start, count=160, label=""):
    print(f"\n========== {label} 0x{start:08X} ==========")
    o=va2off(start)
    if o is None: print("  <bad>"); return
    code=raw[o:o+count*7]; n=0
    for ins in md.disasm(code, start):
        print(f"  0x{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{ann(ins)}")
        n+=1
        if n>=count: break
        if ins.mnemonic=='ret': break

disasm(0x457030, 120, "alloc/decompress? 0x457030")
disasm(0x458690, 120, "archive dir parse 0x458690")
disasm(0x458710, 80, "0x458710")
# the function containing 0x454890 : scan back for prologue (push ebp; mov ebp,esp OR sub esp)
disasm(0x454820, 140, "archive open region 0x454820")
print("done")
