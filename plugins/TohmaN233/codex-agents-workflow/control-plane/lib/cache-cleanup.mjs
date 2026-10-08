import {readdir,readFile,lstat,unlink,rm} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {randomUUID} from 'node:crypto';
import {insideRoot,noSymlinks,requireValue} from './workflow-paths.mjs';
import {writeDurableJSON} from './workflow-events.mjs';
import {digest,canonicalJSON} from './workflow-revisions.mjs';

const exec=promisify(execFile);
const hashPattern=/^[a-f0-9]{64}$/;
function hashes(value,result=new Set()) {
  if(typeof value==='string' && hashPattern.test(value))result.add(value);
  else if(value && typeof value==='object')for(const item of Object.values(value))hashes(item,result);
  return result;
}
async function fileEntry(root,path,kind) {
  insideRoot(root,path);await noSymlinks(path);const info=await lstat(path);
  requireValue(info.isFile() && info.nlink===1,'CACHE_FILE_TYPE','Cache cleanup requires regular unlinked files');
  return {path,kind,bytes:info.size,sha256:digest(await readFile(path))};
}

// All retained metadata (including generation provenance) contributes pins.
// Mark first, then sweep revisions, then blobs. Never delete Run evidence.
export async function workflowCachePlan(store,runs) {
  const live=await store.list(),keep=new Set(),snapshots=[];
  for(const pack of live)hashes(pack,keep);
  for(const run of await runs.list())hashes((await runs.read(run.run_id)).pins,keep);
  for(const pack of live)for(const revision of await store.revisions(pack.workflow.id)) {
    snapshots.push(await store.snapshot(pack.workflow.id,revision.revision_hash));
  }
  let changed=true;
  while(changed) {const size=keep.size;for(const pack of snapshots)if(keep.has(pack.revision_hash))hashes(pack,keep);changed=keep.size!==size;}
  const files=[];
  for(const pack of live) {
    const root=insideRoot(store.root,join(store.root,`wf-${pack.workflow.id}.pack`));
    const retained=new Set();
    for(const old of snapshots.filter(p=>p.workflow.id===pack.workflow.id)) {
      if(keep.has(old.revision_hash))for(const item of old.resources)retained.add(item.sha256);
      else files.push(await fileEntry(root,join(root,'revisions',old.revision_hash+'.json'),'workflow_revision'));
    }
    await noSymlinks(join(root,'objects'));
    for(const item of await readdir(join(root,'objects'),{withFileTypes:true})) {
      requireValue(item.isFile() && hashPattern.test(item.name),'CACHE_OBJECT_TYPE','Unexpected Workflow object entry');
      if(!retained.has(item.name))files.push(await fileEntry(root,join(root,'objects',item.name),'workflow_resource'));
    }
  }
  return {files,retained_revisions:snapshots.length-files.filter(f=>f.kind==='workflow_revision').length};
}

export async function pluginInventory(cacheRoot,env,{platform=process.platform,execImpl=exec}={}) {
  // Only version names leave this probe. Never expose process command lines.
  const script=`$ErrorActionPreference='Stop'
$cacheRoot=$env:WORKFLOW_CLEANUP_CACHE_ROOT
$registryText=(& codex plugin list --marketplace codex-agents-workflow --json | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect installed plugin registry' }
$registry=$registryText | ConvertFrom-Json
$installed=@($registry.installed | Where-Object { $_.pluginId -eq 'codex-agents-workflow@codex-agents-workflow' } | ForEach-Object { $_.version })
if ($installed.Count -ne 1) { throw 'Expected exactly one installed Workflow plugin' }
$commands=@(Get-CimInstance Win32_Process | ForEach-Object { if ($_.CommandLine) { $_.CommandLine.Replace('/','\\').ToLowerInvariant() } })
$active=@(Get-ChildItem -LiteralPath $cacheRoot -Directory | Where-Object { $candidate=$_.FullName.ToLowerInvariant(); @($commands | Where-Object { $_.Contains($candidate) }).Count -gt 0 } | ForEach-Object { $_.Name })
$hosts=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'codex.exe' -and $_.CommandLine -match 'app-server' } | ForEach-Object { @{pid=$_.ProcessId;started_at=$_.CreationDate.ToUniversalTime().ToString('o')} })
@{installed=$installed;active=$active;hosts=$hosts} | ConvertTo-Json -Depth 4 -Compress`;
  let state;
  if(platform==='win32'){
    const {stdout}=await execImpl('powershell.exe',['-NoProfile','-NonInteractive','-Command',script],{windowsHide:true,timeout:30000,maxBuffer:65536,env:{...env,WORKFLOW_CLEANUP_CACHE_ROOT:cacheRoot}});
    state=JSON.parse(stdout);
  }else{
    const {stdout:registryText}=await execImpl('codex',['plugin','list','--marketplace','codex-agents-workflow','--json'],{env,timeout:30000,maxBuffer:65536});
    const registry=JSON.parse(registryText);
    requireValue(Array.isArray(registry.installed),'CACHE_REGISTRY','Codex did not return an installed-plugin inventory');
    // ps exists on both Linux and macOS. Keep command lines inside this probe;
    // only plugin versions and exact host PID/start evidence leave it.
    const {stdout}=await execImpl('ps',['-axww','-o','pid=,lstart=,command='],{env:{...env,LC_ALL:'C'},timeout:10000,maxBuffer:4*1024*1024});
    const processes=stdout.split(/\r?\n/).filter(line=>line.trim()).map(line=>{
      const match=/^\s*(\d+)\s+(\w{3}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4})\s+(.+)$/.exec(line);
      requireValue(match&&Number.isFinite(Date.parse(match[2])),'CACHE_PROCESS_SCHEMA','Process inventory returned incomplete PID/start evidence');
      return {pid:Number(match[1]),started_at:new Date(match[2]).toISOString(),command:match[3]};
    });
    const entries=await readdir(cacheRoot,{withFileTypes:true});
    state={installed:registry.installed.filter(item=>item.pluginId==='codex-agents-workflow@codex-agents-workflow').map(item=>item.version),
      active:entries.filter(item=>item.isDirectory()&&processes.some(row=>row.command.includes(join(cacheRoot,item.name)+'/'))).map(item=>item.name),
      hosts:processes.filter(row=>/(?:^|\/)codex(?:\s|$)/.test(row.command)&&/\bapp-server\b/.test(row.command)).map(({pid,started_at})=>({pid,started_at}))};
  }
  requireValue(Array.isArray(state.installed)&&state.installed.length===1&&Array.isArray(state.active)&&Array.isArray(state.hosts),'CACHE_REGISTRY','Invalid installed plugin or process inventory');
  const retentionPath=resolve(cacheRoot,'../../../../codex-agents-workflow/runtime-retention.json');
  let retention={versions:{}};
  try{retention=JSON.parse(await readFile(retentionPath,'utf8'));}catch(error){if(error.code!=='ENOENT')throw error;}
  const hostKey=h=>`${h.pid}:${Math.floor(Date.parse(h.started_at)/1000)}`;
  const live=new Set(state.hosts.map(hostKey));
  state.active.push(...Object.entries(retention.versions).filter(([,hosts])=>hosts.some(h=>live.has(hostKey(h)))).map(([version])=>version));
  return state;
}
async function treeFiles(root,path=root,result=[]) {
  if(path!==root)insideRoot(root,path);await noSymlinks(path);
  for(const item of await readdir(path,{withFileTypes:true})) {
    const next=insideRoot(root,join(path,item.name));await noSymlinks(next);
    if(item.isDirectory())await treeFiles(root,next,result);
    else result.push(await fileEntry(root,next,'plugin_file'));
    requireValue(result.length<=50000,'CACHE_SCAN_LIMIT','Plugin cache exceeds scan limit');
  }
  return result;
}
export async function pluginCachePlan(home,{env=process.env,inventory=pluginInventory}={}) {
  const root=resolve(home,'plugins/cache/codex-agents-workflow/codex-agents-workflow');
  try {await lstat(root);}catch(error){if(error.code==='ENOENT')return {directories:[],retained_versions:[]};throw error;}
  await noSymlinks(root);
  const state=await inventory(root,env);
  requireValue(Array.isArray(state.installed) && state.installed.length===1 && Array.isArray(state.active),'CACHE_REGISTRY','Invalid installed plugin inspection');
  const keep=new Set([...state.installed,...state.active]);
  const pathKey=path=>process.platform==='win32'?path.replaceAll('\\','/').toLowerCase():path;
  const current=pathKey(fileURLToPath(import.meta.url));
  const config=await readFile(join(home,'config.toml'),'utf8');
  const directories=[];
  for(const entry of await readdir(root,{withFileTypes:true})) {
    const path=insideRoot(root,join(root,entry.name));await noSymlinks(path);
    requireValue(entry.isDirectory() && /^[0-9][A-Za-z0-9.+_-]*$/.test(entry.name),'CACHE_VERSION_ENTRY','Unexpected plugin version entry');
    if(current.startsWith(pathKey(path)+'/') || config.includes(entry.name))keep.add(entry.name);
    if(keep.has(entry.name))continue;
    // Interrupted installs can leave a version directory without a manifest.
    // Its exact plugin-cache namespace, version name and scanned contents still
    // identify a cleanup candidate; a present manifest must match this plugin.
    const manifestPath=join(path,'.codex-plugin/plugin.json');
    let manifest;
    try {await noSymlinks(manifestPath);manifest=JSON.parse(await readFile(manifestPath,'utf8'));}
    catch(error){if(error.code!=='ENOENT')throw error;}
    if(manifest!==undefined)requireValue(manifest?.name==='codex-agents-workflow' && manifest.version===entry.name,'CACHE_PLUGIN_ID','Cached plugin identity differs');
    const files=await treeFiles(path);
    directories.push({path,version:entry.name,manifest_present:manifest!==undefined,bytes:files.reduce((n,f)=>n+f.bytes,0),fingerprint:digest(canonicalJSON(files))});
  }
  return {directories,retained_versions:[...keep]};
}
export async function cleanupCaches({store,runs,home,auditRoot,env=process.env,preview=false,inventory,removePluginDirectory=rm}) {
  return store.withWriter(()=>runs.writer.withWriter(async()=>{
    const workflow=await workflowCachePlan(store,runs);
    const plugin=await pluginCachePlan(home,{env,inventory});
    const result={workflow_revisions:workflow.files.filter(f=>f.kind==='workflow_revision').length,workflow_resources:workflow.files.filter(f=>f.kind==='workflow_resource').length,plugin_versions:plugin.directories.length,incomplete_plugin_versions:plugin.directories.filter(d=>!d.manifest_present).map(d=>d.version),bytes:workflow.files.reduce((n,f)=>n+f.bytes,0)+plugin.directories.reduce((n,d)=>n+d.bytes,0),retained_revisions:workflow.retained_revisions,retained_plugin_versions:plugin.retained_versions};
    if(preview)return result;
    const auditPath=insideRoot(auditRoot,join(auditRoot,'cache-cleanup-'+randomUUID()+'.json'));
    const audit={started_at:new Date().toISOString(),status:'running',planned:result,candidates:[...workflow.files,...plugin.directories],deleted:[],deferred:[]};
    await writeDurableJSON(auditPath,audit);
    try {
      for(const file of workflow.files) {
        const actual=await fileEntry(store.root,file.path,file.kind);
        requireValue(actual.sha256===file.sha256,'CACHE_CHANGED','Cache file changed during cleanup');
        await unlink(file.path);audit.deleted.push({path:file.path,bytes:file.bytes});await writeDurableJSON(auditPath,audit);
      }
      // Reinspect process and registry protections immediately before deletion.
      const fresh=await pluginCachePlan(home,{env,inventory});
      for(const directory of plugin.directories) {
        requireValue(fresh.directories.some(d=>d.path===directory.path && d.fingerprint===directory.fingerprint),'CACHE_CHANGED','Plugin version changed or became active; retry cleanup');
        insideRoot(resolve(home,'plugins/cache/codex-agents-workflow/codex-agents-workflow'),directory.path);
        await noSymlinks(directory.path);
        try {await removePluginDirectory(directory.path,{recursive:true});}
        catch(error) {
          if(error.code!=='EBUSY')throw error;
          audit.deferred.push({path:directory.path,version:directory.version,reason:'busy'});
          await writeDurableJSON(auditPath,audit);
          continue;
        }
        audit.deleted.push({path:directory.path,version:directory.version,bytes:directory.bytes});await writeDurableJSON(auditPath,audit);
      }
      const completed={...result,plugin_versions:plugin.directories.length-audit.deferred.length,bytes:audit.deleted.reduce((total,item)=>total+item.bytes,0),deferred_plugin_versions:audit.deferred.map(item=>item.version),retained_plugin_versions:[...new Set([...result.retained_plugin_versions,...audit.deferred.map(item=>item.version)])]};
      audit.status=audit.deferred.length?'partial':'complete';audit.completed=completed;
      await writeDurableJSON(auditPath,audit);return {...completed,audit_file:auditPath};
    }catch(error){audit.status='failed';audit.error=error.message;await writeDurableJSON(auditPath,audit);throw Object.assign(error,{details:{audit_file:auditPath,deleted: audit.deleted.length}});}
  }));
}
