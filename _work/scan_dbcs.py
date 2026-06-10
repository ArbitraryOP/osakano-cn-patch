import io, sys, re, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\dbcs_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE, "rb").read()
text = [s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text"][0]
tb = raw[text.PointerToRawData:text.PointerToRawData + text.SizeOfRawData]
tva = base + text.VirtualAddress
toff = text.PointerToRawData

def va2off(va):
    return toff + (va - tva)

md = Cs(CS_ARCH_X86, CS_MODE_32)
insns = list(md.disasm(tb, tva))

def imm_of(op_str):
    m = re.search(r"0x([0-9a-fA-F]+)$", op_str)
    return int(m.group(1), 16) if m else None

# Find SJIS lead-byte range checks: a cmp/sub with imm 0x81 near a cmp with 0xE0/0x9F/0xFC/0xA0
found = 0
for k, ins in enumerate(insns):
    if ins.mnemonic in ("cmp", "sub", "add") and imm_of(ins.op_str) == 0x81:
        window = insns[k:k + 16]
        vals = {}
        for w in window:
            vv = imm_of(w.op_str)
            if vv is not None:
                vals.setdefault(vv, w.address)
        if any(x in vals for x in (0xE0, 0x9F, 0xA0, 0xFC, 0xFD)):
            found += 1
            off = va2off(ins.address)
            print(f"=== SJIS-lead check #{found} @ VA 0x{ins.address:08X} (file 0x{off:06X}) ===")
            print(f"    immediates seen: {sorted('0x%X'%x for x in vals)}")
            for w in window:
                vv = imm_of(w.op_str)
                mark = " <<<" if (vv in (0x81,0x9F,0xA0,0xE0,0xFC,0xFD)) else ""
                wo = va2off(w.address)
                # raw bytes of this insn
                rb = tb[wo-toff:wo-toff+w.size].hex()
                print(f"    0x{w.address:08X} (f0x{wo:06X}) {rb:<14} {w.mnemonic} {w.op_str}{mark}")
            print()

print(f"\nTotal SJIS-lead-style checks found: {found}")

# Also: any references to imports IsDBCSLeadByte / MultiByteToWideChar / _ismbblead
imps = []
try:
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
    for e in pe.DIRECTORY_ENTRY_IMPORT:
        dll = e.dll.decode()
        for imp in e.imports:
            if imp.name and any(s in imp.name.decode() for s in ("DBCS","MultiByte","mbb","mbc","WideChar")):
                imps.append((dll, imp.name.decode(), imp.address))
except Exception as ex:
    print("import parse err", ex)
print("\nrelevant imports:")
for d,n,a in imps:
    print(f"  {d}!{n} @ IAT 0x{a:08X}")
print("done")
