import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
// Hold the same POSIX disposition interval as libuv unlink, on the one exact
// caller-owned fixture path. Never inspect/kill an unrelated process.
export async function holdOwnedDeleteDisposition(path){
 const native=`using System;using System.Runtime.InteropServices;
 public static class OwnedDeleteFixture {
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] public static extern IntPtr CreateFileW(string p,uint a,uint s,IntPtr q,uint d,uint f,IntPtr t);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern bool CloseHandle(IntPtr h);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern bool SetFileInformationByHandle(IntPtr h,int c,ref uint i,uint n);
 public static int Error(){return Marshal.GetLastWin32Error();}}
 `;
 const script=`$ErrorActionPreference='Stop';Add-Type -TypeDefinition @'
${native}
'@;
$h=[OwnedDeleteFixture]::CreateFileW($env:OWNED_DELETE_FIXTURE_PATH,0x10080,7,[IntPtr]::Zero,3,0x02000000,[IntPtr]::Zero);
if($h -eq [IntPtr](-1)){throw ('Open holder: '+[OwnedDeleteFixture]::Error())};
try{$flags=[uint32]19;if(-not [OwnedDeleteFixture]::SetFileInformationByHandle($h,21,[ref]$flags,4)){throw ('Disposition: '+[OwnedDeleteFixture]::Error())};[Console]::WriteLine('pending');[Console]::Out.Flush();[Console]::ReadLine()|Out-Null;}
finally{if(-not [OwnedDeleteFixture]::CloseHandle($h)){throw 'Owned holder close failed'}}`;
 const child=spawn('powershell.exe',['-NoProfile','-NonInteractive','-EncodedCommand',Buffer.from(script,'utf16le').toString('base64')],
  {windowsHide:true,env:{...process.env,OWNED_DELETE_FIXTURE_PATH:path},stdio:['pipe','pipe','pipe']});
 let stderr='';child.stderr.on('data',bytes=>stderr+=bytes);const lines=createInterface({input:child.stdout});
 const closed=new Promise((done,reject)=>{child.once('error',reject);child.once('close',(code,signal)=>done({code,signal}));});
 let timer;
 try{assert.equal(await Promise.race([new Promise(done=>lines.once('line',done)),
  closed.then(status=>{throw new Error(`Owned holder exited ${status.code}: ${stderr}`);}),
  new Promise((_,reject)=>timer=setTimeout(()=>reject(new Error('Owned holder readiness timeout')),10000))]),'pending');}
 catch(error){if(child.exitCode===null&&child.signalCode===null)child.kill();await closed;throw error;}
 finally{clearTimeout(timer);lines.close();}
 let stopping;
 return ()=>stopping??=(async()=>{child.stdin.end('close\n');const result=await closed;assert.equal(result.code,0,stderr);})();
}
