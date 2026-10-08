import {access,readdir,realpath,stat} from 'node:fs/promises';
import {constants} from 'node:fs';
import {execFile as execFileCallback} from 'node:child_process';
import {promisify} from 'node:util';
import {delimiter,join,parse,resolve,isAbsolute} from 'node:path';
import {homedir,tmpdir} from 'node:os';
import {requireValue} from './workflow-paths.mjs';
import {isPythonRequirement,normalizeExecutableRequirements,runtimeRequirementKey,versionSatisfies} from './runtime-requirements.mjs';
import {readHostRuntimeRegistry,updateRuntimeCandidate,registryPathForConfig} from './host-runtime-registry.mjs';

export {readHostRuntimeRegistry,updateRuntimeCandidate,registryPathForConfig};
const execFile=promisify(execFileCallback);
const suffixes=process.platform==='win32'?['','.exe','.cmd','.bat']:[''];
const pythonProbe=String.raw`import importlib,json,sys
modules=json.loads(sys.argv[1]); failures={}
for name in modules:
 try: importlib.import_module(name)
 except Exception as error: failures[name]=type(error).__name__+': '+str(error)
print(json.dumps({'version':'.'.join(map(str,sys.version_info[:3])),'module_failures':failures}))`;
const failure=(code,message,details={})=>Object.assign(new Error(message),{code,...details});

function validDirectories(directories,label){
 requireValue(Array.isArray(directories)&&directories.length<=64&&directories.every(p=>typeof p==='string'&&isAbsolute(p)),'ENVIRONMENT_DIRECTORIES',`${label} must be a bounded list of absolute directories`);
}

async function directoriesFor(env,extraDirectories,knownDirectories){
 validDirectories(extraDirectories,'Extra tool search directories');validDirectories(knownDirectories,'Known tool search directories');
 const home=env.USERPROFILE||env.HOME||homedir();
 requireValue(isAbsolute(home),'ENVIRONMENT_DIRECTORIES','Host home directory must be absolute');
 const pathDirectories=(env.PATH||env.Path||'').split(delimiter).filter(isAbsolute);
 const condaBases=['Miniconda3','miniconda3','anaconda3'].map(name=>join(home,name));
 const roots=[...condaBases.flatMap(base=>[base,join(base,'Scripts'),join(base,'Library','bin'),join(base,'bin')]),join(home,'scoop','shims'),join(home,'.local','bin'),join(home,'.cargo','bin'),join(home,'.bun','bin'),join(home,'AppData','Local','Microsoft','WinGet','Links'),join(home,'AppData','Roaming','npm')];
 async function children(base){
  if(!base||!isAbsolute(base))return [];
  let entries;try{entries=await readdir(base,{withFileTypes:true});}catch(error){if(['ENOENT','ENOTDIR'].includes(error.code))return [];throw error;}
  requireValue(entries.length<=256,'ENVIRONMENT_DISCOVERY_LIMIT','Host tool directory has too many immediate entries: '+base);
  return entries.filter(item=>item.isDirectory()).map(item=>join(base,item.name)).sort();
 }
 for(const base of [env.ProgramFiles,env['ProgramFiles(x86)'],join(home,'AppData','Local','Programs'),join(home,'.codex','vendor')]){
  for(const child of await children(base))roots.push(child,join(child,'bin'),join(child,'Scripts'));
 }
 const condaEnvBases=[...condaBases.map(base=>join(base,'envs')),join(home,'.conda','envs'),...(env.CONDA_ENVS_PATH||'').split(delimiter).filter(isAbsolute)];
 if(env.CONDA_PREFIX&&isAbsolute(env.CONDA_PREFIX))roots.push(env.CONDA_PREFIX,join(env.CONDA_PREFIX,'Scripts'),join(env.CONDA_PREFIX,'bin'));
 for(const base of condaEnvBases){
  for(const child of await children(base))roots.push(child,join(child,'Scripts'),join(child,'Library','bin'),join(child,'bin'));
 }
 const volumeInputs=[home,...pathDirectories,env.ProgramFiles,env['ProgramFiles(x86)'],...knownDirectories,...extraDirectories].filter(value=>value&&isAbsolute(value));
 const volumes=[...new Set(volumeInputs.map(value=>parse(value).root))];
 for(const volume of volumes){
  for(const name of ['Tools','toolchains','PortableTools','PortableApps']){
   const base=join(volume,name);roots.push(base,join(base,'bin'),join(base,'Scripts'));
   for(const child of await children(base))roots.push(child,join(child,'bin'),join(child,'Scripts'));
  }
 }
 return [...new Set([...knownDirectories,...extraDirectories,...pathDirectories,...roots].filter(isAbsolute).map(p=>resolve(p)))];
}

async function fileIdentity(candidate){
 const info=await stat(candidate);
 requireValue(info.isFile(),'ENVIRONMENT_CANDIDATE_INVALID',`Executable candidate is not a file: ${candidate}`);
 await access(candidate,process.platform==='win32'?constants.F_OK:constants.X_OK);
 return {realpath:await realpath(candidate),size:info.size,mtime_ms:info.mtimeMs};
}

async function runProbe(path,args,env){
 let program=path,probeArgs=args;
 if(process.platform==='win32'&&/\.(?:cmd|bat)$/i.test(path)){
  // Node cannot directly execute command scripts. Only fixed probe arguments
  // enter cmd, and metacharacters in the host path are rejected.
  requireValue(!/[&|<>^%!\r\n]/.test(path),'ENVIRONMENT_PROBE_PATH','Unsafe command-script path for a fixed version probe');
  program=join(process.env.SystemRoot??'C:\\Windows','System32','cmd.exe');
  probeArgs=['/d','/c','call',`"${path}"`,...args];
 }
 return execFile(program,probeArgs,{cwd:tmpdir(),env,windowsHide:true,windowsVerbatimArguments:program!==path,timeout:10000,maxBuffer:65536});
}

export async function probeRuntimeCandidate(requirement,candidate,{env=process.env}={}){
 const [item]=normalizeExecutableRequirements([requirement]);
 requireValue(typeof candidate==='string'&&isAbsolute(candidate),'ENVIRONMENT_CANDIDATE_INVALID','Executable candidate path must be absolute');
 const identity=await fileIdentity(candidate);
 const evidence={...identity,probe_kind:'file-identity'};
 if(item.version||item.python_modules?.length){
  if(isPythonRequirement(item.name)){
   requireValue(!/\.(?:cmd|bat)$/i.test(identity.realpath),'ENVIRONMENT_PROBE_INVALID','Python command scripts cannot safely carry the fixed module probe');
   const {stdout}=await runProbe(identity.realpath,['-c',pythonProbe,JSON.stringify(item.python_modules??[])],env);
   let result;try{result=JSON.parse(stdout.trim());}catch(error){throw failure('ENVIRONMENT_PROBE_INVALID',`Python probe returned invalid JSON for ${item.name}`,{cause:error});}
   requireValue(result&&typeof result.version==='string'&&result.module_failures&&typeof result.module_failures==='object','ENVIRONMENT_PROBE_INVALID',`Python probe returned invalid evidence for ${item.name}`);
   evidence.probe_kind='python';evidence.observed_version=result.version;evidence.python_modules=item.python_modules??[];
   requireValue(Object.keys(result.module_failures).length===0,'ENVIRONMENT_PYTHON_MODULE_MISSING',`Python modules are unavailable for ${item.name}`,{module_failures:result.module_failures});
  }else{
   const {stdout,stderr}=await runProbe(identity.realpath,['--version'],env);
   const match=`${stdout}\n${stderr}`.match(/(?:^|[^\d])v?(\d+(?:\.\d+){0,2})(?!\d)/);
   requireValue(match,'ENVIRONMENT_PROBE_INVALID',`Version probe did not report a supported numeric version for ${item.name}`);
   evidence.probe_kind='version';evidence.observed_version=match[1];
  }
  if(item.version)requireValue(versionSatisfies(evidence.observed_version,item.version,item.name),'ENVIRONMENT_VERSION_MISMATCH',`Version ${evidence.observed_version} does not satisfy ${item.version} for ${item.name}`,{observed_version:evidence.observed_version,required_version:item.version});
 }
 return evidence;
}

async function checked(requirement,path,env){
 try{const evidence=await probeRuntimeCandidate(requirement,path,{env});return {path:evidence.realpath,evidence};}
 catch(error){if(['ENOENT','ENOTDIR','EACCES','EPERM','ENOEXEC','EINVAL','ENVIRONMENT_CANDIDATE_INVALID','ENVIRONMENT_PROBE_INVALID','ENVIRONMENT_PROBE_PATH','ENVIRONMENT_VERSION_MISMATCH','ENVIRONMENT_PYTHON_MODULE_MISSING','ETIMEDOUT'].includes(error.code)||error.syscall==='spawn'||error.killed||typeof error.code==='number')return {rejection:{path,reason:error.message,cause_code:String(error.code??'PROBE_FAILED'),...(error.module_failures?{module_failures:error.module_failures}:{}),...(error.observed_version?{observed_version:error.observed_version,required_version:error.required_version}:{})}};throw error;}
}

export async function prepareRuntimeEnvironment(requirements,{registryPath,env=process.env,extraDirectories=[],knownDirectories=[]}={}){
 const declared=requirements?.executables??[];
 const order=new Map(declared.map((entry,index)=>[typeof entry==='string'?entry:entry?.name,index]).reverse());
 const items=normalizeExecutableRequirements(declared).sort((a,b)=>order.get(a.name)-order.get(b.name));
 const directories=await directoriesFor(env,extraDirectories,knownDirectories);
 const registry=registryPath===undefined?null:await readHostRuntimeRegistry(registryPath);
 const tools=[];
 for(const item of items){
  const key=runtimeRequirementKey(item),rejections=[];
  let found=null;
  const registered=registry?.candidates[key];
  const attempted=new Set();
  const trySaved=async path=>{
   const candidate=resolve(path);
   if(attempted.has(candidate))return;
   attempted.add(candidate);
   const result=await checked(item,candidate,env);
   if(result.path)found=result;else rejections.push(result.rejection);
  };
  if(registered)await trySaved(registered.path);
  if(!found&&registry){
   const alternatives=Object.values(registry.candidates)
    .filter(candidate=>candidate.name===item.name)
    .sort((a,b)=>b.generation-a.generation||a.requirement_key.localeCompare(b.requirement_key));
   for(const candidate of alternatives){await trySaved(candidate.path);if(found)break;}
  }
  if(!found){
   for(const directory of directories){
    for(const suffix of suffixes){
     const candidate=join(directory,item.name+suffix);
     if(attempted.has(resolve(candidate)))continue;
     attempted.add(resolve(candidate));
     const result=await checked(item,candidate,env);
     if(result.path){found=result;break;}
     if(!['ENOENT','ENOTDIR'].includes(result.rejection.cause_code))rejections.push(result.rejection);
    }
    if(found)break;
   }
  }
  if(found&&registryPath)await updateRuntimeCandidate(item,found.path,{registryPath,env});
  tools.push({name:item.name,status:found?'found':'missing',path:found?.path??null,...(found?{requirement_key:key,evidence:found.evidence}:{}),...(rejections.length?{rejections}:{})});
 }
 const missing=tools.filter(tool=>tool.status==='missing').map(tool=>tool.name);
 return {status:missing.length?'installation_approval_required':'ready',requirements:{executables:items},tools,missing,searched_directories:directories,installation_performed:false,next_action:missing.length?'Review the missing dependencies and rejected candidates. Supply known host directories or ask the user to approve installation; do not install without approval.':'Proceed with the task using the resolved tool paths.'};
}

export async function discoverRuntimeEnvironment(requirements,options={}){return prepareRuntimeEnvironment(requirements,options);}

export async function verifyRuntimeEnvironment(requirements,pinned,{registryPath,env=process.env}={}){
 const items=normalizeExecutableRequirements(requirements?.executables??[]),tools=Array.isArray(pinned)?pinned:pinned?.tools;
 requireValue(Array.isArray(tools),'ENVIRONMENT_BINDING_STALE','Pinned runtime tools are missing',{dependency:null,reason:'missing_binding',cause_code:'BINDING_MISSING',evidence:null});
 const registry=registryPath===undefined?null:await readHostRuntimeRegistry(registryPath);
 const verified=[];
 for(const item of items){
  const key=runtimeRequirementKey(item),tool=tools.find(entry=>entry?.name===item.name);
  const stale=(reason,cause_code,evidence)=>{throw failure('ENVIRONMENT_BINDING_STALE',`Runtime dependency ${item.name} is stale: ${reason}`,{dependency:item.name,reason,cause_code,evidence});};
  if(!tool||tool.status!=='found'||!isAbsolute(tool.path??''))stale('binding_missing_or_changed','BINDING_INVALID',tool??null);
  const hasMetadata=Object.hasOwn(tool,'requirement_key')||Object.hasOwn(tool,'evidence');
  if(hasMetadata&&(!tool.evidence||tool.requirement_key!==key))stale('binding_metadata_changed','BINDING_INVALID',tool);
  if(registry&&hasMetadata&&registry.candidates[key]?.path!==tool.path)stale('registry_binding_changed','REGISTRY_CHANGED',registry.candidates[key]??null);
  const result=await checked(item,tool.path,env);
  if(!result.path)stale('candidate_probe_failed',result.rejection.cause_code,result.rejection);
  if(result.path!==tool.path)stale('candidate_path_changed','PATH_CHANGED',result.evidence);
  if(hasMetadata&&(tool.evidence.size!==result.evidence.size||tool.evidence.mtime_ms!==result.evidence.mtime_ms))stale('candidate_file_changed','FILE_CHANGED',result.evidence);
  verified.push({...tool,requirement_key:key,evidence:result.evidence});
 }
 return verified;
}
