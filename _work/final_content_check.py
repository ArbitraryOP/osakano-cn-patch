import io, sys, os, json
sys.stdout = io.open(r"E:\game\_work\content_check_out.txt", "w", encoding="utf-8")
VER = r"E:\game\_work\verify_unpacked"

def sample(name, ids, n=6):
    recs = {r["id"]: r for r in json.load(open(rf"E:\game\_work\extract\{name}.json", encoding="utf-8"))}
    d = open(os.path.join(VER, name + ".te"), "rb").read()
    print(f"\n=== {name}.te (from repacked archive) ===")
    shown = 0
    for rid in ids:
        rec = recs.get(rid)
        if not rec:
            continue
        raw = d[rec["offset"]:rec["offset"] + rec["length"]]
        try:
            zh = raw.split(b"\x00")[0].decode("cp936", "replace")
        except Exception as e:
            zh = "ERR"
        print(f"  [{rid}] {zh}")
        shown += 1
        if shown >= n:
            break

# opening dialogue
sample("op", [3, 4, 5, 11, 13, 14])
# a route file
sample("0708", list(range(20, 40)))
# diary
sample("zakki", list(range(2, 8)))
# count overall chinese density in op
d = open(os.path.join(VER, "op.te"), "rb").read()
# count GBK hanzi lead bytes (0x81-0xfe followed by valid)
han = 0
i = 0
while i < len(d) - 1:
    if 0x81 <= d[i] <= 0xfe and (0x40 <= d[i+1] <= 0xfe):
        han += 1; i += 2
    else:
        i += 1
print(f"\nop.te: ~{han} double-byte (GBK) chars in archive copy")
print("done")
