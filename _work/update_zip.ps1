# Replace 3 small entries (osakano.exe, setup.reg, 启动游戏.bat) inside the
# 1.3GB release zip WITHOUT recompressing the 116 large entries.
# Use code page 936 for entry names so new entries match the archive's
# existing GBK naming convention (no per-entry UTF-8-flag mismatch).
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip='E:\game\青梅竹马的她_简中汉化版.zip'
$gamedir='E:\game\幼なじみな彼女'
$enc=[Text.Encoding]::GetEncoding(936)
$targets='osakano.exe','setup.reg','启动游戏.bat'

$fs=[IO.File]::Open($zip,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite)
try{
  $arc=New-Object IO.Compression.ZipArchive($fs,[IO.Compression.ZipArchiveMode]::Update,$false,$enc)
  try{
    foreach($t in $targets){
      $e=$arc.Entries | Where-Object { $_.Name -eq $t } | Select-Object -First 1
      if(-not $e){ throw "entry not found: $t" }
      $full=$e.FullName
      $src=Join-Path $gamedir $t
      if(-not (Test-Path $src)){ throw "source missing: $src" }
      $e.Delete()
      $ne=$arc.CreateEntry($full,[IO.Compression.CompressionLevel]::NoCompression)
      $in=[IO.File]::OpenRead($src)
      $out=$ne.Open()
      try{ $in.CopyTo($out) } finally { $out.Dispose(); $in.Dispose() }
      Write-Host ("replaced: {0}  ({1} bytes)" -f $full,(Get-Item $src).Length)
    }
  } finally { $arc.Dispose() }   # rewrite happens here
} finally { $fs.Dispose() }
Write-Host 'ZIP UPDATE DONE'
