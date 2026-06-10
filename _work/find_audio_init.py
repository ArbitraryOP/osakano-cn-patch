import io, sys, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\audioinit_out.txt","w",encoding="utf-8")
EXE = r"E:\game\jp\osakano.exe"; raw=open(EXE,"rb").read()
pe=pefile.PE(EXE,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs=[(s.Name.rstrip(b"\x00").decode("latin1"),s.PointerToRawData,s.SizeOfRawData,base+s.VirtualAddress,s.Misc_VirtualSize) for s in pe.sections]
text=[s for s in secs if s[0]=='.text'][0]; tb=raw[text[1]:text[1]+text[2]]; tva=text[3]
md=Cs(CS_ARCH_X86,CS_MODE_32)
def sites(slot):
    needle=struct.pack('<I',slot); i=0; r=[]
    while True:
        j=tb.find(needle,i)
        if j<0: break
        if tb[j-2:j]==b'\xff\x15': r.append(tva+j-2)
        i=j+1
    return r
def aligned(target, back=0x70, fwd=0x30):
    for start in range(target-back, target-2):
        out=[]; ok=False
        for ins in md.disasm(tb[start-tva:start-tva+(target-start)+fwd], start):
            out.append(ins)
            if ins.address==target: ok=True
            if ins.address>=target+fwd: break
        if ok: return out
    return []
APIS={'waveOutGetNumDevs':0x522F38,'waveOutOpen':0x522F44,'waveOutWrite':0x522F30,'waveOutGetDevCapsA':0x522F3C}
for nm,slot in APIS.items():
    for s in sites(slot):
        print(f"\n===== {nm} @ 0x{s:08X} =====")
        for ins in aligned(s):
            tail = " <== CALL" if ins.address==s else ""
            print(f"   0x{ins.address:08X}: {ins.mnemonic} {ins.op_str}{tail}")
print("\ndone")
