import sys, re

path = sys.argv[1]
with open(path, 'rb') as f:
    data = f.read()

# Extract ASCII strings (len>=4)
ascii_re = re.compile(rb'[\x20-\x7e]{4,}')
ascii_strings = [m.group().decode('ascii') for m in ascii_re.finditer(data)]

# Keywords of interest
keywords = ['CreateFont', 'TextOut', 'MultiByte', 'WideChar', 'CharSet', 'charset',
            'GetGlyph', 'sena', 'sce', '.te', '.lax', 'scenario', 'LapH', 'TAMdata',
            'Gothic', 'Mincho', 'font', 'Font', 'SHIFTJIS', 'GB2312', '.exe', 'DirectDraw',
            'd3d', 'D3D', 'ddraw', 'voice', 'common', 'gr24', '.wav', '.mpg', '.ogg',
            'kuma', 'savedata', '.rec', '.id', 'GetProcAddress', 'LoadLibrary']

print("=== ASCII strings matching keywords ===")
seen = set()
for s in ascii_strings:
    for k in keywords:
        if k in s and s not in seen:
            seen.add(s)
            print(repr(s))
            break

# Extract Shift-JIS strings (look for font names like MS Gothic in SJIS)
print("\n=== Possible SJIS strings (font names etc.) ===")
sjis_re = re.compile(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]){2,}')
sjis_seen = set()
count = 0
for m in sjis_re.finditer(data):
    try:
        s = m.group().decode('cp932')
    except Exception:
        continue
    if s not in sjis_seen and len(s) >= 2:
        sjis_seen.add(s)
        # Only print ones that look like font names or meaningful (contain ゴ/ミ/明/ゴシック etc or katakana)
        if any(c in s for c in 'ゴシックミンチョウ明朝ＭＳメイリオ'):
            print(repr(s))
            count += 1
    if count > 30:
        break

print(f"\nFile size: {len(data)} bytes")
