# -*- coding: utf-8 -*-
"""Generate a correct UTF-16LE setup.reg for the game.

The old setup.reg had two fatal bugs:
1. InstallDir contained mojibake (the Japanese folder name was double-encoded),
   so importing it pointed the engine at a nonexistent path -> 'CD drive error'.
2. All four volume values were dword:00000000 -> engine fully attenuates every
   DirectSound buffer -> total silence (BGM/voice/SE).

This writes the full registry set that was empirically verified working
(matches the live HKCU state used during in-game testing), volumes at 100.
"""
import io

GAME_DIR = r"E:\game\幼なじみな彼女" + "\\"

def reg_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')

lines = [
    "Windows Registry Editor Version 5.00",
    "",
    r"[HKEY_CURRENT_USER\Software\E-G-O\OsaKano]",
    f'"InstallDir"="{reg_escape(GAME_DIR)}"',
    f'"CD-ROM Drive"="{reg_escape(GAME_DIR)}"',
    f'"VoicePath"="{reg_escape(GAME_DIR)}"',
    '"GrInstall"=dword:00000001',
    '"MusicInstall"=dword:00000001',
    '"VoiceInstall"=dword:00000001',
    '"Music"=dword:00000001',
    '"Font"="宋体"',
    '"WindowMode"=dword:00000001',
    '"TextAA"=dword:00000000',
    '"Shake"=dword:00000001',
    '"TotalVolume"=dword:00000064',
    '"MusicVolume"=dword:00000064',
    '"VoiceVolume"=dword:00000064',
    '"SEVolume"=dword:00000064',
    '"Voice"=dword:00000001',
    '"UseSE"=dword:00000001',
    '"UseMusic"=dword:00000001',
    '"MouseSE"=dword:00000001',
    '"SystemVoice"=dword:00000001',
    '"VoiceBar"=dword:00000001',
    '"VoiceChr"=dword:7fffffff',
    "",
]

content = "\r\n".join(lines)
out = r"E:\game\幼なじみな彼女\setup.reg"
with open(out, "wb") as f:
    f.write(b"\xff\xfe")  # UTF-16LE BOM
    f.write(content.encode("utf-16-le"))
print(f"wrote {out} ({2 + len(content)*2} bytes)")

# verify round-trip
with open(out, "rb") as f:
    data = f.read()
assert data[:2] == b"\xff\xfe"
text = data[2:].decode("utf-16-le")
assert "幼なじみな彼女" in text and "宋体" in text
assert "dword:00000064" in text
print("verify OK: path + font + volume present, clean UTF-16LE")
