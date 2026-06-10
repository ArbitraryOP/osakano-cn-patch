import io, sys
sys.stdout = io.open(r"E:\game\_work\verify_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
d = open(EXE, "rb").read()
print("file size:", len(d))
spots = {
 0x61DC1: ("charset lfCharSet (want 0x86)", 1),
 0x61EC7: ("charset EnumFont (want 0x86)", 1),
 0x1AD86: ("voice verify tail (want B8 01 00 00 00 5F 5E C3 90)", 9),
 0x8B64C: ("font name MS Gothic (want song-ti)", 8),
 0x8C86C: ("font name MS PGothic", 8),
}
for off,(name,n) in spots.items():
    print(f"0x{off:06X} {name}: {d[off:off+n].hex(' ')}")
print("done")
