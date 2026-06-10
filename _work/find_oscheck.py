import io, sys, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\oscheck_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
base = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE, "rb").read()
secs = [(s.Name.rstrip(b"\x00").decode("latin1"), s.PointerToRawData, s.SizeOfRawData, base+s.VirtualAddress, s.Misc_VirtualSize) for s in pe.sections]
def off2va(o):
    for n,ro,rs,va0,vs in secs:
        if ro<=o<ro+rs: return va0+(o-ro)
    return None
def va2off(va):
    for n,ro,rs,va0,vs in secs:
        if va0<=va<va0+vs:
            o=ro+(va-va0)
            if o<ro+rs: return o
    return None
text=[s for s in secs if s[0]=='.text'][0]
tb=raw[text[1]:text[1]+text[2]]; tva=text[3]
md=Cs(CS_ARCH_X86,CS_MODE_32)

# IAT slots for version / messagebox / CD APIs
iat={}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll=e.dll.decode()
    for imp in e.imports:
        if imp.name:
            iat[imp.name.decode()]=imp.address
want=['GetVersion','GetVersionExA','GetVersionExW','MessageBoxA','GetDriveTypeA','GetLogicalDrives','mciSendCommandA','mciSendStringA','auxGetNumDevs','waveOutGetNumDevs']
print("IAT slots:")
for w in want:
    if w in iat: print(f"  {w} @ 0x{iat[w]:08X}")

def find_calls(slot):
    needle=slot.to_bytes(4,'little'); res=[]; i=0
    while True:
        j=tb.find(needle,i)
        if j<0: break
        if j>=2 and tb[j-2]==0xFF and tb[j-1] in (0x15,0x25): res.append(tva+(j-2))
        i=j+1
    return res

for w in want:
    if w in iat:
        cs=find_calls(iat[w])
        if cs: print(f"\n{w}: call sites {[hex(x) for x in cs]}")

# refs (push imm32) to OS-warning string + CD strings (file offsets -> VA)
strs = {0x08C990:'OS_WARNING', 0x08B528:'CD_DA_OX', 0x08D060:'CD_RETRY', 0x08C310:'CD_RETRY2'}
print("\n--- string pushes ---")
for foff,name in strs.items():
    va=off2va(foff)
    needle=b'\x68'+struct.pack('<I',va)
    i=0; hits=[]
    while True:
        j=tb.find(needle,i)
        if j<0: break
        hits.append(tva+j); i=j+1
    print(f"{name} VA=0x{va:08X} pushed at {[hex(x) for x in hits]}")

# disasm around GetVersionExA call(s) to find the OS-warning branch
print("\n=== context around GetVersionExA / GetVersion ===")
for w in ('GetVersionExA','GetVersion'):
    if w in iat:
        for site in find_calls(iat[w]):
            o=va2off(site)-text[1]
            print(f"\n--- {w} @ 0x{site:08X} ---")
            for ins in md.disasm(tb[o-0x10:o+0x80], site-0x10):
                print(f"  0x{ins.address:08X}: {ins.mnemonic} {ins.op_str}")
print("\ndone")
