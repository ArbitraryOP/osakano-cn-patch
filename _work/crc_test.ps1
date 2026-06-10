# Full CRC validation: stream every entry through; .NET throws InvalidDataException
# on CRC mismatch. Confirms no entry was corrupted by the in-place update.
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip='E:\game\青梅竹马的她_简中汉化版.zip'
$z=[IO.Compression.ZipFile]::OpenRead($zip)
$buf=New-Object byte[] 1048576
$bad=@(); $n=0; $bytes=0L
foreach($e in $z.Entries){
  if($e.Length -eq 0){ $n++; continue }
  try{
    $s=$e.Open()
    try{ while(($r=$s.Read($buf,0,$buf.Length)) -gt 0){ $bytes+=$r } }
    finally{ $s.Dispose() }
    $n++
  } catch { $bad += ("{0}: {1}" -f $e.FullName,$_.Exception.Message) }
}
$z.Dispose()
Write-Host ("entries read OK: {0}  total bytes: {1:N0}" -f $n,$bytes)
if($bad.Count){ Write-Host "CORRUPT ENTRIES:"; $bad | ForEach-Object { Write-Host "  $_" } }
else { Write-Host 'CRC OK - all entries decompressed and validated cleanly' }
