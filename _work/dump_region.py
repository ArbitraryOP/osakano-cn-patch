import sys

path = sys.argv[1]
with open(path, 'rb') as f:
    data = f.read()

def hexdump(off, length, label=""):
    print(f"--- {label} file off 0x{off:X}, len {length} ---")
    end = off + length
    for i in range(off, end, 16):
        chunk = data[i:min(i+16, end)]
        hx = ' '.join(f"{b:02X}" for b in chunk)
        asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"{i:08X}  {hx:<48}  {asc}")
    print()

# Regions around the three font names (struct may start ~28 bytes before facename)
hexdump(0x8B620, 0x60, "around MS Gothic (0x8B64C)")
hexdump(0x8BE20, 0x60, "around MS Mincho (0x8BE48)")
hexdump(0x8C840, 0x60, "around MS PGothic (0x8C86C)")
