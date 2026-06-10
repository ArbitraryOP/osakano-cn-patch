import sys, re, io

path = sys.argv[1]
out_ascii = sys.argv[2]
out_sjis = sys.argv[3]
with open(path, 'rb') as f:
    data = f.read()

# ASCII strings with offsets
ascii_re = re.compile(rb'[\x20-\x7e]{4,}')
with io.open(out_ascii, 'w', encoding='utf-8') as o:
    for m in ascii_re.finditer(data):
        o.write(f"{m.start():08X}  {m.group().decode('ascii')}\n")

# SJIS strings with offsets (sequences of valid double-byte SJIS, optionally mixed with ascii)
sjis_re = re.compile(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc])+')
with io.open(out_sjis, 'w', encoding='utf-8') as o:
    for m in sjis_re.finditer(data):
        try:
            s = m.group().decode('cp932')
        except Exception:
            continue
        if len(s) >= 2:
            o.write(f"{m.start():08X}  {s}\n")

print("done")
print("ascii lines:", sum(1 for _ in open(out_ascii, encoding='utf-8')))
print("sjis lines:", sum(1 for _ in open(out_sjis, encoding='utf-8')))
