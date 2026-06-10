# Drive the game and continuously sample its WASAPI session peak.
# Reliable audio confirmation: if ANY in-game sound (BGM/SE/voice) plays,
# the session goes active and peak rises above 0.
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
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte sc, uint f, IntPtr e);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X,Y; }
}
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator { int EnumAudioEndpoints(int f,int mask,out IMMDeviceCollection c); int GetDefaultAudioEndpoint(int f,int r,out IMMDevice e); }
[ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceCollection { int GetCount(out int n); int Item(int i,out IMMDevice d); }
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice { int Activate([MarshalAs(UnmanagedType.LPStruct)]Guid iid,int ctx,IntPtr p,[MarshalAs(UnmanagedType.IUnknown)]out object o);
  int OpenPropertyStore(int a, out IntPtr ps); int GetId([MarshalAs(UnmanagedType.LPWStr)]out string id); int GetState(out int st); }
[ComImport, Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionManager2 { int GetAudioSessionControl([MarshalAs(UnmanagedType.LPStruct)]Guid g,int f,out IntPtr c);
  int GetSimpleAudioVolume([MarshalAs(UnmanagedType.LPStruct)]Guid g,int f,out IntPtr v); int GetSessionEnumerator(out IAudioSessionEnumerator e); }
[ComImport, Guid("F4B1A599-7266-4319-A8CA-E70ACB11E8CD"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionControl { int GetState(out int s); }
[ComImport, Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionEnumerator { int GetCount(out int n); int GetSession(int i,out IAudioSessionControl s); }
[ComImport, Guid("BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionControl2 { int GetState(out int s); int x1(); int x2(); int x3(); int x4(); int x5(); int x6(); int x7(); int x8();
  int GetSessionIdentifier([MarshalAs(UnmanagedType.LPWStr)]out string id); int GetSessionInstanceIdentifier([MarshalAs(UnmanagedType.LPWStr)]out string id);
  int GetProcessId(out int pid); int IsSystemSoundsSession(); int SetDuckingPreference(bool opt); }
[ComImport, Guid("C02216F6-8C67-4B5B-9D00-D008E73E0064"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioMeterInformation { int GetPeakValue(out float p); }
public static class M {
  static IAudioMeterInformation meter; static IAudioSessionControl2 ctrl;
  public static bool Bind(int pid){
    var t=Type.GetTypeFromCLSID(new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"));
    var en=(IMMDeviceEnumerator)Activator.CreateInstance(t);
    IMMDeviceCollection coll; en.EnumAudioEndpoints(0,1,out coll); int nd; coll.GetCount(out nd);
    for(int d=0; d<nd; d++){ IMMDevice dev; coll.Item(d,out dev); object o;
      if(dev.Activate(typeof(IAudioSessionManager2).GUID,1,IntPtr.Zero,out o)!=0) continue;
      var mgr=(IAudioSessionManager2)o; IAudioSessionEnumerator se; if(mgr.GetSessionEnumerator(out se)!=0) continue;
      int ns; se.GetCount(out ns);
      for(int i=0;i<ns;i++){ IAudioSessionControl sc; if(se.GetSession(i,out sc)!=0) continue;
        var sc2=(IAudioSessionControl2)sc; int p; sc2.GetProcessId(out p);
        if(p==pid){ meter=(IAudioMeterInformation)sc; ctrl=sc2; return true; } } }
    return false;
  }
  public static float Peak(){ if(meter==null) return -1; float p; meter.GetPeakValue(out p); return p; }
  public static int State(){ if(ctrl==null) return -1; int s; ctrl.GetState(out s); return s; }
}
"@
[W]::SetProcessDPIAware()|Out-Null
$ErrorActionPreference='SilentlyContinue'
$MD=0x2;$MU=0x4
function Find-Main($pid0){
  $script:M=$null
  $cb=[W+EnumProc]{ param($h,$x)
    $wp=0;[W]::GetWindowThreadProcessId($h,[ref]$wp)|Out-Null
    if($wp -eq $pid0 -and [W]::IsWindowVisible($h)){
      $c=New-Object Text.StringBuilder 64;[W]::GetClassName($h,$c,64)|Out-Null
      $r=New-Object W+RECT;[W]::GetWindowRect($h,[ref]$r)|Out-Null
      if($c.ToString() -ne '#32770' -and ($r.R-$r.L) -gt 500){ $script:M=$h } }
    return $true }
  [W]::EnumWindows($cb,[IntPtr]::Zero)|Out-Null
  return $script:M
}
function Click($h,$fx,$fy){
  $c=New-Object W+RECT;[W]::GetClientRect($h,[ref]$c)|Out-Null
  $p=New-Object W+POINT;$p.X=[int]($c.R*$fx);$p.Y=[int]($c.B*$fy)
  [W]::ClientToScreen($h,[ref]$p)|Out-Null
  [W]::SetForegroundWindow($h)|Out-Null
  [W]::SetCursorPos($p.X,$p.Y)|Out-Null;Start-Sleep -Milliseconds 120
  [W]::mouse_event($MD,0,0,0,[IntPtr]::Zero);Start-Sleep -Milliseconds 70;[W]::mouse_event($MU,0,0,0,[IntPtr]::Zero)
}
function Peaks($sec){
  $best=0.0; $active=$false
  $end=(Get-Date).AddSeconds($sec)
  while((Get-Date) -lt $end){ $p=[M]::Peak(); if($p -gt $best){$best=$p}; if([M]::State() -eq 1){$active=$true}; Start-Sleep -Milliseconds 40 }
  return [pscustomobject]@{peak=$best;active=$active}
}

$gp=Get-Process osakano -EA SilentlyContinue
if(-not $gp){ Write-Host 'game not running'; exit 1 }
$pid0=$gp[0].Id
if(-not [M]::Bind($pid0)){ Write-Host "no session for pid $pid0"; exit 1 }
$h=$null;$dl=(Get-Date).AddSeconds(20)
while((Get-Date) -lt $dl -and $null -eq $h){ $h=Find-Main $pid0; if(-not $h){Start-Sleep -Milliseconds 400} }
if(-not $h){ Write-Host 'no window'; exit 1 }
Write-Host "bound session + window for pid=$pid0"

# advance logos -> title
1..3 | ForEach-Object { Click $h 0.5 0.5; Start-Sleep -Milliseconds 1200 }
$r=Peaks 3
Write-Host ("TITLE: peak={0:N4} active={1}" -f $r.peak,$r.active)

# wiggle mouse over menu area to trigger cursor SE (move, no click)
$c=New-Object W+RECT;[W]::GetClientRect($h,[ref]$c)|Out-Null
$p=New-Object W+POINT
foreach($fy in 0.40,0.46,0.52,0.58,0.64,0.40,0.52){
  $p.X=[int]($c.R*0.18);$p.Y=[int]($c.B*$fy);$pp=$p
  [W]::ClientToScreen($h,[ref]$pp)|Out-Null;[W]::SetCursorPos($pp.X,$pp.Y)|Out-Null;Start-Sleep -Milliseconds 250
}
$r2=Peaks 2
Write-Host ("MENU HOVER (cursor SE): peak={0:N4} active={1}" -f $r2.peak,$r2.active)

# click New Game candidates (cleared-save menu); test a few y positions, measure between
foreach($fy in 0.40,0.44,0.48){
  Click $h 0.18 $fy
  $rr=Peaks 2
  Write-Host ("after click (0.18,{0:N2}): peak={1:N4} active={2}" -f $fy,$rr.peak,$rr.active)
}
Write-Host 'AUDIO CONFIRM DONE'
