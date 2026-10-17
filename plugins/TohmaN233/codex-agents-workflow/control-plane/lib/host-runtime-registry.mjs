import {lstat,open,readFile,rename,rm} from 'node:fs/promises';
import {dirname,isAbsolute,join,resolve} from 'node:path';
import {randomUUID} from 'node:crypto';
import {noSymlinks,requireValue} from './workflow-paths.mjs';
import {syncDirectory} from './workflow-store.mjs';
import {normalizeExecutableRequirements,runtimeRequirementKey} from './runtime-requirements.mjs';

const empty=()=>({schema_version:1,generation:0,candidates:{}});
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const invalid=(message,cause)=>Object.assign(new Error(message),{code:'ENVIRONMENT_REGISTRY_INVALID',...(cause?{cause}:{})});

export function registryPathForConfig(configPath){
 requireValue(typeof configPath==='string'&&isAbsolute(configPath),'ENVIRONMENT_REGISTRY_PATH','Config path must be absolute');
 return join(dirname(resolve(configPath)),'host-runtime-registry.json');
}

export async function readHostRuntimeRegistry(path){
 requireValue(typeof path==='string'&&isAbsolute(path),'ENVIRONMENT_REGISTRY_PATH','Host runtime registry path must be absolute');
 let info;try{info=await lstat(path);}catch(error){if(error.code==='ENOENT')return empty();throw error;}
 requireValue(info.isFile()&&!info.isSymbolicLink()&&info.size<=2*1024*1024,'ENVIRONMENT_REGISTRY_INVALID','Host runtime registry must be a bounded regular file without a symlink');
 await noSymlinks(dirname(path));
 const data=await readFile(path,'utf8');
 let parsed;try{parsed=JSON.parse(data);}catch(error){throw invalid('Host runtime registry is malformed JSON',error);}
 requireValue(object(parsed)&&parsed.schema_version===1&&Number.isSafeInteger(parsed.generation)&&parsed.generation>=0&&object(parsed.candidates)&&Object.keys(parsed.candidates).length<=1024,'ENVIRONMENT_REGISTRY_INVALID','Host runtime registry has an invalid schema');
 for(const [key,value] of Object.entries(parsed.candidates)){
  let actualKey;try{actualKey=runtimeRequirementKey(value?.requirement);}catch{actualKey=null;}
  const evidence=value?.evidence;
  requireValue(/^[a-zA-Z0-9][a-zA-Z0-9_.+-]{0,99}:[a-f0-9]{64}$/.test(key)&&object(value)&&value.requirement_key===key&&actualKey===key&&value.requirement.name===value.name&&typeof value.path==='string'&&isAbsolute(value.path)&&object(evidence)&&typeof evidence.realpath==='string'&&isAbsolute(evidence.realpath)&&evidence.realpath===value.path&&Number.isFinite(evidence.size)&&evidence.size>=0&&Number.isFinite(evidence.mtime_ms)&&['file-identity','version','python'].includes(evidence.probe_kind)&&Number.isSafeInteger(value.generation)&&value.generation>0&&value.generation<=parsed.generation&&typeof value.registered_at==='string'&&typeof value.checked_at==='string','ENVIRONMENT_REGISTRY_INVALID','Host runtime registry contains an invalid candidate: '+key);
 }
 return parsed;
}

async function releaseLock(lock,primary){
 const errors=[];
 try{await lock.handle.close();}catch(error){errors.push(error);}
 try{await rm(lock.path);}catch(error){errors.push(error);}
 if(primary&&errors.length)throw new AggregateError([primary,...errors],'Registry update and lock cleanup failed');
 if(primary)throw primary;
 if(errors.length)throw new AggregateError(errors,'Registry lock cleanup failed');
}

async function lockRegistry(path){
 const lockPath=path+'.lock',deadline=Date.now()+10000;
 for(;;){
  let handle;
  try{handle=await open(lockPath,'wx');}
  catch(error){
   if(error.code!=='EEXIST')throw error;
   requireValue(Date.now()<deadline,'ENVIRONMENT_REGISTRY_LOCK_TIMEOUT','Timed out acquiring host runtime registry lock: '+lockPath);
   await new Promise(resolve=>setTimeout(resolve,25));continue;
  }
  const lock={handle,path:lockPath};
  try{await handle.writeFile(JSON.stringify({pid:process.pid,created_at:new Date().toISOString()}));await handle.sync();return lock;}
  catch(error){await releaseLock(lock,error);}
 }
}

export async function updateRuntimeCandidate(requirement,path,{registryPath,env=process.env}={}){
 const [item]=normalizeExecutableRequirements([requirement]);
 requireValue(typeof registryPath==='string'&&isAbsolute(registryPath),'ENVIRONMENT_REGISTRY_PATH','Host runtime registry path must be absolute');
 requireValue(typeof path==='string'&&isAbsolute(path),'ENVIRONMENT_CANDIDATE_INVALID','Executable candidate path must be absolute');
 await noSymlinks(dirname(registryPath));
 // Probe before lock acquisition and before persistence; caller evidence is never trusted.
 const {probeRuntimeCandidate}=await import('./runtime-environment.mjs');
 const evidence=await probeRuntimeCandidate(item,path,{env});
 const lock=await lockRegistry(registryPath);
 let result,error;
 try{
  const current=await readHostRuntimeRegistry(registryPath),key=runtimeRequirementKey(item),previous=current.candidates[key];
  const same=previous?.path===evidence.realpath&&JSON.stringify(previous.evidence)===JSON.stringify(evidence);
  const generation=current.generation+(same?0:1),now=new Date().toISOString();
  const candidate={name:item.name,requirement:item,requirement_key:key,path:evidence.realpath,evidence,generation,registered_at:previous?.registered_at??now,checked_at:now};
  const next={...current,generation,candidates:{...current.candidates,[key]:candidate}};
  const temporary=join(dirname(registryPath),'.'+randomUUID()+'.host-runtime-registry.tmp');
  let temp,tempError;
  try{
   temp=await open(temporary,'wx');
   await temp.writeFile(JSON.stringify(next,null,2)+'\n');await temp.sync();await temp.close();temp=null;
   await rename(temporary,registryPath);await syncDirectory(dirname(registryPath));
  }catch(caught){tempError=caught;}
  const cleanup=[];
  if(temp)try{await temp.close();}catch(caught){cleanup.push(caught);}
  try{await rm(temporary,{force:true});}catch(caught){cleanup.push(caught);}
  if(tempError&&cleanup.length)throw new AggregateError([tempError,...cleanup],'Registry write and temp cleanup failed');
  if(tempError)throw tempError;
  if(cleanup.length)throw new AggregateError(cleanup,'Registry temp cleanup failed');
  result=candidate;
 }catch(caught){error=caught;}
 await releaseLock(lock,error);
 return result;
}
