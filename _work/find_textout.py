import sys, io, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\textout_out.txt", "w", encoding="utf-8")
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
# IAT slots of interest
slots = {}
for a,n in iat.items():
    if n in ('TextOutA','ExtTextOutA','GetGlyphOutlineA','GetGlyphOutlineW','GetTextExtentPoint32A','CreateFontIndirectA','SetDIBitsToDevice','CreateDIBSection','GetCharABCWidthsA','PolyTextOutA'):
        slots[n]=a
print("relevant GDI IAT slots:", {k:hex(v) for k,v in slots.items()})
text=[s for s in sections if s[0]=='.text'][0]
tb=raw[text[1]:text[1]+text[2]]; tva=text[3]
# count call/jmp [slot] (FF15/FF25) for each
import struct
def refs(slot):
    needle=slot.to_bytes(4,'little'); r=[]; i=0
    while True:
        j=tb.find(needle,i)
        if j<0: break
        if j>=2 and tb[j-2]==0xFF and tb[j-1] in (0x15,0x25): r.append(('FFcalljmp',tva+(j-2)))
        i=j+1
    return r
for n,a in slots.items():
    rr=refs(a)
    print(f"{n}: {len(rr)} direct call/jmp sites: {[hex(x[1]) for x in rr]}")
# Also find callers of the TextOutA thunk 0x4672b0 (jmp [TextOutA]) -> E8 rel32 calls to it
def callers_of(target):
    res=[]
    for i in range(len(tb)-5):
        if tb[i]==0xE8:
            rel=struct.unpack_from('<i', tb, i+1)[0]
            if (tva+i+5+rel)&0xffffffff==target: res.append(tva+i)
    return res
print("\ncallers of TextOutA thunk 0x4672b0:", [hex(x) for x in callers_of(0x4672b0)])
md=Cs(CS_ARCH_X86,CS_MODE_32)
# disasm around the TextOutA call site(s)
for n,a in slots.items():
    for _,site in refs(a):
        print(f"\n--- context @ {n} call 0x{site:08X} ---")
        o=va2off(site-0x40)
        for ins in md.disasm(raw[o:o+0x48], site-0x40):
            m=' <==' if ins.address==site else ''
            print(f"  0x{ins.address:08X}: {ins.mnemonic:7} {ins.op_str}{m}")
        break  # one per function
print("done")
