Add-Type @"
using System;using System.Collections.Generic;using System.Runtime.InteropServices;
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator { int EnumAudioEndpoints(int f,int mask,out IMMDeviceCollection c); int GetDefaultAudioEndpoint(int f,int r,out IMMDevice e); }
[ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceCollection { int GetCount(out int n); int Item(int i,out IMMDevice d); }
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice { int Activate([MarshalAs(UnmanagedType.LPStruct)]Guid iid,int ctx,IntPtr p,[MarshalAs(UnmanagedType.IUnknown)]out object o);
  int OpenPropertyStore(int a, out IPropertyStore ps); int GetId([MarshalAs(UnmanagedType.LPWStr)]out string id); int GetState(out int st); }
[ComImport, Guid("886d8eeb-8cf2-4446-8d02-cdba1dbdcf99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPropertyStore { int GetCount(out int n); int GetAt(int i,out PROPERTYKEY k); int GetValue(ref PROPERTYKEY k, out PROPVARIANT v); }
[StructLayout(LayoutKind.Sequential)] struct PROPERTYKEY { public Guid fmtid; public int pid; }
[StructLayout(LayoutKind.Explicit)] struct PROPVARIANT { [FieldOffset(0)] public ushort vt; [FieldOffset(8)] public IntPtr p; }
[ComImport, Guid("C02216F6-8C67-4B5B-9D00-D008E73E0064"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMeter { int GetPeakValue(out float p); }
public static class AD {
  static List<IMeter> meters = new List<IMeter>();
  static List<string> names = new List<string>();
  static float[] max;
  static string defId="";
  public static int Init(){
    var t=Type.GetTypeFromCLSID(new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"));
    var e=(IMMDeviceEnumerator)Activator.CreateInstance(t);
    IMMDevice dd; e.GetDefaultAudioEndpoint(0,0,out dd); dd.GetId(out defId);
    IMMDeviceCollection c; e.EnumAudioEndpoints(0,1,out c); int n; c.GetCount(out n);
    for(int i=0;i<n;i++){ IMMDevice d; c.Item(i,out d);
      string id; d.GetId(out id);
      IPropertyStore ps; d.OpenPropertyStore(0,out ps);
      var k=new PROPERTYKEY(); k.fmtid=new Guid("a45c254e-df1c-4efd-8020-67d146a850e0"); k.pid=14;
      PROPVARIANT v; ps.GetValue(ref k,out v); string nm=""; try{ nm=Marshal.PtrToStringUni(v.p); }catch{}
      object o; d.Activate(typeof(IMeter).GUID,1,IntPtr.Zero,out o);
      meters.Add((IMeter)o); names.Add(nm + (id==defId?"  [DEFAULT]":""));
    }
    max=new float[meters.Count]; return meters.Count;
  }
  public static void Sample(){ for(int i=0;i<meters.Count;i++){ float p; meters[i].GetPeakValue(out p); if(p>max[i]) max[i]=p; } }
  public static string Report(){ var s=""; for(int i=0;i<meters.Count;i++){ s+=string.Format("dev {0}: max={1:N4}  {2}\n", i, max[i], names[i]); } return s; }
}
public static class K {
 [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p); public delegate bool EnumProc(IntPtr h, IntPtr p);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, System.Text.StringBuilder s, int n);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte sc, uint f, IntPtr e);
}
"@
$cnt=[AD]::Init(); "active render devices: $cnt"
$gp=Get-Process osakano -EA SilentlyContinue; $script:H=[IntPtr]::Zero
if($gp){ $pid0=$gp[0].Id; $cb=[K+EnumProc]{ param($h,$x) $wp=0;[K]::GetWindowThreadProcessId($h,[ref]$wp)|Out-Null
  if($wp -eq $pid0 -and [K]::IsWindowVisible($h)){ $c=New-Object Text.StringBuilder 64;[K]::GetClassName($h,$c,64)|Out-Null; if($c.ToString() -ne '#32770'){ $script:H=$h } }; return $true }
  [K]::EnumWindows($cb,[IntPtr]::Zero)|Out-Null }
"game window=$($script:H)"
for($t=0;$t -lt 30;$t++){
  if($script:H -ne [IntPtr]::Zero){ [K]::SetForegroundWindow($script:H)|Out-Null; [K]::keybd_event(0x0D,0,0,[IntPtr]::Zero); Start-Sleep -Milliseconds 30; [K]::keybd_event(0x0D,0,2,[IntPtr]::Zero) }
  for($s=0;$s -lt 5;$s++){ [AD]::Sample(); Start-Sleep -Milliseconds 60 }
}
"=== max peak per device (while game advancing) ==="
[AD]::Report()
