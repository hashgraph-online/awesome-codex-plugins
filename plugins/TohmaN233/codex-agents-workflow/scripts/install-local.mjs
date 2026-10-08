import {lstat,readFile,readdir,rm} from 'node:fs/promises';
import {homedir} from 'node:os';
import {join,resolve,dirname} from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {insideRoot,noSymlinks,requireValue} from '../control-plane/lib/workflow-paths.mjs';

const pluginRoot=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const defaultCacheRoot=()=>resolve(process.env.CODEX_HOME||join(homedir(),'.codex'),'plugins/cache/codex-agents-workflow/codex-agents-workflow');
async function releaseObsoleteMcpProcesses(version){
 if(process.platform!=='win32')return [];
 const home=resolve(process.env.CODEX_HOME||join(homedir(),'.codex'));
 let lines;
 try{lines=(await readFile(join(home,'codex-agents-workflow/mcp-startup.jsonl'),'utf8')).split(/\r?\n/);}
 catch(error){if(error.code==='ENOENT')return [];throw error;}
 const events=new Map();
 for(const line of lines){
  if(!line)continue;let event;try{event=JSON.parse(line);}catch{continue;}
  if(event?.phase==='resolved'&&event.version===version&&Number.isInteger(event.pid)&&event.pid>0)events.set(event.pid,{pid:event.pid,at:event.at});
 }
 if(!events.size)return [];
 const script=`$ErrorActionPreference='Stop'
$events=$env:WORKFLOW_OBSOLETE_MCP_EVENTS | ConvertFrom-Json
$stopped=@()
foreach($event in @($events)){
 $process=Get-CimInstance Win32_Process -Filter ("ProcessId="+[int]$event.pid) -ErrorAction SilentlyContinue
 if(-not $process){continue}
 $started=[DateTimeOffset]$process.CreationDate
 $observed=[DateTimeOffset]::Parse([string]$event.at)
 $delta=[Math]::Abs(($started.UtcDateTime-$observed.UtcDateTime).TotalSeconds)
 if($process.Name -eq 'node.exe' -and $delta -le 120 -and $process.CommandLine -like '*registeredRoot*codex-agents-workflow*'){
  Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
  $stopped += [int]$process.ProcessId
 }
}
@($stopped) | ConvertTo-Json -Compress`;
 const stdout=execFileSync('powershell.exe',['-NoProfile','-NonInteractive','-Command',script],{encoding:'utf8',windowsHide:true,
  env:{...process.env,WORKFLOW_OBSOLETE_MCP_EVENTS:JSON.stringify([...events.values()])}}).trim();
 if(!stdout)return [];
 const parsed=JSON.parse(stdout);return Array.isArray(parsed)?parsed:[parsed];
}

export async function retireObsoleteVersions(cacheRoot,currentVersion,{remove=rm,release=releaseObsoleteMcpProcesses}={}){
 const root=resolve(cacheRoot);await noSymlinks(root);
 const entries=await readdir(root,{withFileTypes:true});
 requireValue(entries.some(entry=>entry.isDirectory()&&entry.name===currentVersion),'PLUGIN_CACHE_CURRENT','Installed plugin cache does not contain the new version');
 const removed=[],released=[];
 for(const entry of entries){
  requireValue(entry.isDirectory()&&/^[0-9][A-Za-z0-9.+_-]*$/.test(entry.name),'PLUGIN_CACHE_ENTRY','Unexpected plugin cache entry');
  if(entry.name===currentVersion)continue;
  const target=insideRoot(root,join(root,entry.name));await noSymlinks(target);
  requireValue((await lstat(target)).isDirectory(),'PLUGIN_CACHE_ENTRY','Plugin cache version is not a directory');
  try{
   const manifest=JSON.parse(await readFile(join(target,'.codex-plugin/plugin.json'),'utf8'));
   requireValue(manifest?.name==='codex-agents-workflow'&&manifest.version===entry.name,'PLUGIN_CACHE_IDENTITY','Obsolete cache identity differs');
  }catch(error){if(error.code!=='ENOENT')throw error;}
  const stopped=await release(entry.name);if(stopped.length)released.push({version:entry.name,count:stopped.length});
  await remove(target,{recursive:true,force:false,maxRetries:3,retryDelay:50});removed.push(entry.name);
 }
 return {removed_versions:removed.sort(),released_processes:released};
}

// Installation keeps one active version. Obsolete cache directories are not a
// rollback mechanism and must not silently accumulate after the CLI succeeds.
export async function installLocal({
 install=()=>execFileSync('codex',['plugin','add','codex-agents-workflow@codex-agents-workflow'],{stdio:'inherit',windowsHide:true}),
 cacheRoot=defaultCacheRoot(),currentVersion,remove=rm,release=releaseObsoleteMcpProcesses,
}={}) {
 currentVersion??=JSON.parse(await readFile(join(pluginRoot,'.codex-plugin/plugin.json'),'utf8')).version;
 const currentReleased=await release(currentVersion);
 await install();
 const retired=await retireObsoleteVersions(cacheRoot,currentVersion,{remove,release});
 return {installed:true,retained_versions:[],...retired,
  released_processes:[...(currentReleased.length?[{version:currentVersion,count:currentReleased.length}]:[]),...retired.released_processes]};
}

if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
 const manifest=JSON.parse(await readFile(join(pluginRoot,'.codex-plugin/plugin.json'),'utf8'));
 requireValue(manifest.name==='codex-agents-workflow','PLUGIN_IDENTITY','Wrong plugin source');
 console.log(JSON.stringify(await installLocal()));
}
