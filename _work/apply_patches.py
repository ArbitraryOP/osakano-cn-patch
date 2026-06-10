"""Apply verified binary patches from a JSON list to osakano.exe (in place, with backup).
JSON: [{"tag":..,"file_offset_hex":"0x..","orig_bytes_hex":"..","new_bytes_hex":".."}, ...]
Each orig must match the current file bytes exactly, else that patch is SKIPPED and reported.
Usage: python apply_patches.py pending_patches.json [--write]
Without --write it does a DRY RUN (verify only).
"""
import io, sys, json, shutil
sys.stdout = io.open(r"E:\game\_work\apply_patches_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\jp\osakano.exe"
BUILD = r"E:\game\_work\build\osakano.exe"

def parse_hex(s):
    return bytes.fromhex(s.replace("0x","").replace(" ","").replace(",",""))

def main(jpath, write):
    patches = json.load(open(jpath, encoding="utf-8"))
    d = bytearray(open(EXE, "rb").read())
    ok=[]; bad=[]
    for p in patches:
        off = int(p["file_offset_hex"], 16)
        orig = parse_hex(p["orig_bytes_hex"]); new = parse_hex(p["new_bytes_hex"])
        tag = p.get("tag", p.get("target",""))
        cur = bytes(d[off:off+len(orig)])
        if cur != orig:
            bad.append((tag, off, f"orig mismatch: file has {cur.hex(' ')} expected {orig.hex(' ')}"))
            continue
        if len(new) != len(orig):
            bad.append((tag, off, f"length differs orig={len(orig)} new={len(new)} (refusing, would shift)"))
            continue
        d[off:off+len(new)] = new
        ok.append((tag, off, f"{orig.hex(' ')} -> {new.hex(' ')}"))
    print("=== OK (will apply) ===")
    for t,o,m in ok: print(f"  [{t}] 0x{o:06X}: {m}")
    print("=== SKIPPED ===")
    for t,o,m in bad: print(f"  [{t}] 0x{o:06X}: {m}")
    if write and ok and not bad:
        shutil.copy(EXE, EXE+".pre_bin.bak")
        open(EXE,"wb").write(d)
        shutil.copy(EXE, BUILD)
        print(f"\nWROTE {len(ok)} patches to exe + synced build/. backup: osakano.exe.pre_bin.bak")
    elif write and bad:
        print("\nNOT WRITING: some patches failed verification. Resolve first.")
    else:
        print("\nDRY RUN (pass --write to apply).")

if __name__ == "__main__":
    main(sys.argv[1], "--write" in sys.argv)
