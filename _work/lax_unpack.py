import sys, io, struct, os
sys.stdout = io.open(r"E:\game\_work\lax_unpack_out.txt", "w", encoding="utf-8")

LAX = r"E:\game\文本\scenario.lax"
lax = open(LAX,'rb').read()
N=len(lax)
print("scenario.lax", N, "bytes")

# find $LapI__ index marker
ipos = lax.find(b'$LapI__\x00')
print("$LapI__ at compressed offset:", hex(ipos), "(",ipos,")")
print("bytes from header:", lax[8:16].hex(' '))
print("index region hex (from $LapI__):")
idx = lax[ipos:]
for i in range(0, min(len(idx),256), 16):
    ch=idx[i:i+16]
    print(f"  +{i:04X}: " + ' '.join(f'{b:02X}' for b in ch) + "  " + ''.join(chr(c) if 32<=c<127 else '.' for c in ch))

# LZSS decode up to ipos only
def lzss_decode(data, start, end, plv=0, threshold=3, ring_size=4096, ring_init=0):
    out=bytearray(); ring=bytearray([ring_init])*ring_size
    R=ring_size-threshold; mask=ring_size-1; i=start
    while i<end:
        flag=data[i]; i+=1
        for b in range(8):
            if i>=end and True: pass
            bit=(flag>>b)&1
            if bit==1:
                if i>=end: break
                c=data[i]; i+=1; out.append(c); ring[R]=c; R=(R+1)&mask
            else:
                if i+1>end: break
                b0=data[i]; b1=data[i+1]; i+=2
                pos=b0|((b1&0xF0)<<4); length=(b1&0x0F)+threshold
                for k in range(length):
                    c=ring[(pos+k)&mask]; out.append(c); ring[R]=c; R=(R+1)&mask
    return bytes(out)

dec = lzss_decode(lax, 0x10, ipos)
print("\ndecoded size (stream up to index):", len(dec))
open(r"E:\game\_work\scenario_blob.bin",'wb').write(dec)

# Parse index: after '$LapI__\0' (8 bytes): count(uint32)? then entries
p = ipos+8
count = struct.unpack_from('<I', lax, p)[0]; p+=4
print("declared count:", count)
# Try to detect entry layout. After count, maybe a table of dwords then names, OR interleaved.
# Show raw after count
print("after count, next 64 bytes:", lax[p:p+64].hex(' '))

# Hypothesis A: entries = count * (name(?) ...). Let's scan: the tail had pattern dwords then names earlier.
# Let's just look for ascii names in index region and the dword groups.
import re
names=[(m.start(), m.group().decode('latin1')) for m in re.finditer(rb'[A-Za-z0-9_]{1,16}', idx)]
print("ascii tokens in index:", [(hex(o),n) for o,n in names[:60]])
print("done")
