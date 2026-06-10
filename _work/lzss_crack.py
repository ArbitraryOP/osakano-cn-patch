import sys, io, struct, os
sys.stdout = io.open(r"E:\game\_work\lzss_out.txt", "w", encoding="utf-8")

lax = open(r"E:\game\文本\scenario.lax",'rb').read()
print("scenario.lax size", len(lax))
print("header:", lax[:16].hex(' '))
magic = lax[:8]
method = lax[8:12]
val = struct.unpack_from('<I', lax, 12)[0]
print("magic", magic, "method", method, "val@12", hex(val))

# known plaintext: any .te file. Build set of first 16 bytes signatures.
te_dir = r"E:\game\幼なじみな彼女\sena\sce"
te_files = {}
for fn in os.listdir(te_dir):
    if fn.endswith('.te'):
        p=os.path.join(te_dir,fn)
        b=open(p,'rb').read()
        if b[:8]==b'$TAMdata':
            te_files[fn]=b
print("te files:", len(te_files))

def lzss_decode(data, start, ring_size, ring_init, threshold, lit_is_1, lsb_first, pos_len_variant, out_limit):
    out = bytearray()
    ring = bytearray([ring_init])*ring_size
    R = ring_size - threshold  # common init position (Okumura uses N-F)
    mask = ring_size-1
    i = start
    n = len(data)
    err=None
    while i < n and len(out) < out_limit:
        flag = data[i]; i+=1
        for b in range(8):
            if lsb_first:
                bit = (flag >> b) & 1
            else:
                bit = (flag >> (7-b)) & 1
            is_lit = (bit==1) if lit_is_1 else (bit==0)
            if is_lit:
                if i>=n: return bytes(out), "eof-lit"
                c = data[i]; i+=1
                out.append(c); ring[R]=c; R=(R+1)&mask
            else:
                if i+1>=n: return bytes(out), "eof-match"
                b0=data[i]; b1=data[i+1]; i+=2
                if pos_len_variant==0:
                    pos = b0 | ((b1 & 0xF0)<<4); length=(b1&0x0F)+threshold
                elif pos_len_variant==1:
                    pos = b0 | ((b1 & 0x0F)<<8); length=((b1>>4)&0x0F)+threshold
                elif pos_len_variant==2:
                    # length high
                    pos = ((b0<<4)|(b1>>4)); length=(b1&0x0F)+threshold
                else:
                    pos = ((b0&0x0F)<<8)|b1; length=(b0>>4)+threshold
                for k in range(length):
                    c=ring[(pos+k)&mask]
                    out.append(c); ring[R]=c; R=(R+1)&mask
            if len(out)>=out_limit: break
        # safety
        if len(out)>out_limit: break
    return bytes(out), err

# brute force over variants and starts, score by matching $TAMdata + presence of a known te header
te_sigs = [b[:16] for b in te_files.values()]
best=None
for start in (0x10,0x11,0x12,0x14,0x18):
    for ring_size in (4096,2048):
        for ring_init in (0x00,0x20):
            for threshold in (2,3):
                for lit_is_1 in (True,False):
                    for lsb in (True,False):
                        for plv in (0,1,2,3):
                            try:
                                out,err = lzss_decode(lax,start,ring_size,ring_init,threshold,lit_is_1,lsb,plv,4096)
                            except Exception as e:
                                continue
                            if out[:8]==b'$TAMdata':
                                # score: how many known sigs appear in out
                                score=sum(1 for s in te_sigs if s in out)
                                cand=(score,start,ring_size,ring_init,threshold,lit_is_1,lsb,plv,out[:32].hex(' '))
                                if best is None or cand[0]>best[0]:
                                    best=cand
                                if out[:16]==b'$TAMdata\x71\x00\x00\x00\x78\x47\x00\x00' or out[:12]==b'$TAMdata\x71\x00\x00\x00':
                                    print("CANDIDATE start=0x%X ring=%d init=%d thr=%d lit1=%s lsb=%s plv=%d -> %s"%(start,ring_size,ring_init,threshold,lit_is_1,lsb,plv,out[:32].hex(' ')))
print("BEST:", best)
print("done")
