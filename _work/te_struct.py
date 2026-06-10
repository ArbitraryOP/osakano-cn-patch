import sys, io, struct
sys.stdout = io.open(r"E:\game\_work\te_struct_out.txt", "w", encoding="utf-8")

path = r"E:\game\幼なじみな彼女\sena\sce\op.te"
d = open(path,'rb').read()
N = len(d)
print(f"file {path} size {N} = 0x{N:X}")
hdr = struct.unpack_from('<8I', d, 8)
print("hdr dwords @8:", [f"0x{x:X}({x})" for x in hdr])
print()

def hexwin(off, length, label=""):
    print(f"--- {label} @0x{off:X} len {length} ---")
    end=min(N, off+length)
    for i in range(off, end, 16):
        chunk=d[i:i+16]
        hx=' '.join(f'{x:02X}' for x in chunk)
        asc=''.join(chr(x) if 32<=x<127 else '.' for x in chunk)
        print(f"  {i:06X}: {hx:<47}  {asc}")
    print()

# regions at each header offset
hexwin(0x28, 0x80, "post-header (code start)")
for i,v in enumerate(hdr):
    if 0 < v < N:
        hexwin(v, 0x60, f"hdr[{i}]=0x{v:X}")
# tail
hexwin(max(0,N-0x80), 0x80, "file tail")

# Detect potential uint32 offset tables: scan whole file, find runs where consecutive
# dwords are monotonic increasing and all < N (>=8 in a row)
print("\n=== scanning for monotonic uint32 offset-table runs (>=8 entries, values< N) ===")
i=0
runs=[]
while i+4 <= N-32:
    # try a run starting here (4-aligned)
    if i % 4 != 0:
        i+=1; continue
    vals=[]
    j=i
    prev=-1
    while j+4<=N:
        v=struct.unpack_from('<I', d, j)[0]
        if 0 <= v < N and v >= prev:
            vals.append(v); prev=v; j+=4
        else:
            break
    if len(vals)>=12:
        runs.append((i, len(vals), vals[0], vals[-1]))
        i=j
    else:
        i+=4
for off,cnt,v0,v1 in runs[:40]:
    print(f"  table @0x{off:X}: {cnt} entries, first=0x{v0:X} last=0x{v1:X}")
print(f"total candidate tables: {len(runs)}")
print("done")
