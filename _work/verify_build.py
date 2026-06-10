import io, sys, os, hashlib
sys.path.insert(0, r"E:\game\_work\agentA")
import lax
sys.stdout = io.open(r"E:\game\_work\verify_out.txt", "w", encoding="utf-8")

BUILT = r"E:\game\_work\built"
VER = r"E:\game\_work\verify_unpacked"
LAXF = r"E:\game\_work\build\scenario.lax"

# 1. unpack the repacked archive
m = lax.unpack(LAXF, VER)
print("unpacked entries:", m["count"])

# 2. compare each entry in built/ vs verify_unpacked/ (round-trip must be byte-identical)
def md5(p): return hashlib.md5(open(p,"rb").read()).hexdigest()
mismatch = 0; checked = 0
for f in os.listdir(BUILT):
    a = os.path.join(BUILT, f); b = os.path.join(VER, f)
    if not os.path.isfile(a): continue
    checked += 1
    if not os.path.exists(b):
        print("  MISSING in archive:", f); mismatch += 1; continue
    if md5(a) != md5(b):
        print("  CONTENT DIFF:", f); mismatch += 1
print(f"round-trip: checked {checked}, mismatches {mismatch}")

# 3. spot-check Chinese GBK bytes in the unpacked-from-archive system.te
d = open(os.path.join(VER, "system.te"), "rb").read()
checks = [(0x1A4C, 8, "舞的房间"), (0x1B1A, 4, "龙童"), (0x90C, 20, "缺少必要文件")]
for off, ln, label in checks:
    raw = d[off:off+ln]
    try: dec = raw.split(b"\x00")[0].decode("cp936", "replace")
    except Exception as e: dec = "ERR"+str(e)
    print(f"  system.te @0x{off:X}: {raw.hex(' ')} -> GBK {dec!r}  [{label}]")

# 4. confirm all entries start with $TAMdata (or are .id placeholders)
bad = []
for f in os.listdir(VER):
    p = os.path.join(VER, f)
    if not os.path.isfile(p) or f == "manifest.json": continue
    head = open(p, "rb").read(8)
    if f.endswith(".te") and head != b"$TAMdata":
        bad.append(f)
print("entries not starting with $TAMdata:", bad if bad else "none (all .te OK)")
print("VERDICT:", "PASS" if mismatch == 0 and not bad else "CHECK")
print("done")
