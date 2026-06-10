import io, sys
sys.stdout = io.open(r"E:\game\_work\uiverify_out.txt", "w", encoding="utf-8")
d = open(r"E:\game\cn\osakano.exe", "rb").read()   # ASCII path == game exe
checks = {
 0x8B040:"menu:exit", 0x8B060:"menu:title", 0x8B07C:"menu:back",
 0x8B08C:"menu:backlog", 0x8B0B4:"menu:skip", 0x8B0D4:"menu:config",
 0x8B0EC:"menu:resume", 0x8B108:"menu:save",
 0x8BDCC:"load-fail", 0x8BDF0:"save-fail", 0x8BE0C:"save-done",
 0x8C304:"OK", 0x8C2F4:"cancel", 0x8B634:"message", 0x8BA1C:"error",
 0x8AE44:"exit+hotkey", 0x8BEB4:"load-desc",
}
for off, name in checks.items():
    run = d[off:off+40].split(b"\x00")[0]
    gbk = run.decode("cp936","replace")
    sjis = run.decode("cp932","replace")
    print(f"0x{off:06X} {name:14} GBK={gbk!r}")
print("done")
