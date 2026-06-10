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
}
"@
[W]::SetProcessDPIAware()|Out-Null
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference='SilentlyContinue'
$MD=0x2;$MU=0x4;$OUT='E:\game\_work'
function Find-Main($pid0){ $script:M=$null
  $cb=[W+EnumProc]{ param($h,$x) $wp=0;[W]::GetWindowThreadProcessId($h,[ref]$wp)|Out-Null
    if($wp -eq $pid0 -and [W]::IsWindowVisible($h)){ $c=New-Object Text.StringBuilder 64;[W]::GetClassName($h,$c,64)|Out-Null
      $r=New-Object W+RECT;[W]::GetWindowRect($h,[ref]$r)|Out-Null
      if($c.ToString() -ne '#32770' -and ($r.R-$r.L) -gt 500){ $script:M=$h } }; return $true }
  [W]::EnumWindows($cb,[IntPtr]::Zero)|Out-Null; return $script:M }
function Click($h,$fx,$fy){ $c=New-Object W+RECT;[W]::GetClientRect($h,[ref]$c)|Out-Null
  $p=New-Object W+POINT;$p.X=[int]($c.R*$fx);$p.Y=[int]($c.B*$fy);[W]::ClientToScreen($h,[ref]$p)|Out-Null
  [W]::SetForegroundWindow($h)|Out-Null;[W]::SetCursorPos($p.X,$p.Y)|Out-Null;Start-Sleep -Milliseconds 120
  [W]::mouse_event($MD,0,0,0,[IntPtr]::Zero);Start-Sleep -Milliseconds 70;[W]::mouse_event($MU,0,0,0,[IntPtr]::Zero) }
function Shot($h,$path){ $r=New-Object W+RECT;[W]::GetWindowRect($h,[ref]$r)|Out-Null
  $w=$r.R-$r.L;$ht=$r.B-$r.T; if($w -le 0){return}
  $bmp=New-Object Drawing.Bitmap $w,$ht;$g=[Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.L,$r.T,0,0,(New-Object Drawing.Size($w,$ht)));$bmp.Save($path);$g.Dispose();$bmp.Dispose() }
function PeakWhile($sec){ $best=0.0;$end=(Get-Date).AddSeconds($sec)
  while((Get-Date) -lt $end){ $p=[M]::Peak(); if($p -gt $best){$best=$p}; Start-Sleep -Milliseconds 35 }; return $best }

$gp=Get-Process osakano -EA SilentlyContinue; if(-not $gp){ Write-Host 'not running'; exit 1 }
$pid0=$gp[0].Id; [M]::Bind($pid0)|Out-Null
$h=Find-Main $pid0; if(-not $h){ Write-Host 'no window'; exit 1 }
Write-Host "pid=$pid0 driving New Game"
# click はじめから (top menu item)
Click $h 0.16 0.44; Start-Sleep -Milliseconds 800
Shot $h "$OUT\vt_afterNG1.png"
# a confirm/diff dialog may appear; click likely 'yes' positions then advance
Click $h 0.40 0.56; Start-Sleep -Milliseconds 600
Click $h 0.16 0.44; Start-Sleep -Milliseconds 1500
Shot $h "$OUT\vt_afterNG2.png"
# advance prologue with ENTER + center click, measure voice peak across lines
$overall=0.0
for($k=0;$k -lt 12;$k++){
  [W]::SetForegroundWindow($h)|Out-Null
  [W]::keybd_event(0x0D,0,0,[IntPtr]::Zero);Start-Sleep -Milliseconds 50;[W]::keybd_event(0x0D,0,2,[IntPtr]::Zero)
  Click $h 0.5 0.62
  $pk=PeakWhile 1.6
  if($pk -gt $overall){$overall=$pk}
  Write-Host ("line {0}: peak={1:N4}" -f $k,$pk)
  if($k -eq 5){ Shot $h "$OUT\vt_dlg_mid.png" }
}
Shot $h "$OUT\vt_dlg_end.png"
Write-Host ("OVERALL dialogue peak = {0:N4}  ({1})" -f $overall, $(if($overall -gt 0.01){'AUDIBLE - voice/BGM playing'}else{'silent'}))
Write-Host 'VOICE TEST DONE'
