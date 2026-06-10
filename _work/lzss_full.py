import sys, io, struct, os
sys.stdout = io.open(r"E:\game\_work\lzss_full_out.txt", "w", encoding="utf-8")

lax = open(r"E:\game\文本\scenario.lax",'rb').read()
N=len(lax)
print("scenario.lax size", N)
print("header16:", lax[:16].hex(' '))
print("tail 96 bytes:")
tail=lax[-96:]
for i in range(0,len(tail),16):
    ch=tail[i:i+16]
    print("  "+ ' '.join(f'{b:02X}' for b in ch) + "  " + ''.join(chr(c) if 32<=c<127 else '.' for c in ch))

def lzss_decode(data, start, plv, threshold=3, ring_size=4096, ring_init=0, out_limit=8*1024*1024):
    out=bytearray(); ring=bytearray([ring_init])*ring_size
    R=ring_size-threshold; mask=ring_size-1; i=start; n=len(data)
    while i<n and len(out)<out_limit:
        flag=data[i]; i+=1
        for b in range(8):
            bit=(flag>>b)&1
            if bit==1:
                if i>=n: return bytes(out),i
                c=data[i]; i+=1; out.append(c); ring[R]=c; R=(R+1)&mask
            else:
                if i+1>=n: return bytes(out),i
                b0=data[i]; b1=data[i+1]; i+=2
                if plv==0:
                    pos=b0|((b1&0xF0)<<4); length=(b1&0x0F)+threshold
                else:
                    pos=((b0<<4)|(b1>>4)); length=(b1&0x0F)+threshold
                for k in range(length):
                    c=ring[(pos+k)&mask]; out.append(c); ring[R]=c; R=(R+1)&mask
    return bytes(out),i

te_dir=r"E:\game\幼なじみな彼女\sena\sce"
te_files={fn:open(os.path.join(te_dir,fn),'rb').read() for fn in os.listdir(te_dir) if fn.endswith('.te')}

for plv in (0,1):
    out,consumed=lzss_decode(lax,0x12,plv)
    found=sum(1 for b in te_files.values() if b in out)
    print(f"\nplv={plv}: decoded {len(out)} bytes, consumed {consumed}/{N}, te-files-found-exact {found}/{len(te_files)}")
    if found>0:
        # report offsets of found files
        for fn,b in sorted(te_files.items()):
            idx=out.find(b)
            if idx>=0:
                print(f"   {fn:16} size={len(b):7} @ decoded off 0x{idx:X}")

# pick best plv (the one with more exact matches) and dump structure
out0,_=lzss_decode(lax,0x12,0)
out1,_=lzss_decode(lax,0x12,1)
f0=sum(1 for b in te_files.values() if b in out0)
f1=sum(1 for b in te_files.values() if b in out1)
out = out0 if f0>=f1 else out1
print(f"\nchosen plv={'0' if f0>=f1 else '1'} decoded size {len(out)}")
# save decoded for inspection
open(r"E:\game\_work\scenario_decoded.bin",'wb').write(out)
# look at the very start (is there a directory before first $TAMdata?) and the tail
print("decoded head 64:", out[:64].hex(' '))
print("first $TAMdata at:", out.find(b'$TAMdata'))
# count $TAMdata occurrences
import re
occ=[m.start() for m in re.finditer(b'\\$TAMdata', out)]
print("num $TAMdata entries in decoded:", len(occ), "first few offs:", [hex(x) for x in occ[:8]])
print("decoded tail 160:")
dt=out[-160:]
for i in range(0,len(dt),16):
    ch=dt[i:i+16]
    print("  "+ ' '.join(f'{b:02X}' for b in ch) + "  " + ''.join(chr(c) if 32<=c<127 else '.' for c in ch))
print("done")
