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
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
  [DllImport("user32.dll")] public static extern IntPtr FindWindowExW(IntPtr parent, IntPtr after, string cls, string title);
  [DllImport("user32.dll")] public static extern bool PostMessageW(IntPtr h, uint msg, IntPtr wp, IntPtr lp);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x,int y,int cx,int cy,uint flags);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint dx,uint dy,uint d,IntPtr e);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X,Y; }
}
"@
[W]::SetProcessDPIAware() | Out-Null
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference='SilentlyContinue'
$GAME='E:\game\jp\osakano.exe'; $OUT='E:\game\_work'
$WM_COMMAND=0x0111; $HWND_TOPMOST=[IntPtr]-1
$SWP_NOMOVE=0x2; $SWP_NOSIZE=0x1; $SWP_SHOW=0x40; $MD=0x2; $MU=0x4
$YES    = [char]0x662F                       # 是  (Yes)
$QUXIAO = -join @([char]0x53D6,[char]0x6D88)  # 取消 (Cancel)
$ZHONGZHI = -join @([char]0x4E2D,[char]0x6B62)# 中止 (Abort)

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
function Answer-Dialog($hDlg){
  # target is always a confirmed #32770 dialog -> post the proceed/skip ids;
  # a std MessageBox only acts on the id matching a present button, ignores the rest.
  # IDYES=6 (OS warning: run anyway), IDCANCEL=2 (RetryCancel: skip CD), IDABORT=3 (AbortRetryIgnore: skip)
  # OS YesNo is patched out; remaining is the custom CD-drive-error dialog (Retry/Abort/ChangeDrive).
  # It is a DialogBoxIndirectParam custom dialog -> click the middle "ABORT" button physically.
  $r=New-Object W+RECT; [W]::GetWindowRect($hDlg,[ref]$r)|Out-Null
  $x=[int]($r.L + ($r.R-$r.L)*0.532); $y=[int]($r.T + ($r.B-$r.T)*0.886)
  [W]::SetForegroundWindow($hDlg)|Out-Null
  [W]::SetCursorPos($x,$y)|Out-Null; Start-Sleep -Milliseconds 150
  [W]::mouse_event($MD,0,0,0,[IntPtr]::Zero); Start-Sleep -Milliseconds 90
  [W]::mouse_event($MU,0,0,0,[IntPtr]::Zero)
  Write-Host "  clicked ABORT button at phys $x,$y"
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
  [W]::SetCursorPos($p.X,$p.Y)|Out-Null; Start-Sleep -Milliseconds 140
  [W]::mouse_event($MD,0,0,0,[IntPtr]::Zero); Start-Sleep -Milliseconds 90
  [W]::mouse_event($MU,0,0,0,[IntPtr]::Zero)
  Write-Host ("  clickClient ({0:N2},{1:N2}) -> phys {2},{3}" -f $fx,$fy,$p.X,$p.Y)
}
# click by full-WINDOW fraction (matches the GetWindowRect screenshot space the title coords were measured in)
function ClickWindow($h,$fx,$fy){
  $r=New-Object W+RECT; [W]::GetWindowRect($h,[ref]$r)|Out-Null
  $x=[int]($r.L + ($r.R-$r.L)*$fx); $y=[int]($r.T + ($r.B-$r.T)*$fy)
  [W]::SetForegroundWindow($h)|Out-Null
  [W]::SetCursorPos($x,$y)|Out-Null; Start-Sleep -Milliseconds 140
  [W]::mouse_event($MD,0,0,0,[IntPtr]::Zero); Start-Sleep -Milliseconds 90
  [W]::mouse_event($MU,0,0,0,[IntPtr]::Zero)
  Write-Host ("  clickWin ({0:N3},{1:N3}) -> phys {2},{3}" -f $fx,$fy,$x,$y)
}

Get-Process osakano -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
Start-Sleep -Milliseconds 500
$proc = Start-Process $GAME -PassThru; $pid0=$proc.Id
Write-Host "launched pid=$pid0"
$main=$null
for($i=0;$i -lt 60;$i++){
  $wins = Get-Wins $pid0
  foreach($w in ($wins | Where-Object {$_.Cls -eq '#32770'})){ Answer-Dialog $w.H }
  $cand = $wins | Where-Object {$_.Cls -ne '#32770' -and $_.W -gt 500 -and $_.Ht -gt 400}
  if($cand){ $main=($cand | Sort-Object {$_.W*$_.Ht} -Descending | Select-Object -First 1); Write-Host "main found iter=$i size=$($main.W)x$($main.Ht)"; break }
  Start-Sleep -Milliseconds 400
}
if($main -eq $null){ Write-Host "NO MAIN WINDOW"; exit }
$h=$main.H
[W]::BringWindowToTop($h)|Out-Null; [W]::SetForegroundWindow($h)|Out-Null
[W]::SetWindowPos($h,$HWND_TOPMOST,0,0,0,0,($SWP_NOMOVE -bor $SWP_NOSIZE -bor $SWP_SHOW))|Out-Null
Start-Sleep -Milliseconds 900
# in case more dialogs pop after window shows (CD-DA), keep clearing for 3s
for($i=0;$i -lt 6;$i++){ foreach($w in (Get-Wins $pid0 | Where-Object {$_.Cls -eq '#32770'})){ Answer-Dialog $w.H }; Start-Sleep -Milliseconds 400 }
# advance publisher logo / age disclaimer to title
ClickClient $h 0.5 0.5; Start-Sleep -Milliseconds 1200
ClickClient $h 0.5 0.5; Start-Sleep -Milliseconds 1200
ClickClient $h 0.5 0.5; Start-Sleep -Milliseconds 1000
Shot $h "$OUT\v_title.png"
# click New Game (はじめから): top-left menu item, window-fraction (0.123, 0.398)
ClickWindow $h 0.123 0.398; Start-Sleep -Milliseconds 2000
Shot $h "$OUT\v_afterNG.png"
# advance prologue dialogue with center clicks, capture several frames
for($k=0;$k -lt 10;$k++){
  ClickClient $h 0.5 0.5; Start-Sleep -Milliseconds 1100
  Shot $h ("$OUT\v_dlg{0}.png" -f $k)
}
Write-Host "DONE"
