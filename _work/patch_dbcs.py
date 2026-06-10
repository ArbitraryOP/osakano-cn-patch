import io, sys, shutil
sys.stdout = io.open(r"E:\game\_work\patch_dbcs_out.txt", "w", encoding="utf-8")
EXE = r"E:\game\幼なじみな彼女\osakano.exe"
OFF = 0x05C507          # the 0x9F immediate of  cmp cl,0x9f  at VA 0x45C505
d = bytearray(open(EXE, "rb").read())

# sanity: the instruction must be  80 F9 9F  (cmp cl, 0x9f)
ctx = bytes(d[0x05C500:0x05C50A])
print("func head bytes:", ctx.hex(" "))
assert d[0x05C505] == 0x80 and d[0x05C506] == 0xF9, "not cmp cl,imm8 — abort"
if d[OFF] == 0xFE:
    print("already patched (0xFE).")
else:
    assert d[OFF] == 0x9F, f"unexpected byte 0x{d[OFF]:02X} at 0x{OFF:06X} — abort"
    d[OFF] = 0xFE       # widen SJIS range-1 (0x81..0x9F) to GBK lead range (0x81..0xFE)
    open(EXE, "wb").write(d)
    print(f"patched 0x{OFF:06X}: 9F -> FE  (IsSJISLead now accepts GBK leads 0x81..0xFE)")

# re-read & show the patched function bytes
d2 = open(EXE, "rb").read()
print("patched func:", d2[0x05C500:0x05C523].hex(" "))
shutil.copy(EXE, r"E:\game\_work\build\osakano.exe")
print("synced -> build\\osakano.exe")
print("done")
