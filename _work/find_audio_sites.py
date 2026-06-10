import io, sys, json, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\audio_sites_out.txt","w",encoding="utf-8")
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

# IAT addresses of interest
iat={}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in e.imports:
        if imp.name:
            n=imp.name.decode()
            if n.startswith("waveOut") or n in ("mciSendCommandA","mciSendStringA","RegQueryValueExA","RegSetValueExA","auxGetNumDevs","auxSetVolume"):
                iat[n]=imp.address

# volume value-name strings
names={"TotalVolume":None,"MusicVolume":None,"VoiceVolume":None,"SEVolume":None,"Music":None,
       "MusicInstall":None,"VoiceInstall":None}
for nm in list(names):
    i=raw.find(nm.encode()+b"\x00")
    names[nm]=off2va(i) if i>=0 else None

def immrefs(va):
    """all positions in .text where the 4-byte LE value `va` appears (push/mov/lea/call[mem])."""
    needle=struct.pack('<I',va); res=[]; i=0
    while True:
        j=tb.find(needle,i)
        if j<0: break
        res.append(j); i=j+1
    return res

sites=[]
# IAT call sites (FF15 / FF25 just before the slot addr)
for n,addr in iat.items():
    for j in immrefs(addr):
        va=tva+j
        pre = tb[j-2:j]
        kind = "call" if pre==b'\xff\x15' else ("jmp" if pre==b'\xff\x25' else "ref")
        if kind in ("call","jmp"):
            sites.append({"api":n,"kind":kind,"va":f"0x{va-2:08X}","file":f"0x{va2off(va-2):06X}"})
# volume name references
for nm,va in names.items():
    if va is None: continue
    for j in immrefs(va):
        site=tva+j
        sites.append({"api":f"strref:{nm}","kind":"ref","va":f"0x{site:08X}","file":f"0x{va2off(site):06X}"})

print(f"total audio sites: {len(sites)}")
from collections import Counter
c=Counter(s["api"] for s in sites)
for k,v in c.most_common(): print(f"  {k}: {v}")
json.dump(sites, open(r"E:\game\_work\audio_sites.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nwrote audio_sites.json")
