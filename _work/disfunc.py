import sys, io, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

sys.stdout = io.open(r"E:\game\_work\disfunc_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
base = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE,'rb').read()

sections=[]
for s in pe.sections:
    sections.append((s.Name.rstrip(b'\x00').decode('latin1'), s.PointerToRawData, s.SizeOfRawData, base+s.VirtualAddress, s.Misc_VirtualSize))

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

# IAT map: VA of slot -> name
iatname={}
if hasattr(pe,'DIRECTORY_ENTRY_IMPORT'):
    for e in pe.DIRECTORY_ENTRY_IMPORT:
        dll=e.dll.decode()
        for imp in e.imports:
            if imp.name:
                iatname[imp.address]=f"{dll}!{imp.name.decode()}"

# crude string lookup at a VA (ascii or sjis)
def str_at(va):
    o=va2off(va)
    if o is None: return None
    b=raw[o:o+64]
    end=b.find(b'\x00')
    if end<=0: return None
    bb=b[:end]
    if all(32<=c<127 for c in bb):
        return bb.decode('ascii')
    try:
        s=bb.decode('cp932')
        if all(ord(c)>=0x20 for c in s): return s
    except: pass
    return None

md=Cs(CS_ARCH_X86,CS_MODE_32)
md.detail=False

def annotate(ins):
    notes=[]
    # call/jmp to absolute imm
    if ins.mnemonic in ('call','jmp') and ins.op_str.startswith('0x'):
        tgt=int(ins.op_str,16)
        # nothing
    # call dword ptr [imm] -> IAT
    if 'dword ptr [0x' in ins.op_str:
        try:
            imm=int(ins.op_str.split('[')[1].split(']')[0],16)
            if imm in iatname: notes.append('IMPORT '+iatname[imm])
        except: pass
    # immediate that is a string VA
    for tok in ins.op_str.replace(',',' ').split():
        if tok.startswith('0x'):
            try: v=int(tok,16)
            except: continue
            if 0x480000<=v<0x4d0000:
                s=str_at(v)
                if s: notes.append(f'"{s}"')
    return '  ; '+' '.join(notes) if notes else ''

def disasm(start, count=140, label=""):
    print(f"\n========== {label} func 0x{start:08X} ==========")
    o=va2off(start)
    if o is None:
        print("  <bad va>"); return
    code=raw[o:o+count*6]
    n=0
    for ins in md.disasm(code, start):
        print(f"  0x{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{annotate(ins)}")
        n+=1
        if n>=count: break
        if ins.mnemonic=='ret': break

# Find all CALL sites to a given IAT slot va, print address
def callsites_to_iat(slot_va):
    needle=slot_va.to_bytes(4,'little')
    res=[]
    for n,ro,rs,va0,vs in sections:
        if n!='.text': continue
        seg=raw[ro:ro+rs]
        i=0
        while True:
            j=seg.find(needle,i)
            if j<0: break
            # check if preceded by FF 15 (call) or FF 25 (jmp)
            if j>=2 and seg[j-2]==0xFF and seg[j-1] in (0x15,0x25):
                res.append(va0+(j-2))
            i=j+1
    return res

targets=[
 (0x4408f0,"LOADFILE(sce\\%s.te caller)"),
 (0x461d80,"FONT_BUILD_A"),
 (0x444510,"FONT_SETUP"),
 (0x454890,"LAX_OPEN/$LapH check"),
]
for va,lbl in targets:
    disasm(va,160,lbl)

print("\n\n###### CreateFontIndirectA call sites ######")
for cs in callsites_to_iat(0x522948):
    print(f"\n--- callsite 0x{cs:08X} (disasm 60 ins before) ---")
    o=va2off(cs-0x90)
    code=raw[o:o+0x90+8]
    for ins in md.disasm(code, cs-0x90):
        mark=' <== CALL' if ins.address==cs else ''
        print(f"  0x{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{annotate(ins)}{mark}")

print("\n\n###### MultiByteToWideChar call sites (check codepage arg) ######")
for cs in callsites_to_iat(0x522BA0):
    print(f"\n--- callsite 0x{cs:08X} ---")
    o=va2off(cs-0x40)
    code=raw[o:o+0x40+8]
    for ins in md.disasm(code, cs-0x40):
        mark=' <== CALL' if ins.address==cs else ''
        print(f"  0x{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{annotate(ins)}{mark}")

print("done")
