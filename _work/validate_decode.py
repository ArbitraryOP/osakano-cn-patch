import sys, io, struct, os
sys.stdout = io.open(r"E:\game\_work\validate_out.txt", "w", encoding="utf-8")
lax = open(r"E:\game\文本\scenario.lax",'rb').read()
ipos = lax.find(b'$LapI__\x00')

def lzss_decode(data, start, end, threshold=3, ring_size=4096, ring_init=0):
    out=bytearray(); ring=bytearray([ring_init])*ring_size
    R=ring_size-threshold; mask=ring_size-1; i=start
    while i<end:
        flag=data[i]; i+=1
        for b in range(8):
            if i>=end: break
            bit=(flag>>b)&1
            if bit==1:
                c=data[i]; i+=1; out.append(c); ring[R]=c; R=(R+1)&mask
            else:
                if i+1>=end: break
                b0=data[i]; b1=data[i+1]; i+=2
                pos=b0|((b1&0xF0)<<4); length=(b1&0x0F)+threshold
                for k in range(length):
                    c=ring[(pos+k)&mask]; out.append(c); ring[R]=c; R=(R+1)&mask
    return bytes(out)

blob = lzss_decode(lax, 0x10, ipos)  # decode whole compressed region
print("blob size:", len(blob))

# 1) Search for known JP dialogue from loose op.te
op = open(r"E:\game\幼なじみな彼女\sena\sce\op.te",'rb').read()
# take a few 40-byte chunks of op.te's dialogue area and see if they appear in blob
import re
samples = []
# find SJIS dialogue chunks in op (around the 「」 lines)
for m in re.finditer(rb'\x81\x75(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]|[\x20-\x7e]){4,40}\x81\x76', op):
    samples.append(m.group())
    if len(samples)>=10: break
print(f"\nop.te dialogue samples: {len(samples)}")
hit=0
for s in samples:
    idx = blob.find(s)
    try: txt=s.decode('cp932')
    except: txt=repr(s)
    print(f"  {'FOUND@0x%X'%idx if idx>=0 else 'MISS':14}  {txt[:30]}")
    if idx>=0: hit+=1
print(f"dialogue hits in blob: {hit}/{len(samples)}")

# 2) SJIS validity ratio of blob
def sjis_valid_ratio(b):
    i=0; valid=0; total=0
    while i < len(b):
        c=b[i]
        if 0x81<=c<=0x9f or 0xe0<=c<=0xfc:
            if i+1<len(b) and (0x40<=b[i+1]<=0x7e or 0x80<=b[i+1]<=0xfc):
                valid+=2; i+=2; total+=2; continue
            else:
                i+=1; total+=1; continue
        else:
            i+=1; total+=1
    return valid,total
v,t = sjis_valid_ratio(blob)
print(f"\nSJIS double-byte coverage: {v}/{t} = {100*v/t:.1f}% (rest are ascii/control/single)")

# 3) find filenames present in blob (entries like the loose names without 'sce\\')
names = ['0708','0709','op','system','zakki','config','end','ending','cgmode','special1','title','prof','staff','mem','sp']
print("\nfilename markers found in blob:")
for nm in names:
    print(f"  {nm:10} {'yes' if nm.encode() in blob else 'no'}")

# 4) Show a window of readable text deep in the blob (e.g., at 50%)
mid = len(blob)//2
# find a $TAMdata or large sjis run near mid
print("\nblob window near middle (offset 0x%X):" % mid)
w=blob[mid:mid+160]
try:
    print(repr(w.decode('cp932','replace')[:120]))
except Exception as e:
    print("decode err", e)
print("done")
