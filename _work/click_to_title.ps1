Add-Type @"
using System;using System.Text;using System.Runtime.InteropServices;
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
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint dx,uint dy,uint d,IntPtr e);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X,Y; }
}
"@
[W]::SetProcessDPIAware()|Out-Null
$ErrorActionPreference='SilentlyContinue'
function Find-Main(){
  $gp=Get-Process osakano -EA SilentlyContinue
  if(-not $gp){ return $null }
  $pid0=$gp[0].Id
  $script:M=$null
  $cb=[W+EnumProc]{ param($h,$x)
    $wp=0;[W]::GetWindowThreadProcessId($h,[ref]$wp)|Out-Null
    if($wp -eq $pid0 -and [W]::IsWindowVisible($h)){
      $c=New-Object Text.StringBuilder 64;[W]::GetClassName($h,$c,64)|Out-Null
      $r=New-Object W+RECT;[W]::GetWindowRect($h,[ref]$r)|Out-Null
      if($c.ToString() -ne '#32770' -and ($r.R-$r.L) -gt 500){ $script:M=$h }
    }; return $true }
  [W]::EnumWindows($cb,[IntPtr]::Zero)|Out-Null
  return $script:M
}
function ClickClient($h,$fx,$fy){
  $c=New-Object W+RECT;[W]::GetClientRect($h,[ref]$c)|Out-Null
  $p=New-Object W+POINT;$p.X=[int]($c.R*$fx);$p.Y=[int]($c.B*$fy)
  [W]::ClientToScreen($h,[ref]$p)|Out-Null
  [W]::SetForegroundWindow($h)|Out-Null
  [W]::SetCursorPos($p.X,$p.Y)|Out-Null;Start-Sleep -Milliseconds 150
  [W]::mouse_event(2,0,0,0,[IntPtr]::Zero);Start-Sleep -Milliseconds 80
  [W]::mouse_event(4,0,0,0,[IntPtr]::Zero)
}
$h=$null
$deadline=(Get-Date).AddSeconds(30)
while((Get-Date) -lt $deadline -and $null -eq $h){ $h=Find-Main; if($null -eq $h){ Start-Sleep -Milliseconds 500 } }
if($null -eq $h){ Write-Host 'no window'; exit 1 }
Write-Host "window found, advancing to title"
Start-Sleep -Milliseconds 1500
ClickClient $h 0.5 0.5; Start-Sleep -Milliseconds 1300
ClickClient $h 0.5 0.5; Start-Sleep -Milliseconds 1300
ClickClient $h 0.5 0.5; Start-Sleep -Milliseconds 1000
Write-Host 'at title (3 clicks done), letting BGM window run'
