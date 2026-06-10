# Fresh-player end-to-end verification:
#   wipe HKCU key -> run new 启动游戏.bat -> check registry -> title BGM peak
#   -> New Game -> dialogue voice peak -> screenshots.
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p);
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x,int y,int cx,int cy,uint flags);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint dx,uint dy,uint d,IntPtr e);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X,Y; }
}
"@
Add-Type @"
using System;using System.Collections.Generic;using System.Runtime.InteropServices;
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator { int EnumAudioEndpoints(int f,int mask,out IMMDeviceCollection c); int GetDefaultAudioEndpoint(int f,int r,out IMMDevice e); }
[ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceCollection { int GetCount(out int n); int Item(int i,out IMMDevice d); }
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice { int Activate([MarshalAs(UnmanagedType.LPStruct)]Guid iid,int ctx,IntPtr p,[MarshalAs(UnmanagedType.IUnknown)]out object o);
  int OpenPropertyStore(int a, out IntPtr ps); int GetId([MarshalAs(UnmanagedType.LPWStr)]out string id); int GetState(out int st); }
[ComImport, Guid("C02216F6-8C67-4B5B-9D00-D008E73E0064"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMeter { int GetPeakValue(out float p); }
public static class AD {
  static List<IMeter> meters = new List<IMeter>();
  public static float[] max;
  public static int Init(){
    var t=Type.GetTypeFromCLSID(new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"));
    var e=(IMMDeviceEnumerator)Activator.CreateInstance(t);
    IMMDeviceCollection c; e.EnumAudioEndpoints(0,1,out c); int n; c.GetCount(out n);
    for(int i=0;i<n;i++){ IMMDevice d; c.Item(i,out d);
      object o; d.Activate(typeof(IMeter).GUID,1,IntPtr.Zero,out o); meters.Add((IMeter)o); }
    max=new float[meters.Count]; return meters.Count;
  }
  public static void Reset(){ for(int i=0;i<max.Length;i++) max[i]=0; }
  public static void Sample(){ for(int i=0;i<meters.Count;i++){ float p; meters[i].GetPeakValue(out p); if(p>max[i]) max[i]=p; } }
  public static float Best(){ float b=0; for(int i=0;i<max.Length;i++) if(max[i]>b) b=max[i]; return b; }
}
"@
[W]::SetProcessDPIAware() | Out-Null
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference='SilentlyContinue'
$GAMEDIR='E:\game\幼なじみな彼女'
$OUT='E:\game\_work'
$HWND_TOPMOST=[IntPtr]-1; $SWP_NOMOVE=0x2; $SWP_NOSIZE=0x1; $SWP_SHOW=0x40; $MD=0x2; $MU=0x4

function Get-Wins($pid0){
  $script:WL=@()
  $cb=[W+EnumProc]{ param($h,$p)
    $wp=0; [W]::GetWindowThreadProcessId($h,[ref]$wp)|Out-Null
    if($wp -eq $pid0 -and [W]::IsWindowVisible($h)){
      $sb=New-Object Text.StringBuilder 256; [W]::GetClassName($h,$sb,256)|Out-Null
      $r=New-Object W+RECT; [W]::GetWindowRect($h,[ref]$r)|Out-Null
      $script:WL += [pscustomobject]@{H=$h;Cls=$sb.ToString();W=($r.R-$r.L);Ht=($r.B-$r.T)}
    }; return $true
  }
  [W]::EnumWindows($cb,[IntPtr]::Zero)|Out-Null
  return $script:WL
}
function Shot($h,$path){
  $r=New-Object W+RECT; [W]::GetWindowRect($h,[ref]$r)|Out-Null
  $w=$r.R-$r.L; $ht=$r.B-$r.T; if($w -le 0 -or $ht -le 0){return}
  $bmp=New-Object Drawing.Bitmap $w,$ht; $g=[Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.L,$r.T,0,0,(New-Object Drawing.Size($w,$ht)))
  $bmp.Save($path,[Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
  Write-Host "  shot -> $path ($w x $ht)"
}
function ClickClient($h,$fx,$fy){
  $c=New-Object W+RECT; [W]::GetClientRect($h,[ref]$c)|Out-Null
  $p=New-Object W+POINT; $p.X=[int]($c.R*$fx); $p.Y=[int]($c.B*$fy)
  [W]::ClientToScreen($h,[ref]$p)|Out-Null
  [W]::SetForegroundWindow($h)|Out-Null
  [W]::SetCursorPos($p.X,$p.Y)|Out-Null; Start-Sleep -Milliseconds 120
  [W]::mouse_event($MD,0,0,0,[IntPtr]::Zero); Start-Sleep -Milliseconds 80
  [W]::mouse_event($MU,0,0,0,[IntPtr]::Zero)
}
function ClickWindow($h,$fx,$fy){
  $r=New-Object W+RECT; [W]::GetWindowRect($h,[ref]$r)|Out-Null
  $x=[int]($r.L + ($r.R-$r.L)*$fx); $y=[int]($r.T + ($r.B-$r.T)*$fy)
  [W]::SetForegroundWindow($h)|Out-Null
  [W]::SetCursorPos($x,$y)|Out-Null; Start-Sleep -Milliseconds 120
  [W]::mouse_event($MD,0,0,0,[IntPtr]::Zero); Start-Sleep -Milliseconds 80
  [W]::mouse_event($MU,0,0,0,[IntPtr]::Zero)
}
function SamplePeaks($seconds){
  $end=(Get-Date).AddSeconds($seconds)
  while((Get-Date) -lt $end){ [AD]::Sample(); Start-Sleep -Milliseconds 50 }
}

# ---------- step 0: clean slate ----------
Get-Process osakano -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
Start-Sleep -Milliseconds 600
Remove-Item 'HKCU:\Software\E-G-O\OsaKano' -Recurse -Force -EA SilentlyContinue
if(Test-Path 'HKCU:\Software\E-G-O\OsaKano'){ Write-Host 'FAIL: registry key still present' } else { Write-Host 'OK: registry key wiped (fresh player)' }

# ---------- step 1: run the launcher bat (detached!) ----------
# NOTE: no pipe (game inherits stdout handle) and no -Wait (PS5.1 -Wait waits
# for the whole process tree incl. the game). Fire and poll instead.
$bat = Join-Path $GAMEDIR '启动游戏.bat'
Start-Process -FilePath $bat -WorkingDirectory $GAMEDIR -WindowStyle Minimized
$deadline=(Get-Date).AddSeconds(40)
while((Get-Date) -lt $deadline -and -not (Get-Process osakano -EA SilentlyContinue)){ Start-Sleep -Milliseconds 500 }
if(-not (Get-Process osakano -EA SilentlyContinue)){ Write-Host 'FAIL: game did not start within 40s'; exit 1 }
Write-Host 'OK: game process started by bat'

# ---------- step 2: verify registry written ----------
$p=$null
$deadline=(Get-Date).AddSeconds(15)
while((Get-Date) -lt $deadline){
  $p = Get-ItemProperty 'HKCU:\Software\E-G-O\OsaKano' -EA SilentlyContinue
  if($p -and $null -ne $p.TotalVolume){ break }
  Start-Sleep -Milliseconds 500
}
if($null -eq $p){ Write-Host 'FAIL: registry not created by bat'; exit 1 }
$expect100 = 'TotalVolume','MusicVolume','VoiceVolume','SEVolume'
$bad=@()
foreach($n in $expect100){ if($p.$n -ne 100){ $bad += "$n=$($p.$n)" } }
foreach($n in 'GrInstall','MusicInstall','VoiceInstall','Music','Voice','UseSE','UseMusic','MouseSE','SystemVoice','VoiceBar','Shake'){ if($p.$n -ne 1){ $bad += "$n=$($p.$n)" } }
if($p.InstallDir -ne ($GAMEDIR + '\')){ $bad += "InstallDir=$($p.InstallDir)" }
if($p.Font -ne ([char]0x5B8B+[char]0x4F53)){ $bad += "Font=$($p.Font)" }
if($bad.Count){ Write-Host ("REG PROBLEMS: " + ($bad -join '; ')) } else { Write-Host 'OK: registry fully configured (volumes=100, switches=1, paths/font correct)' }

# ---------- step 3: wait for game window ----------
$pid0 = (Get-Process osakano -EA SilentlyContinue | Select-Object -First 1).Id
if(-not $pid0){ Write-Host 'FAIL: osakano.exe not running'; exit 1 }
Write-Host "game pid=$pid0"
$nDevs=[AD]::Init(); Write-Host "audio render devices: $nDevs"
$main=$null; $dlgSeen=0
for($i=0;$i -lt 60;$i++){
  $wins = Get-Wins $pid0
  $dlgs = @($wins | Where-Object {$_.Cls -eq '#32770'})
  if($dlgs.Count){ $dlgSeen += $dlgs.Count; Write-Host ("  WARNING: dialog box appeared! count=" + $dlgs.Count) }
  $cand = $wins | Where-Object {$_.Cls -ne '#32770' -and $_.W -gt 500 -and $_.Ht -gt 400}
  if($cand){ $main=($cand | Sort-Object {$_.W*$_.Ht} -Descending | Select-Object -First 1); Write-Host "main window found iter=$i size=$($main.W)x$($main.Ht)"; break }
  Start-Sleep -Milliseconds 400
}
if($null -eq $main){ Write-Host 'FAIL: no main window'; exit 1 }
$h=$main.H
[W]::BringWindowToTop($h)|Out-Null; [W]::SetForegroundWindow($h)|Out-Null
[W]::SetWindowPos($h,$HWND_TOPMOST,0,0,0,0,($SWP_NOMOVE -bor $SWP_NOSIZE -bor $SWP_SHOW))|Out-Null
Start-Sleep -Milliseconds 900

# ---------- step 4: advance logo->title, measure BGM ----------
ClickClient $h 0.5 0.5; Start-Sleep -Milliseconds 1200
ClickClient $h 0.5 0.5; Start-Sleep -Milliseconds 1200
ClickClient $h 0.5 0.5; Start-Sleep -Milliseconds 1000
Shot $h "$OUT\f_title.png"
[AD]::Reset()
SamplePeaks 4
$bgmPeak=[AD]::Best()
Write-Host ("TITLE BGM max peak = {0:N4}  ({1})" -f $bgmPeak, $(if($bgmPeak -gt 0.005){'AUDIBLE'}else{'SILENT'}))

# ---------- step 5: New Game -> dialogue, measure voice ----------
ClickWindow $h 0.123 0.398; Start-Sleep -Milliseconds 2200
Shot $h "$OUT\f_afterNG.png"
[AD]::Reset()
for($k=0;$k -lt 8;$k++){
  ClickClient $h 0.5 0.6
  SamplePeaks 1.4
  if($k -eq 3 -or $k -eq 7){ Shot $h ("$OUT\f_dlg{0}.png" -f $k) }
}
$voicePeak=[AD]::Best()
Write-Host ("DIALOGUE voice/BGM max peak = {0:N4}  ({1})" -f $voicePeak, $(if($voicePeak -gt 0.005){'AUDIBLE'}else{'SILENT'}))

# ---------- step 6: wrap up ----------
Write-Host ("dialog boxes during boot: " + $dlgSeen)
Get-Process osakano -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
Write-Host 'VERIFY DONE'
