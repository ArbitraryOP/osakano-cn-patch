@echo off
rem ============================================================
rem  Qingmeizhuma de Ta (Osananajimi na Kanojo) - Chinese patch
rem  One-click launcher: configures the registry for THIS folder
rem  (wherever you unzip it) and starts the game. No admin needed.
rem ============================================================
cd /d "%~dp0"
echo.
echo   [ Qing Mei Zhu Ma De Ta - Han Hua Ban ]
echo   Configuring environment for this folder...
echo.
powershell -NoProfile -Command "$d='%~dp0'; $k='HKCU:\Software\E-G-O\OsaKano'; [void](New-Item -Path $k -Force); Set-ItemProperty $k InstallDir $d; Set-ItemProperty $k 'CD-ROM Drive' $d; foreach($n in 'GrInstall','MusicInstall','VoiceInstall','Music','WindowMode'){ Set-ItemProperty $k $n 1 -Type DWord }; Set-ItemProperty $k Font ([char]0x5B8B+[char]0x4F53)"
if errorlevel 1 (
  echo   [!] Configuration failed. Make sure PowerShell is available.
  pause
  exit /b
)
echo   Done. Starting game...
start "" "%~dp0osakano.exe"
exit
