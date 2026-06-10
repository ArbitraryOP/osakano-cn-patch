import io, sys, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\volume_out.txt","w",encoding="utf-8")
EXE = r"E:\game\jp\osakano.exe"
raw = open(EXE,"rb").read()
pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
base = pe.OPTIONAL_HEADER.ImageBase
secs=[(s.Name.rstrip(b"\x00").decode("latin1"), s.PointerToRawData, s.SizeOfRawData, base+s.VirtualAddress, s.Misc_VirtualSize) for s in pe.sections]
def off2va(o):
    for n,ro,rs,va0,vs in secs:
        if ro<=o<ro+rs: return va0+(o-ro)
def va2off(va):
    for n,ro,rs,va0,vs in secs:
        if va0<=va<va0+vs:
            o=ro+(va-va0)
            if o<ro+rs: return o
text=[s for s in secs if s[0]=='.text'][0]
tb=raw[text[1]:text[1]+text[2]]; tva=text[3]
md=Cs(CS_ARCH_X86,CS_MODE_32)

# 1) find the volume value-name ASCII strings
names=["TotalVolume","MusicVolume","VoiceVolume","SEVolume","Music"]
vas={}
for nm in names:
    b=nm.encode()+b"\x00"
    i=raw.find(b)
    if i>=0:
        vas[nm]=off2va(i); print(f"{nm:12} VA 0x{vas[nm]:08X} file 0x{i:06X}")
    else: print(f"{nm:12} NOT FOUND")

# 2) audio APIs imported?
imps={}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll=e.dll.decode().lower()
    for imp in e.imports:
        if imp.name:
            n=imp.name.decode()
            if any(k in n for k in ("waveOut","DirectSound","RegQueryValueEx","RegSetValueEx","mciSend","SetVolume")):
                imps[n]=imp.address
print("\naudio/reg imports:", {k:hex(v) for k,v in imps.items()})

def find_pushes(va):
    needle=b'\x68'+struct.pack('<I',va); i=0; hits=[]
    while True:
        j=tb.find(needle,i)
        if j<0: break
        hits.append(tva+j); i=j+1
    return hits

# 3) disasm around each volume name push (the RegQueryValueEx read site -> shows default + clamp)
for nm in ("TotalVolume","MusicVolume","VoiceVolume","SEVolume"):
    if nm not in vas: continue
    for site in find_pushes(vas[nm])[:1]:
        o=va2off(site)-text[1]
        print(f"\n=== {nm} pushed @ 0x{site:08X} (context) ===")
        for ins in md.disasm(tb[o-0x30:o+0x70], site-0x30):
            print(f"   0x{ins.address:08X}: {ins.mnemonic} {ins.op_str}")
        break
print("\ndone")
