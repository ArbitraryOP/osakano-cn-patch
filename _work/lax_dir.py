import sys, io, struct, os
sys.stdout = io.open(r"E:\game\_work\lax_dir_out.txt", "w", encoding="utf-8")
lax = open(r"E:\game\文本\scenario.lax",'rb').read()
N=len(lax)
ipos = lax.find(b'$LapI__\x00')
hdr_val = struct.unpack_from('<I', lax, 12)[0]
footer = lax[ipos+8:]
fcount = struct.unpack_from('<I', footer, 0)[0]
fvals = struct.unpack_from('<6I', footer, 4)
print("uint32@12 =", hex(hdr_val), hdr_val)
print("footer count =", fcount, "vals =", [hex(v) for v in fvals])
dir_start = fvals[4]  # 0x10C497
print("dir_start(0x10C497?)=", hex(dir_start))

def lzss_decode(data, start, end, plv=0, threshold=3, ring_size=4096, ring_init=0):
    out=bytearray(); ring=bytearray([ring_init])*ring_size
    R=ring_size-threshold; mask=ring_size-1; i=start
    while i<end:
        flag=data[i]; i+=1
        for b in range(8):
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

# decode up to dir_start
for endp in (dir_start, dir_start+8, ipos):
    dec = lzss_decode(lax, 0x10, endp)
    print(f"decode 0x10..0x{endp:X}: out size {len(dec)} (target 0x1E74B8={0x1E74B8})  match={len(dec)==0x1E74B8}")

# dump the directory bytes
print("\n=== directory region lax[0x%X:0x%X] (%d bytes) ===" % (dir_start, ipos, ipos-dir_start))
dreg = lax[dir_start:ipos]
for i in range(0, min(len(dreg), 0x300), 16):
    ch=dreg[i:i+16]
    print(f"  +{i:04X}: " + ' '.join(f'{b:02X}' for b in ch) + "  " + ''.join(chr(c) if 32<=c<127 else '.' for c in ch))
print("done")
