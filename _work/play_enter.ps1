Add-Type @"
using System;using System.Text;using System.Runtime.InteropServices;
public class P {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p);
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr SetFocus(IntPtr h);
  [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool c);
  [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint dx,uint dy,uint d,IntPtr e);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte sc, uint f, IntPtr e);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after,int x,int y,int cx,int cy,uint flags);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
}
"@
[P]::SetProcessDPIAware()|Out-Null
Add-Type -AssemblyName System.Drawing
$OUT='E:\game\_work'
$ps=Get-Process osakano -EA SilentlyContinue
if(-not $ps){ "no osakano running"; exit }
$pid0=$ps[0].Id
# find main window
$script:H=[IntPtr]::Zero
$cb=[P+EnumProc]{ param($h,$x)
  $wp=0;[P]::GetWindowThreadProcessId($h,[ref]$wp)|Out-Null
  if($wp -eq $pid0 -and [P]::IsWindowVisible($h)){
    $c=New-Object Text.StringBuilder 64;[P]::GetClassName($h,$c,64)|Out-Null
    $r=New-Object P+RECT;[P]::GetWindowRect($h,[ref]$r)|Out-Null
    if($c.ToString() -ne '#32770' -and ($r.R-$r.L) -gt 500){ $script:H=$h }
  }; return $true }
[P]::EnumWindows($cb,[IntPtr]::Zero)|Out-Null
if($script:H -eq [IntPtr]::Zero){ "no main window"; exit }
$h=$script:H
"main window h=$h"

function Shot($path){
  $r=New-Object P+RECT;[P]::GetWindowRect($h,[ref]$r)|Out-Null
  $w=$r.R-$r.L;$ht=$r.B-$r.T
  $bmp=New-Object Drawing.Bitmap $w,$ht;$g=[Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.L,$r.T,0,0,(New-Object Drawing.Size($w,$ht)));$bmp.Save($path);$g.Dispose();$bmp.Dispose()
  Write-Host "  shot $path"
}
function ForceFocus(){
  $fg=[P]::GetCurrentThreadId()
  $tt=0;[P]::GetWindowThreadProcessId($h,[ref]$tt)|Out-Null
  [P]::AttachThreadInput($fg,$tt,$true)|Out-Null
  [P]::BringWindowToTop($h)|Out-Null
  [P]::SetForegroundWindow($h)|Out-Null
  [P]::SetFocus($h)|Out-Null
  [P]::AttachThreadInput($fg,$tt,$false)|Out-Null
}
function Hover($fx,$fy){
  $r=New-Object P+RECT;[P]::GetWindowRect($h,[ref]$r)|Out-Null
  $x=[int]($r.L+($r.R-$r.L)*$fx);$y=[int]($r.T+($r.B-$r.T)*$fy)
  [P]::SetCursorPos($x,$y)|Out-Null
  Write-Host "  hover $x,$y"
}
function Enter(){ [P]::keybd_event(0x0D,0,0,[IntPtr]::Zero); Start-Sleep -Milliseconds 60; [P]::keybd_event(0x0D,0,2,[IntPtr]::Zero) }
function ClickHere($fx,$fy){
  $r=New-Object P+RECT;[P]::GetWindowRect($h,[ref]$r)|Out-Null
  $x=[int]($r.L+($r.R-$r.L)*$fx);$y=[int]($r.T+($r.B-$r.T)*$fy)
  [P]::SetCursorPos($x,$y)|Out-Null;Start-Sleep -Milliseconds 120
  [P]::mouse_event(2,0,0,0,[IntPtr]::Zero);Start-Sleep -Milliseconds 200;[P]::mouse_event(4,0,0,0,[IntPtr]::Zero)
}
[P]::SetWindowPos($h,[IntPtr]-1,0,0,0,0,(0x1 -bor 0x2 -bor 0x40))|Out-Null
ForceFocus
# hover New Game and press ENTER to start
Hover 0.123 0.398; Start-Sleep -Milliseconds 400
ForceFocus
Enter; Start-Sleep -Milliseconds 2200
Shot "$OUT\p_start.png"
# also try a deliberate click on New Game in case ENTER didn't take
ClickHere 0.123 0.398; Start-Sleep -Milliseconds 2200
Shot "$OUT\p_start2.png"
# advance prologue: alternate ENTER and click-center, capture frames
for($k=0;$k -lt 10;$k++){
  ForceFocus; Enter; Start-Sleep -Milliseconds 700
  ClickHere 0.5 0.6; Start-Sleep -Milliseconds 700
  Shot ("$OUT\p_dlg{0}.png" -f $k)
}
Write-Host "DONE"
