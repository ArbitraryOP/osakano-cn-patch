import sys, io, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\decomp_out.txt", "w", encoding="utf-8")
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
md=Cs(CS_ARCH_X86,CS_MODE_32)
def ann(ins):
    if 'dword ptr [0x' in ins.op_str:
        try:
            imm=int(ins.op_str.split('[')[1].split(']')[0],16)
            if imm in iat: return '  ; IMPORT '+iat[imm]
        except: pass
    return ''
def disasm(start, count=220, label=""):
    print(f"\n========== {label} 0x{start:08X} ==========")
    o=va2off(start)
    code=raw[o:o+count*7]; n=0
    for ins in md.disasm(code, start):
        print(f"  0x{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{ann(ins)}")
        n+=1
        if n>=count: break
        if ins.mnemonic=='ret': break
disasm(0x4432c0, 260, "DECOMPRESS 0x4432c0")
disasm(0x456f90, 40, "alloc 0x456f90")
print("done")
