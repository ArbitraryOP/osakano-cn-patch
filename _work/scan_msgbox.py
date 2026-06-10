import io, sys
sys.stdout = io.open(r"E:\game\_work\msgbox_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
raw = open(EXE, "rb").read()

# scan whole file for SJIS strings that contain a newline (multi-line prompts) OR end with ？/?
def is_kana_kanji(s):
    return any('぀'<=c<='ヿ' or '一'<=c<='鿿' for c in s)

i = 0; N = len(raw); hits = []
while i < N:
    j = raw.find(b"\x00", i)
    if j < 0: break
    run = raw[i:j]
    if 4 <= len(run) <= 200 and (b"\n" in run or run.endswith(b"\x81H") or run.endswith(b"?")):
        try:
            s = run.decode("cp932")
            if is_kana_kanji(s):
                hits.append((i, len(run), s))
        except Exception:
            pass
    i = j + 1

for off, ln, s in hits:
    disp = s.replace("\n", " / ")
    print(f"0x{off:06X} len={ln:3d}  {disp}")
print(f"\n# total multi-line/question SJIS strings: {len(hits)}")
