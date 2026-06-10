import sys, pefile, io
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

# Redirect all prints to a UTF-8 file to avoid Windows console (GBK) crashes
sys.stdout = io.open(r"E:\game\_work\analyze_out.txt", "w", encoding="utf-8")

EXE = r"E:\game\幼なじみな彼女\osakano.exe"
pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories(directories=[
    pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
image_base = pe.OPTIONAL_HEADER.ImageBase

with open(EXE, 'rb') as f:
    raw = f.read()

# Section table: map file offset <-> VA
sections = []
for s in pe.sections:
    name = s.Name.rstrip(b'\x00').decode('latin1')
    sections.append({
        'name': name,
        'raw_off': s.PointerToRawData,
        'raw_size': s.SizeOfRawData,
        'va': image_base + s.VirtualAddress,
        'vsize': s.Misc_VirtualSize,
    })
    print(f"sec {name:8} raw 0x{s.PointerToRawData:08X}+0x{s.SizeOfRawData:06X}  VA 0x{image_base+s.VirtualAddress:08X}+0x{s.Misc_VirtualSize:06X}")
print(f"ImageBase 0x{image_base:08X}")

def foff_to_va(off):
    for s in sections:
        if s['raw_off'] <= off < s['raw_off'] + s['raw_size']:
            return s['va'] + (off - s['raw_off'])
    return None

def va_to_foff(va):
    for s in sections:
        if s['va'] <= va < s['va'] + s['vsize']:
            o = s['raw_off'] + (va - s['va'])
            if o < s['raw_off'] + s['raw_size']:
                return o
    return None

# Build import name -> IAT VA(s)
iat = {}
if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in entry.imports:
            if imp.name:
                iat.setdefault(imp.name.decode(), []).append(imp.address)  # address = VA of IAT slot

for fn in ['CreateFontIndirectA','TextOutA','MultiByteToWideChar','WideCharToMultiByte','EnumFontFamiliesExA','CreateFileA','ReadFile','SetFilePointer']:
    if fn in iat:
        print(f"IAT {fn}: " + ", ".join(f"0x{a:08X}" for a in iat[fn]))

# Find all references (as 32-bit little-endian immediate) to a given VA within .text
text = next(s for s in sections if s['name'] == '.text')
text_bytes = raw[text['raw_off']:text['raw_off']+text['raw_size']]
text_va = text['va']

def find_refs(target_va):
    needle = target_va.to_bytes(4, 'little')
    refs = []
    start = 0
    while True:
        i = text_bytes.find(needle, start)
        if i < 0: break
        refs.append(text_va + i)
        start = i + 1
    return refs

md = Cs(CS_ARCH_X86, CS_MODE_32)

def disasm_around(center_va, before=32, after=48):
    foff = va_to_foff(center_va - before)
    if foff is None: return
    code = raw[foff:foff+before+after]
    for ins in md.disasm(code, center_va - before):
        marker = " <==" if abs(ins.address - center_va) < 6 else ""
        print(f"  0x{ins.address:08X}: {ins.mnemonic:7} {ins.op_str}{marker}")

# Strings of interest -> file offsets (from earlier scans)
targets = {
    'sce\\%s.te': None,
    'scenario.lax': None,
    'patch\\%s.id': None,
    'ＭＳ ゴシック(font)': 0x8B64C,
    '$LapH__': None,
}

# locate ascii strings by searching raw
def find_ascii(s):
    b = s.encode('latin1') + b'\x00'
    i = raw.find(b)
    return i if i >= 0 else None

for key in ['sce\\%s.te','scenario.lax','patch\\%s.id','$LapH__']:
    targets[key] = find_ascii(key)

print("\n=== String VAs and code references ===")
for name, foff in targets.items():
    if foff is None:
        print(f"\n[{name}] NOT FOUND")
        continue
    va = foff_to_va(foff)
    print(f"\n[{name}] foff=0x{foff:X} va=0x{va:08X}")
    refs = find_refs(va) if va else []
    print(f"  refs in .text: " + (", ".join(f"0x{r:08X}" for r in refs) if refs else "none"))
    for r in refs[:3]:
        print(f"  --- context @ ref 0x{r:08X} ---")
        disasm_around(r, before=40, after=40)
