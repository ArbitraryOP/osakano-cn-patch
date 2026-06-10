import sys, io, re
sys.stdout = io.open(r"E:\game\_work\exe_ui_strings.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
raw = open(EXE, "rb").read()

# UI strings live in .data; scan a generous range and keep null-terminated SJIS runs
# that contain kana/kanji (i.e. real Japanese UI text), with offset + byte length.
# Range covers the observed UI block.
START, END = 0x8A000, 0x8D400

def is_jp(s):
    return any('぀' <= c <= 'ヿ' or '一' <= c <= '鿿'
               or '！' <= c <= '｠' for c in s)

i = START
seen = 0
while i < END:
    # find a null-terminated run starting at i
    j = raw.find(b'\x00', i)
    if j < 0 or j > END:
        break
    run = raw[i:j]
    if len(run) >= 2:
        try:
            s = run.decode('cp932')
            if is_jp(s) and all(ord(c) >= 0x20 or c in '　' for c in s):
                print(f"0x{i:06X}\t{len(run)}\t{s}")
                seen += 1
        except Exception:
            pass
    i = j + 1
print(f"\n# total JP UI strings found: {seen}", file=sys.stderr)
