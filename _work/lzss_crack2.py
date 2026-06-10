import sys, io, re
sys.stdout = io.open(r"E:\game\_work\crack2_out.txt", "w", encoding="utf-8")
lax = open(r"E:\game\文本\scenario.lax",'rb').read()
ipos = lax.find(b'$LapI__\x00')
op = open(r"E:\game\幼なじみな彼女\sena\sce\op.te",'rb').read()

# known dialogue samples from op.te
samples=[]
for m in re.finditer(rb'\x81\x75(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]){3,30}\x81\x76', op):
    samples.append(m.group())
    if len(samples)>=15: break

def decode(start, end, threshold, Rinit, ring_size, ring_init, plv):
    out=bytearray(); ring=bytearray([ring_init])*ring_size
    R=Rinit; mask=ring_size-1; i=start
    while i<end:
        flag=data=lax[i]; i+=1
        for b in range(8):
            if i>=end: break
            bit=(flag>>b)&1
            if bit==1:
                c=lax[i]; i+=1; out.append(c); ring[R]=c; R=(R+1)&mask
            else:
                if i+1>=end: break
                b0=lax[i]; b1=lax[i+1]; i+=2
                if plv==0:
                    pos=b0|((b1&0xF0)<<4); length=(b1&0x0F)+threshold
                else:
                    pos=b0|((b1&0x0F)<<8); length=((b1>>4)&0x0F)+threshold
                for k in range(length):
                    c=ring[(pos+k)&mask]; out.append(c); ring[R]=c; R=(R+1)&mask
    return bytes(out)

def sjis_ratio(b):
    i=0; valid=0; n=len(b)
    while i<n:
        c=b[i]
        if (0x81<=c<=0x9f or 0xe0<=c<=0xfc) and i+1<n and (0x40<=b[i+1]<=0x7e or 0x80<=b[i+1]<=0xfc):
            valid+=2; i+=2
        else:
            i+=1
    return valid/n if n else 0

best=None
results=[]
for plv in (0,1):
    for threshold in (2,3):
        F = 15+threshold
        for Rinit in (4096-F, 4096-threshold, 4078, 4096-18, 0, 1):
            for ring_init in (0x00,0x20):
                ring_size=4096
                try:
                    out=decode(0x12, ipos, threshold, Rinit, ring_size, ring_init, plv)
                except Exception as e:
                    continue
                if out[:8]!=b'$TAMdata': continue
                r=sjis_ratio(out)
                hits=sum(1 for s in samples if s in out)
                results.append((r,hits,plv,threshold,Rinit,ring_init,len(out)))
results.sort(reverse=True)
print("top results (sjis_ratio, dialogue_hits, plv, threshold, Rinit, ring_init, outlen):")
for row in results[:15]:
    print(f"  ratio={row[0]*100:.1f}% hits={row[1]:2}/{len(samples)} plv={row[2]} thr={row[3]} Rinit={row[4]} init=0x{row[5]:02X} len={row[6]}")
print("done")
