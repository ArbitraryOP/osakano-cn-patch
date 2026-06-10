"""Apply equal-length GBK UI-string translations in place to osakano.exe.
JSON: [{"file_offset_hex":"0x..","jp":"...","zh":"..."}, ...]
For each: read the NUL-terminated run at offset, confirm it equals jp.encode(cp932)
(if jp given), then write zh.encode(cp936) + NUL padding up to the original run length.
Refuses any zh that does not fit. Usage: python apply_trans.py file.json [--write]
"""
import io, sys, json, shutil
sys.stdout = io.open(r"E:\game\_work\apply_trans_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\jp\osakano.exe"
BUILD = r"E:\game\_work\build\osakano.exe"

# pointer-table / non-string ranges flagged by the patchesIntact audit -- never edit as strings
FORBIDDEN = [(0x08C504,0x08C5A3), (0x08D148,0x08D317), (0x08A000,0x08A3DF)]
def forbidden(off):
    return any(a <= off <= b for a,b in FORBIDDEN)

def run_at(d, off):
    j = d.find(b"\x00", off)
    return bytes(d[off:j]), j

def main(jpath, write):
    items = json.load(open(jpath, encoding="utf-8"))
    d = bytearray(open(EXE, "rb").read())
    applied=[]; skipped=[]; warned=[]
    for it in items:
        off = int(it["file_offset_hex"], 16)
        zh = it["zh"]; jp = it.get("jp")
        if forbidden(off):
            skipped.append((off, "in FORBIDDEN pointer-table range; refusing")); continue
        run, _ = run_at(d, off)
        # encode target
        try: zb = zh.encode("cp936")
        except Exception as e:
            skipped.append((off, f"zh not cp936-encodable: {e} : {zh!r}")); continue
        if len(zb) > len(run):
            skipped.append((off, f"too long zh={len(zb)} > run={len(run)} : {zh!r}")); continue
        # jp-match: confidence signal only. mixed runs (line2 already GBK) won't match cp932 -> warn, still apply.
        jp_status = "no-jp"
        if jp is not None:
            try: jb = jp.encode("cp932")
            except Exception: jb = None
            if jb == run: jp_status = "jp-match"
            elif run == zb: skipped.append((off, "already applied (run==zh)")); continue
            else:
                jp_status = "jp-MISMATCH(mixed/partial)"
                warned.append((off, f"jp!=run (len run={len(run)} jp={len(jb) if jb else '?'}) applying by fit"))
        d[off:off+len(run)] = zb + b"\x00"*(len(run)-len(zb))
        applied.append((off, f"[{jp_status}] -> {zh[:40]!r} ({len(zb)}/{len(run)} B)"))
    print(f"=== APPLIED ({len(applied)}) ===")
    for o,m in applied: print(f"  0x{o:06X}: {m}")
    print(f"=== WARN-MISMATCH ({len(warned)}) (applied by fit) ===")
    for o,m in warned: print(f"  0x{o:06X}: {m}")
    print(f"=== SKIPPED ({len(skipped)}) ===")
    for o,m in skipped: print(f"  0x{o:06X}: {m}")
    if write and applied:
        shutil.copy(EXE, EXE+".pre_trans.bak")
        open(EXE,"wb").write(d)
        shutil.copy(EXE, BUILD)
        print(f"\nWROTE {len(applied)} string patches + synced build/. backup: osakano.exe.pre_trans.bak")
    else:
        print("\nDRY RUN (pass --write to apply)." if not write else "\nnothing applied.")

if __name__ == "__main__":
    main(sys.argv[1], "--write" in sys.argv)
