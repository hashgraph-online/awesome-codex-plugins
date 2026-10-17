import {lstat,readFile,readdir,rm} from 'node:fs/promises';
import {homedir} from 'node:os';
import {join,resolve,dirname} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {insideRoot,noSymlinks,requireValue} from '../control-plane/lib/workflow-paths.mjs';
import {preflightNativeContextProfileRegistration,installNativeContextProfile} from './native-context-profile.mjs';

const pluginRoot=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const defaultCacheRoot=()=>resolve(process.env.CODEX_HOME||join(homedir(),'.codex'),'plugins/cache/codex-agents-workflow/codex-agents-workflow');
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
async function capturePluginSource(sourceRoot){
 const root=resolve(sourceRoot),manifest=JSON.parse(await readFile(join(root,'.codex-plugin/plugin.json'),'utf8'));
 requireValue(manifest.name==='codex-agents-workflow','PLUGIN_IDENTITY','Wrong plugin source');
 const files=[];
 async function visit(relative=''){
  const entries=await readdir(join(root,relative),{withFileTypes:true});
  for(const entry of entries.sort((a,b)=>a.name.localeCompare(b.name))){
   const path=relative?relative+'/'+entry.name:entry.name;
   if(entry.isDirectory())await visit(path);
   else{
    requireValue(entry.isFile(),'PLUGIN_SOURCE_ENTRY','Plugin source contains an unsupported entry: '+path);
    requireValue(!/^agents?\.md$/i.test(entry.name),'PLUGIN_PRIVATE_INSTRUCTIONS','Private maintainer instructions cannot be installed: '+path);
    files.push({path,sha256:sha256(await readFile(join(root,path)))});
   }
  }
 }
 await visit();
 return {root,version:manifest.version,files,sha256:sha256(JSON.stringify(files))};
}
async function registerSource(source,runCli,codexHome){
 const marketplaceRoot=resolve(source.root,'../..');
 const catalog=JSON.parse(await readFile(join(marketplaceRoot,'.agents/plugins/marketplace.json'),'utf8'));
 const entry=catalog.plugins?.find(item=>item.name==='codex-agents-workflow');
 const path=typeof entry?.source==='string'?entry.source:entry?.source?.source==='local'?entry.source.path:undefined;
 requireValue(catalog.name==='codex-agents-workflow'&&typeof path==='string'&&resolve(marketplaceRoot,path)===source.root,
  'PLUGIN_SOURCE_CATALOG','Local marketplace must point at the source being installed');
 const options={stdio:'inherit',windowsHide:true,...(codexHome?{env:{...process.env,CODEX_HOME:codexHome}}:{})};
 await runCli('codex',['plugin','marketplace','add',marketplaceRoot],options);
 await runCli('codex',['plugin','add','codex-agents-workflow@codex-agents-workflow'],options);
}
async function verifyPluginSource(source,deployedRoot){
 for(const file of source.files){
  let actual;
  try{actual=sha256(await readFile(join(deployedRoot,file.path)));}
  catch(error){if(error.code!=='ENOENT')throw error;}
  requireValue(actual===file.sha256,'PLUGIN_SOURCE_MISMATCH','Installed plugin differs from selected source: '+file.path);
 }
 return {source_root:source.root,installed_root:deployedRoot,sha256:source.sha256,file_count:source.files.length};
}
export function selectObsoleteMcpEvents(lines,version,cacheRoot){
 const root=resolve(cacheRoot),marketplace=dirname(root).split(/[\\/]/).at(-1);
 const samePath=(left,right)=>typeof left==='string'&&(process.platform==='win32'
  ?resolve(left).toLowerCase()===resolve(right).toLowerCase():resolve(left)===resolve(right));
 const events=new Map();
 for(const line of lines){
  if(!line)continue;let event;try{event=JSON.parse(line);}catch{continue;}
  if(event?.phase==='resolved'&&event.version===version&&samePath(event.namespace,root)
   &&event.marketplace===marketplace&&event.pluginId===`codex-agents-workflow@${marketplace}`
   &&samePath(event.entry,join(root,version,'control-plane/server.mjs'))
   &&Number.isInteger(event.pid)&&event.pid>0&&Number.isFinite(Date.parse(event.at)))
   events.set(event.pid,{pid:event.pid,at:event.at});
 }
 return [...events.values()];
}
async function observedObsoleteMcpVersions(currentVersion,cacheRoot,codexHome){
 const home=resolve(codexHome??process.env.CODEX_HOME??join(homedir(),'.codex'));
 let lines;
 try{lines=(await readFile(join(home,'codex-agents-workflow/mcp-startup.jsonl'),'utf8')).split(/\r?\n/);}
 catch(error){if(error.code==='ENOENT')return [];throw error;}
 const versions=new Set();
 for(const line of lines){
  if(!line)continue;let event;try{event=JSON.parse(line);}catch{continue;}
  const version=event?.version;
  if(typeof version==='string'&&/^[0-9][A-Za-z0-9.+_-]*$/.test(version)&&version!==currentVersion
   &&selectObsoleteMcpEvents([line],version,cacheRoot).length)versions.add(version);
 }
 return [...versions].sort();
}
async function releaseObsoleteMcpProcesses(version,cacheRoot){
 if(process.platform!=='win32')return [];
 const home=resolve(process.env.CODEX_HOME||join(homedir(),'.codex'));
 let lines;
 try{lines=(await readFile(join(home,'codex-agents-workflow/mcp-startup.jsonl'),'utf8')).split(/\r?\n/);}
 catch(error){if(error.code==='ENOENT')return [];throw error;}
 const events=selectObsoleteMcpEvents(lines,version,cacheRoot);
 if(!events.length)return [];
 const script=`$ErrorActionPreference='Stop'
$events=$env:WORKFLOW_OBSOLETE_MCP_EVENTS | ConvertFrom-Json
$stopped=@()
# Take one process snapshot; hundreds of historical PIDs must not each issue a
# separate WMI query. The creation-time and command checks below still fence PID reuse.
$processes=@{}
foreach($candidate in @(Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction Stop)){
 $processes[[int]$candidate.ProcessId]=$candidate
}
foreach($event in @($events)){
 $process=$processes[[int]$event.pid]
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
  env:{...process.env,WORKFLOW_OBSOLETE_MCP_EVENTS:JSON.stringify(events)}}).trim();
 if(!stdout)return [];
 const parsed=JSON.parse(stdout);return Array.isArray(parsed)?parsed:[parsed];
}

export async function retireObsoleteVersions(cacheRoot,currentVersion,{remove=rm,release=releaseObsoleteMcpProcesses,observedVersions=[]}={}){
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
  const stopped=await release(entry.name,root);if(stopped.length)released.push({version:entry.name,count:stopped.length});
  await remove(target,{recursive:true,force:false,maxRetries:3,retryDelay:50});removed.push(entry.name);
 }
 // The standard CLI can remove old directories itself. Persisted startup
 // identity remains sufficient for the existing exact PID/time/command check.
 for(const version of observedVersions){
  if(version===currentVersion||entries.some(entry=>entry.name===version))continue;
  const stopped=await release(version,root);if(stopped.length)released.push({version,count:stopped.length});
 }
 return {removed_versions:removed.sort(),released_processes:released};
}

// Installation keeps one active version. Obsolete cache directories are not a
// rollback mechanism and must not silently accumulate after the CLI succeeds.
export async function installLocal({
 install,runCli=execFileSync,sourceRoot,
 cacheRoot=defaultCacheRoot(),currentVersion,remove=rm,release=releaseObsoleteMcpProcesses,codexHome,
}={}) {
 // The CLI installs its registered marketplace, not the script's directory.
 // Bind normal local installation to this checkout before invoking plugin add.
 // Injected legacy installer fixtures can omit sourceRoot; real installs cannot.
 if(!install)sourceRoot??=pluginRoot;
 const source=sourceRoot?await capturePluginSource(sourceRoot):undefined;
 currentVersion??=source?.version??JSON.parse(await readFile(join(pluginRoot,'.codex-plugin/plugin.json'),'utf8')).version;
 if(source)requireValue(currentVersion===source.version,'PLUGIN_SOURCE_VERSION','Selected source version differs from requested installation');
 preflightNativeContextProfileRegistration({codexHome});
 const observedVersions=await observedObsoleteMcpVersions(currentVersion,cacheRoot,codexHome);
 // Normal updates must not sever every current-version client before the CLI
 // even runs. A sharing violation remains an explicit install failure; only
 // obsolete-version retirement after success may release its exact processes.
 if(install)await install();else await registerSource(source,runCli,codexHome);
 const verifiedSource=source?await verifyPluginSource(source,resolve(cacheRoot,currentVersion)):undefined;
 const native_context_profile=installNativeContextProfile({codexHome,deployedPluginRoot:resolve(cacheRoot,currentVersion)});
 const retired=await retireObsoleteVersions(cacheRoot,currentVersion,{remove,release,observedVersions});
 return {installed:true,retained_versions:[],...retired,native_context_profile,...(verifiedSource?{source:verifiedSource}:{}),
  mcp_connection_refresh_required:retired.released_processes.length>0};
}

if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
 const manifest=JSON.parse(await readFile(join(pluginRoot,'.codex-plugin/plugin.json'),'utf8'));
 requireValue(manifest.name==='codex-agents-workflow','PLUGIN_IDENTITY','Wrong plugin source');
 console.log(JSON.stringify(await installLocal()));
}
