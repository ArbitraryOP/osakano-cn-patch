param([int]$Seconds = 6)
Add-Type @"
using System;
using System.Runtime.InteropServices;
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDeviceEnumerator { int EnumAudioEndpoints(int d,int m,out IntPtr c); int GetDefaultAudioEndpoint(int f,int r,out IMMDevice e); }
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDevice { int Activate([MarshalAs(UnmanagedType.LPStruct)]Guid iid,int ctx,IntPtr p,[MarshalAs(UnmanagedType.IUnknown)]out object o); }
[ComImport, Guid("C02216F6-8C67-4B5B-9D00-D008E73E0064"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMeter { int GetPeakValue(out float p); }
public static class A {
  public static float Peak(){ var t=Type.GetTypeFromCLSID(new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"));
    var e=(IMMDeviceEnumerator)Activator.CreateInstance(t); IMMDevice d; e.GetDefaultAudioEndpoint(0,0,out d);
    object o; d.Activate(typeof(IMeter).GUID,1,IntPtr.Zero,out o); float pk; ((IMeter)o).GetPeakValue(out pk); return pk; }
}
"@
$max=0.0
for($i=0;$i -lt ($Seconds*10);$i++){ $p=[A]::Peak(); if($p -gt $max){ $max=$p }; Start-Sleep -Milliseconds 100 }
"max device peak over $Seconds s = {0:N4}" -f $max
if($max -gt 0.01){ "RESULT: AUDIO IS PLAYING (peak {0:N4})" -f $max } else { "RESULT: SILENT" }
