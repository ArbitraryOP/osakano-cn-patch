import io, sys, re, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\scan2_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE, "rb").read()
text = [s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text"][0]
tb = raw[text.PointerToRawData:text.PointerToRawData + text.SizeOfRawData]
tva = base + text.VirtualAddress
toff = text.PointerToRawData
TARGET = 0x0045C500

# 1) Find E8 rel32 callers of TARGET
print(f"=== callers of IsSJISLead 0x{TARGET:08X} ===")
callers = []
for i in range(len(tb) - 5):
    if tb[i] == 0xE8:
        rel = struct.unpack_from("<i", tb, i + 1)[0]
        if (tva + i + 5 + rel) & 0xFFFFFFFF == TARGET:
            callers.append(tva + i)
print(f"  {len(callers)} direct calls:", [hex(x) for x in callers])

# 2) Scan for OTHER lead-byte idioms we might have missed
md = Cs(CS_ARCH_X86, CS_MODE_32)
insns = list(md.disasm(tb, tva))
def imm_of(op):
    m = re.search(r"0x([0-9a-fA-F]+)$", op); return int(m.group(1),16) if m else None

print("\n=== other potential lead-byte tests (cmp ?,0x81 clusters not at TARGET) ===")
for k, ins in enumerate(insns):
    if ins.mnemonic in ("cmp","sub","add","lea") and imm_of(ins.op_str) in (0x81,0x5E,0x1F,0x3F):
        win = insns[k:k+10]
        vals = {imm_of(w.op_str) for w in win}
        vals.discard(None)
        # SJIS signature bytes
        sig = vals & {0x81,0x9f,0xa0,0xe0,0xfc,0xfd,0x40,0x7f,0x5e,0x1f,0x3f,0x9e,0xdf}
        if {0x81} <= sig and len(sig) >= 2 and not (tva+0x0 and 0x45C4F0 <= ins.address <= 0x45C525):
            print(f"  @0x{ins.address:08X} sig={sorted('0x%X'%x for x in sig)}")
            for w in win[:6]:
                print(f"      0x{w.address:08X}: {w.mnemonic} {w.op_str}")
            print()

# 3) Show a couple caller contexts (to confirm it's text-walking code)
print("=== caller contexts (first 3) ===")
def off(va): return toff + (va - tva)
for c in callers[:3]:
    o = off(c) - toff
    print(f"--- around call @ 0x{c:08X} ---")
    for ins in md.disasm(tb[o-0x18:o+0x10], c-0x18):
        mk = " <== call" if ins.address == c else ""
        print(f"    0x{ins.address:08X}: {ins.mnemonic} {ins.op_str}{mk}")
    print()
print("done")
