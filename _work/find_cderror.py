import io, sys, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\cderror_out.txt","w",encoding="utf-8")
EXE = r"E:\game\jp\osakano.exe"
raw = open(EXE,"rb").read()
pe = pefile.PE(EXE, fast_load=True)
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

# 1) find the caption + related CD strings
targets = {
 "CD-drive-err-caption":"ＣＤドライブのエラー",
 "CD-audio-err-caption":"ＣＤオーディオのエラー",
 "not-music-cd":"音楽ＣＤではない",
}
vas={}
for name,s in targets.items():
    b=s.encode("cp932")
    i=raw.find(b)
    if i>=0:
        va=off2va(i); vas[name]=va
        print(f"{name}: file 0x{i:06X} VA 0x{va:08X}  {s}")
    else:
        print(f"{name}: NOT FOUND")

# 2) for each found string VA, find push imm32 (68 <va>) sites in .text
print("\n=== push sites (caption usage) ===")
for name,va in vas.items():
    needle=b'\x68'+struct.pack('<I',va)
    i=0; hits=[]
    while True:
        j=tb.find(needle,i)
        if j<0: break
        hits.append(tva+j); i=j+1
    print(f"{name} VA0x{va:08X} pushed at {[hex(x) for x in hits]}")
    # disasm context around each push (back up to find the MessageBoxA + the branch)
    for site in hits:
        o=va2off(site)-text[1]
        print(f"  --- context @ 0x{site:08X} ---")
        for ins in md.disasm(tb[o-0x60:o+0x40], site-0x60):
            mk=""
            if ins.mnemonic in ('call',) and 'MessageBox' in (ins.op_str or ''): mk=' <-MsgBox'
            print(f"     0x{ins.address:08X}: {ins.bytes.hex():<12} {ins.mnemonic} {ins.op_str}")
        print()
print("done")
