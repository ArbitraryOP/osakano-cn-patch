import io, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout = io.open(r"E:\game\_work\verify_render_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\jp\osakano.exe"
raw = open(EXE, "rb").read()
# .text: VA0x401000 raw0x1000 -> file = VA-0x400000 ; .data VA0x488000 raw0x88000 -> file=VA-0x400000 too here
def f(va): return va - 0x400000
md = Cs(CS_ARCH_X86, CS_MODE_32)

print("=== bodyPump 0x446E50 region (file 0x046E50..0x046F10) ===")
o = f(0x446E50)
for ins in md.disasm(raw[o:o+0xC0], 0x446E50):
    mk = ""
    if ins.address == 0x446EA7: mk = "   <-- table index (lead>>4)"
    if ins.address == 0x446EC3: mk = "   <-- cmp dl,0xEB"
    if ins.address == 0x446EC6: mk = "   <-- jb (Fix2: 72->EB)"
    print(f"  0x{ins.address:08X} ({f(ins.address):06X}): {ins.bytes.hex():<14} {ins.mnemonic} {ins.op_str}{mk}")

print("\n=== SJIS class table @ VA 0x48CAE8 (file 0x08CAE8), 16 dwords by high-nibble ===")
tb = f(0x48CAE8)
for nib in range(16):
    off = tb + nib*4
    dw = int.from_bytes(raw[off:off+4], "little")
    leadlo = nib<<4
    note = ""
    if nib in (0xA,0xB,0xC,0xD): note = f"  <-- leads 0x{leadlo:02X}-0x{leadlo+0xF:02X} (GBK hanzi) Fix1: 01->02"
    print(f"  nib 0x{nib:X} file 0x{off:06X}: dword={dw:08X}  byte0={raw[off]:02X}{note}")

print("\n=== exact patch-site bytes ===")
for foff in (0x08CB10,0x08CB14,0x08CB18,0x08CB1C):
    print(f"  0x{foff:06X}: {raw[foff]:02X} (want 01->02)")
print(f"  0x046EC6: {raw[0x046EC6]:02X} (want 72->EB)")
print(f"  0x03F87D: {raw[0x03F87D]:02X} {raw[0x03F87E]:02X} (OS warn, want 75 26->EB 26)")
print(f"  0x0580AD: {raw[0x0580AD]:02X} {raw[0x0580AE]:02X} (CD prompt, want 74 4C->EB 53)")
print("done")
