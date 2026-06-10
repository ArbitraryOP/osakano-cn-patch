Add-Type @"
using System;using System.Runtime.InteropServices;
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator { int EnumAudioEndpoints(int f,int mask,out IMMDeviceCollection c); int GetDefaultAudioEndpoint(int f,int r,out IMMDevice e); }
[ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceCollection { int GetCount(out int n); int Item(int i,out IMMDevice d); }
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice { int Activate([MarshalAs(UnmanagedType.LPStruct)]Guid iid,int ctx,IntPtr p,[MarshalAs(UnmanagedType.IUnknown)]out object o);
  int OpenPropertyStore(int a, out IntPtr ps); int GetId([MarshalAs(UnmanagedType.LPWStr)]out string id); int GetState(out int st); }
[ComImport, Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionManager2 {
  int GetAudioSessionControl([MarshalAs(UnmanagedType.LPStruct)]Guid g,int f,out IntPtr c);
  int GetSimpleAudioVolume([MarshalAs(UnmanagedType.LPStruct)]Guid g,int f,out IntPtr v);
  int GetSessionEnumerator(out IAudioSessionEnumerator e); }
[ComImport, Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionEnumerator { int GetCount(out int n); int GetSession(int i,out IAudioSessionControl s); }
[ComImport, Guid("F4B1A599-7266-4319-A8CA-E70ACB11E8CD"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionControl {
  int GetState(out int s);
  int GetDisplayName([MarshalAs(UnmanagedType.LPWStr)]out string n);
  int SetDisplayName(string n, IntPtr g);
  int GetIconPath([MarshalAs(UnmanagedType.LPWStr)]out string p);
  int SetIconPath(string p, IntPtr g);
  int GetGroupingParam(out Guid g);
  int SetGroupingParam(IntPtr g, IntPtr c);
  int RegisterAudioSessionNotification(IntPtr n);
  int UnregisterAudioSessionNotification(IntPtr n); }
[ComImport, Guid("BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionControl2 {
  int GetState(out int s);
  int GetDisplayName([MarshalAs(UnmanagedType.LPWStr)]out string n);
  int SetDisplayName(string n, IntPtr g);
  int GetIconPath([MarshalAs(UnmanagedType.LPWStr)]out string p);
  int SetIconPath(string p, IntPtr g);
  int GetGroupingParam(out Guid g);
  int SetGroupingParam(IntPtr g, IntPtr c);
  int RegisterAudioSessionNotification(IntPtr n);
  int UnregisterAudioSessionNotification(IntPtr n);
  int GetSessionIdentifier([MarshalAs(UnmanagedType.LPWStr)]out string id);
  int GetSessionInstanceIdentifier([MarshalAs(UnmanagedType.LPWStr)]out string id);
  int GetProcessId(out int pid);
  int IsSystemSoundsSession();
  int SetDuckingPreference(bool opt); }
[ComImport, Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface ISimpleAudioVolume {
  int SetMasterVolume(float v, IntPtr g);
  int GetMasterVolume(out float v);
  int SetMute(bool m, IntPtr g);
  int GetMute(out bool m); }
[ComImport, Guid("C02216F6-8C67-4B5B-9D00-D008E73E0064"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioMeterInformation { int GetPeakValue(out float p); }
public static class SES {
  public static string Report(int targetPid, double seconds, bool fix){
    var sb=new System.Text.StringBuilder();
    var t=Type.GetTypeFromCLSID(new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"));
    var en=(IMMDeviceEnumerator)Activator.CreateInstance(t);
    IMMDeviceCollection coll; en.EnumAudioEndpoints(0,1,out coll);
    int nd; coll.GetCount(out nd);
    for(int d=0; d<nd; d++){
      IMMDevice dev; coll.Item(d,out dev);
      object o;
      var iidMgr=typeof(IAudioSessionManager2).GUID;
      if(dev.Activate(iidMgr,1,IntPtr.Zero,out o)!=0) continue;
      var mgr=(IAudioSessionManager2)o;
      IAudioSessionEnumerator se; if(mgr.GetSessionEnumerator(out se)!=0) continue;
      int ns; se.GetCount(out ns);
      for(int i=0;i<ns;i++){
        IAudioSessionControl sc; if(se.GetSession(i,out sc)!=0) continue;
        var sc2=(IAudioSessionControl2)sc;
        int pid; sc2.GetProcessId(out pid);
        if(pid!=targetPid) continue;
        int state; sc.GetState(out state);
        var sav=(ISimpleAudioVolume)sc;
        float vol; sav.GetMasterVolume(out vol);
        bool mute; sav.GetMute(out mute);
        string sid; sc2.GetSessionIdentifier(out sid);
        sb.AppendFormat("dev{0} session pid={1} state={2} sessionVol={3:N3} mute={4}\n  id={5}\n", d, pid, state, vol, mute, sid);
        if(fix){
          sav.SetMasterVolume(1.0f, IntPtr.Zero);
          sav.SetMute(false, IntPtr.Zero);
          float v2; sav.GetMasterVolume(out v2);
          sb.AppendFormat("  -> FIXED: sessionVol set to {0:N3}, unmuted\n", v2);
        }
        var met=(IAudioMeterInformation)sc;
        float max=0;
        var end=DateTime.Now.AddSeconds(seconds);
        while(DateTime.Now<end){ float p; met.GetPeakValue(out p); if(p>max)max=p; System.Threading.Thread.Sleep(50); }
        sb.AppendFormat("  session max peak over {0}s = {1:N4}\n", seconds, max);
      }
    }
    if(sb.Length==0) sb.Append("NO audio session found for pid "+targetPid+"\n");
    return sb.ToString();
  }
}
"@
$gp=Get-Process osakano -EA SilentlyContinue
if(-not $gp){ Write-Host 'game not running'; exit 1 }
$mode=$args[0]
$fix = ($mode -eq 'fix')
Write-Host ([SES]::Report($gp[0].Id, 4.0, $fix))
