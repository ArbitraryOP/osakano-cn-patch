"""Merge translated parts (with salvage of corrupt JSON), one-pass equal-length
reinsert into v1.02 .te files, stage built/. Writes overflow.json.
Usage: python integrate.py [name1 name2 ...]   (default: all names that have parts)
"""
import sys, os, json, glob, re, shutil, io
sys.path.insert(0, r"E:\game\_work\agentB")
import te_text

UNPACKED   = r"E:\game\_work\unpacked"
PARTS      = r"E:\game\_work\translated_parts"
TRANSLATED = r"E:\game\_work\translated"
BUILT      = r"E:\game\_work\built"
os.makedirs(TRANSLATED, exist_ok=True)
os.makedirs(BUILT, exist_ok=True)
LOG = io.open(r"E:\game\_work\integrate_out.txt", "w", encoding="utf-8")

def baseline_copy():
    n = 0
    for f in os.listdir(UNPACKED):
        if f == "manifest.json":
            continue
        shutil.copy(os.path.join(UNPACKED, f), os.path.join(BUILT, f))
        n += 1
    LOG.write(f"baseline: copied {n} original entries into built/\n")

def salvage(text):
    """Recover {id, zh_spans} objects from possibly-malformed JSON via bracket matching."""
    out = []
    for m in re.finditer(r'"id"\s*:\s*(\d+)\s*,\s*"zh_spans"\s*:\s*\[', text):
        rid = int(m.group(1)); i = m.end() - 1
        depth = 0; j = i; instr = False; esc = False
        while j < len(text):
            c = text[j]
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': instr = not instr
            elif not instr and c == '[': depth += 1
            elif not instr and c == ']':
                depth -= 1
                if depth == 0: break
            j += 1
        try:
            spans = json.loads(text[i:j + 1])
            if isinstance(spans, list):
                out.append({"id": rid, "zh_spans": spans})
        except Exception:
            pass
    return out

def merge(name):
    parts = sorted(glob.glob(os.path.join(PARTS, f"{name}__*.json")))
    by_id = {}
    salvaged = 0
    for p in parts:
        txt = open(p, encoding="utf-8").read()
        try:
            data = json.loads(txt)
            if isinstance(data, dict):
                data = data.get("items", [])
        except Exception:
            data = salvage(txt)
            salvaged += 1
            LOG.write(f"  salvaged {len(data)} records from {os.path.basename(p)}\n")
        for it in data:
            if isinstance(it, dict) and "id" in it and "zh_spans" in it:
                by_id[it["id"]] = {"id": it["id"], "zh_spans": it["zh_spans"]}
    merged = [by_id[k] for k in sorted(by_id)]
    json.dump(merged, open(os.path.join(TRANSLATED, name + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return merged, len(parts), salvaged

def build_file(name, tr_by_id):
    src = os.path.join(UNPACKED, name + ".te")
    data = bytearray(open(src, "rb").read())
    records = te_text.extract(src)
    edited = 0; removed = []
    for idx, rec in enumerate(records):
        orig_raw = bytes.fromhex(rec["raw_bytes_hex"])
        tokens = rec["tokens"]
        item = tr_by_id.get(idx)
        if item is None:
            continue  # untranslated -> keep original bytes already in place
        spans = item.get("zh_spans", [])
        jp_idx = [k for k, t in enumerate(tokens) if t["t"] == "jp"]
        jp_map = {}
        for n, k in enumerate(jp_idx):
            if n < len(spans) and spans[n] is not None:
                jp_map[k] = spans[n]
        if not jp_map:
            continue
        try:
            new_raw = te_text.build_run_bytes(orig_raw, tokens, jp_map,
                                              target_codec="cp936", rec_id=idx)
            data[rec["offset"]:rec["offset"] + len(new_raw)] = new_raw
            edited += 1
        except ValueError:
            removed.append(idx)
    open(os.path.join(BUILT, name + ".te"), "wb").write(data)
    return edited, removed

def main():
    baseline_copy()
    names = sys.argv[1:]
    if not names:
        names = sorted(set(os.path.basename(p).split("__")[0]
                           for p in glob.glob(os.path.join(PARTS, "*.json"))))
    total_edit = total_rm = 0
    overflow = {}
    for name in names:
        if not os.path.exists(os.path.join(UNPACKED, name + ".te")):
            continue
        merged, nparts, salv = merge(name)
        if not merged:
            continue
        tr_by_id = {it["id"]: it for it in merged}
        edited, removed = build_file(name, tr_by_id)
        total_edit += edited; total_rm += len(removed)
        if removed:
            overflow[name] = sorted(removed)
        LOG.write(f"{name:14} parts={nparts:2} salvaged={salv} edited={edited:4} "
                  f"overflow={len(removed)} {removed[:8]}\n")
    LOG.write(f"TOTAL edited={total_edit} overflow={total_rm}\n")
    json.dump(overflow, open(r"E:\game\_work\overflow.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    LOG.close()
    print(f"integrate done; edited={total_edit} overflow={total_rm}")

if __name__ == "__main__":
    main()
