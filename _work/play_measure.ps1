Add-Type @"
using System;using System.Runtime.InteropServices;using System.Text;
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDeviceEnumerator { int EnumAudioEndpoints(int d,int m,out IntPtr c); int GetDefaultAudioEndpoint(int f,int r,out IMMDevice e); }
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDevice { int Activate([MarshalAs(UnmanagedType.LPStruct)]Guid iid,int ctx,IntPtr p,[MarshalAs(UnmanagedType.IUnknown)]out object o); }
[ComImport, Guid("C02216F6-8C67-4B5B-9D00-D008E73E0064"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMeter { int GetPeakValue(out float p); }
public static class M {
  public static float Peak(){ var t=Type.GetTypeFromCLSID(new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"));
    var e=(IMMDeviceEnumerator)Activator.CreateInstance(t); IMMDevice d; e.GetDefaultAudioEndpoint(0,0,out d);
    object o; d.Activate(typeof(IMeter).GUID,1,IntPtr.Zero,out o); float pk; ((IMeter)o).GetPeakValue(out pk); return pk; }
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p);
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte sc, uint f, IntPtr e);
}
"@
$ps=Get-Process osakano -EA SilentlyContinue
if(-not $ps){ "no osakano running"; exit }
$pid0=$ps[0].Id; $script:H=[IntPtr]::Zero
$cb=[M+EnumProc]{ param($h,$x)
  $wp=0;[M]::GetWindowThreadProcessId($h,[ref]$wp)|Out-Null
  if($wp -eq $pid0 -and [M]::IsWindowVisible($h)){ $c=New-Object Text.StringBuilder 64;[M]::GetClassName($h,$c,64)|Out-Null
    if($c.ToString() -ne '#32770'){ $script:H=$h } }; return $true }
[M]::EnumWindows($cb,[IntPtr]::Zero)|Out-Null
"game window=$($script:H)"
$max=0.0
for($k=0;$k -lt 24;$k++){
  [M]::SetForegroundWindow($script:H)|Out-Null
  [M]::keybd_event(0x0D,0,0,[IntPtr]::Zero); Start-Sleep -Milliseconds 40; [M]::keybd_event(0x0D,0,2,[IntPtr]::Zero)  # ENTER advance
  for($s=0;$s -lt 8;$s++){ $p=[M]::Peak(); if($p -gt $max){ $max=$p }; Start-Sleep -Milliseconds 80 }
}
"MAX peak while advancing 24 voiced lines = {0:N4}" -f $max
if($max -gt 0.01){ "AUDIO PLAYS" } else { "NO AUDIO (game silent)" }
