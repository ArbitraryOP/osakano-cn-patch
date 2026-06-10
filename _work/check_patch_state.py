# -*- coding: utf-8 -*-
"""Dump bytes at every documented patch site across live exe and backups."""
import os

GAME = r"E:\game\幼なじみな彼女"
FILES = [
    "osakano.exe",                # live
    "osakano.exe.pre_bgm.bak",    # before BGM backend patch
    "osakano.exe.pre_trans.bak",  # before UI translation
    "osakano.exe.pre_bin.bak",    # before binary patches
    "osakano.exe.jp.bak",         # original Japanese
]

# (file_offset, length, label)
SITES = [
    (0x07C75, 10, "audio backend selector +0x1271C/0x12720 (A3..=DSound1 / 8935..=waveOut0)"),
    (0x1AD86, 9,  "voice-verify force-exist"),
    (0x3F873, 2,  "OS warn branch 1"),
    (0x3F87D, 2,  "OS warn branch 2"),
    (0x3FCD3, 6,  "Music source force (B8 01.. / B8 03.. / 8B86..)"),
    (0x41250, 2,  "music-prepare gate jne->jmp"),
    (0x41787, 6,  "music-ready GATE_B (B801=force / 8B87=orig)"),
    (0x41816, 6,  "BeginMusicStream GATE_B (B801=force / 8B86=orig)"),
    (0x46EC6, 1,  "body DBCS order branch (EB)"),
    (0x5C507, 1,  "IsSJISLead hi bound (FE)"),
    (0x580AD, 2,  "CD-DA prompt suppress (EB53)"),
    (0x61DC1, 1,  "lfCharSet #1 (86=GB2312)"),
    (0x61EC7, 1,  "lfCharSet #2 (86=GB2312)"),
    (0x8B64C, 8,  "font name #1"),
    (0x8C86C, 8,  "font name #2"),
    (0x8CB10, 4,  "class tbl A0-A7"),
    (0x8CB14, 4,  "class tbl A8-AF"),
    (0x8CB18, 4,  "class tbl B0-B7? (01->02)"),
    (0x8CB1C, 4,  "class tbl ..DF"),
]

data = {}
for fn in FILES:
    p = os.path.join(GAME, fn)
    if os.path.exists(p):
        with open(p, "rb") as f:
            data[fn] = f.read()
    else:
        print(f"MISSING: {fn}")

for off, ln, label in SITES:
    print(f"\n0x{off:06X} ({label})")
    for fn in FILES:
        if fn in data:
            b = data[fn][off:off+ln]
            print(f"  {fn:30s} {b.hex(' ')}")

# also confirm all files same size
print("\nsizes:", {fn: len(d) for fn, d in data.items()})
