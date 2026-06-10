@echo off
rem ============================================================
rem  Qingmeizhuma de Ta (Osananajimi na Kanojo) - Chinese patch
rem  One-click launcher: configures the registry for THIS folder
rem  (wherever you unzip it) and starts the game. No admin needed.
rem  v2: also writes the 4 volume values (missing/zero volumes
rem      were the cause of "no sound") and all audio switches.
rem ============================================================
cd /d "%~dp0"
echo.
echo   [ Qing Mei Zhu Ma De Ta - Han Hua Ban ]
echo   Configuring environment for this folder...
echo.
powershell -NoProfile -Command "$d='%~dp0'; $k='HKCU:\Software\E-G-O\OsaKano'; [void](New-Item -Path $k -Force); foreach($n in 'InstallDir','CD-ROM Drive','VoicePath'){ Set-ItemProperty $k $n $d }; Set-ItemProperty $k Font ([char]0x5B8B+[char]0x4F53); foreach($n in 'GrInstall','MusicInstall','VoiceInstall','Music'){ Set-ItemProperty $k $n 1 -Type DWord }; $p=Get-ItemProperty $k; foreach($n in 'Voice','UseSE','UseMusic','MouseSE','SystemVoice','VoiceBar','Shake'){ if($null -eq $p.$n){ Set-ItemProperty $k $n 1 -Type DWord } }; if($null -eq $p.WindowMode){ Set-ItemProperty $k WindowMode 1 -Type DWord }; if($null -eq $p.TextAA){ Set-ItemProperty $k TextAA 0 -Type DWord }; if($null -eq $p.VoiceChr){ Set-ItemProperty $k VoiceChr 0x7fffffff -Type DWord }; foreach($n in 'TotalVolume','MusicVolume','VoiceVolume','SEVolume'){ if($null -eq $p.$n -or 0 -eq $p.$n){ Set-ItemProperty $k $n 100 -Type DWord } }"
if errorlevel 1 (
  echo   [!] Configuration failed. Make sure PowerShell is available.
  pause
  exit /b
)
echo   Done. Starting game...
start "" "%~dp0osakano.exe"
exit
