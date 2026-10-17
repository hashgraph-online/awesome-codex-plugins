import {createHash,randomUUID} from 'node:crypto';
import {lstatSync,mkdirSync,readFileSync,writeFileSync,unlinkSync,renameSync,openSync,closeSync} from 'node:fs';
import {homedir,tmpdir} from 'node:os';
import {dirname,isAbsolute,join,parse,relative,resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';

export const NATIVE_BUILTINS_PROFILE_NAME='caw_native_builtins';
export const NATIVE_CONTEXT_PROFILE_TEMPLATE_PATH=resolve(dirname(fileURLToPath(import.meta.url)),'../agent-profiles/caw-native-builtins.toml');
const owner='codex-agents-workflow',profileFile='caw-native-builtins.toml',receiptFile='native-context-profile.json';
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
function requireProfile(condition,code,message){
 if(!condition)throw Object.assign(new Error(message),{code:`NATIVE_CONTEXT_PROFILE_${code}`});
}
function contains(root,path){const rel=relative(root,path);return rel===''||(!rel.startsWith('..'+sep)&&rel!=='..'&&!isAbsolute(rel));}
// Match normal path safety: runtime home/temp are boundaries, not their OS aliases.
function safePath(path){
 requireProfile(isAbsolute(path),'PATH','Native context profile paths must be absolute');
 const absolute=resolve(path),roots=[resolve(homedir()),resolve(tmpdir())].filter(root=>contains(root,absolute)).sort((a,b)=>b.length-a.length);
 const root=roots[0]??parse(absolute).root;let current=root,stat;
 for(const part of ['',...relative(root,absolute).split(sep).filter(Boolean)]){
  if(part)current=join(current,part);
  try{stat=lstatSync(current);}catch(error){if(error.code==='ENOENT')return null;throw error;}
  requireProfile(!stat.isSymbolicLink(),'LINK',`Native context profile path cannot be a link: ${current}`);
 }
 return stat;
}
export function nativeContextProfilePaths({codexHome}={}){
 if(codexHome!==undefined)requireProfile(typeof codexHome==='string'&&isAbsolute(codexHome),'PATH','codexHome must be an absolute path');
 const home=codexHome??(process.env.CODEX_HOME?resolve(homedir(),process.env.CODEX_HOME):join(homedir(),'.codex'));
 return {codex_home:resolve(home),profile_path:join(home,'agents',profileFile),ownership_receipt_path:join(home,owner,receiptFile)};
}
function readRegular(path,limit){
 const stat=safePath(path);if(!stat)return null;
 requireProfile(stat.isFile()&&stat.size<=limit,'FILE',`Expected bounded regular native context profile file: ${path}`);
 return readFileSync(path);
}
export function readNativeContextProfileTemplate(){
 const bytes=readRegular(NATIVE_CONTEXT_PROFILE_TEMPLATE_PATH,4096);
 requireProfile(bytes!==null,'TEMPLATE','Native context profile template is missing');return bytes;
}
function readRegistration(options){
 const paths=nativeContextProfilePaths(options),profile=readRegular(paths.profile_path,4096),raw=readRegular(paths.ownership_receipt_path,1024);
 let receipt=null;
 if(raw){
  try{receipt=JSON.parse(raw.toString('utf8'));}catch{requireProfile(false,'RECEIPT','Native context profile ownership receipt is invalid JSON');}
  const keys=receipt&&typeof receipt==='object'&&!Array.isArray(receipt)?Object.keys(receipt):[];
  requireProfile(keys.length>=4&&keys.length<=5&&keys.every(key=>['schema_version','owner','name','sha256','pending_sha256'].includes(key))&&
   receipt.schema_version===1&&receipt.owner===owner&&receipt.name===NATIVE_BUILTINS_PROFILE_NAME&&/^[a-f0-9]{64}$/.test(receipt.sha256)&&
   (receipt.pending_sha256===undefined||/^[a-f0-9]{64}$/.test(receipt.pending_sha256)),'RECEIPT','Native context profile ownership receipt is invalid');
 }
 requireProfile(!profile||receipt,'COLLISION','The native context profile file exists without plugin ownership; leave it untouched');
 if(profile)requireProfile([receipt.sha256,receipt.pending_sha256].includes(sha256(profile)),'EDITED','The plugin-owned native context profile was edited; leave it untouched');
 return {paths,profile,receipt};
}
export function preflightNativeContextProfileRegistration(options={}){
 const state=readRegistration(options);return {name:NATIVE_BUILTINS_PROFILE_NAME,...state.paths,registered:Boolean(state.profile&&state.receipt)};
}
export function verifyInstalledNativeContextProfile(name,options={}){
 requireProfile(name===NATIVE_BUILTINS_PROFILE_NAME,'NAME','Unsupported native tool context profile');
 const {paths,profile,receipt}=readRegistration(options);
 requireProfile(profile&&receipt&&!receipt.pending_sha256,'UNREGISTERED','Native context profile registration is missing or unfinished');
 const template=readNativeContextProfileTemplate();
 requireProfile(profile.equals(template),'TEMPLATE_MISMATCH','Installed native context profile differs from this plugin template');
 return {name,profile_path:paths.profile_path,sha256:sha256(template),ownership_receipt_path:paths.ownership_receipt_path};
}
function replaceOwnedFile(path,bytes,check){
 const staged=`${path}.${randomUUID()}.tmp`;safePath(staged);let descriptor,created=false;
 try{
  descriptor=openSync(staged,'wx');created=true;writeFileSync(descriptor,bytes);closeSync(descriptor);descriptor=undefined;
  check();renameSync(staged,path);
 }catch(error){
  const errors=[error];
  if(descriptor!==undefined)try{closeSync(descriptor);}catch(closeError){errors.push(closeError);}
  if(created)try{if(safePath(staged))unlinkSync(staged);}catch(cleanupError){errors.push(cleanupError);}
  if(errors.length>1)throw Object.assign(new AggregateError(errors,'Native context profile write and staged cleanup failed'),{code:'NATIVE_CONTEXT_PROFILE_WRITE_CLEANUP'});
  throw error;
 }
}
export function installNativeContextProfile({codexHome,deployedPluginRoot}={}){
 const state=readRegistration({codexHome}),template=readNativeContextProfileTemplate();
 requireProfile(typeof deployedPluginRoot==='string'&&isAbsolute(deployedPluginRoot),'PATH','Installed plugin root must be absolute');
 const deployed=readRegular(join(deployedPluginRoot,'agent-profiles',profileFile),4096);
 requireProfile(deployed&&deployed.equals(template),'DEPLOYED_MISMATCH','Installed native context profile template differs from source');
 const {paths,profile,receipt}=state,hash=sha256(template);
 if(profile?.equals(template)&&!receipt.pending_sha256)return {...verifyInstalledNativeContextProfile(NATIVE_BUILTINS_PROFILE_NAME,{codexHome}),changed:false};
 for(const directory of [dirname(paths.profile_path),dirname(paths.ownership_receipt_path)]){
  safePath(directory);mkdirSync(directory,{recursive:true});requireProfile(safePath(directory).isDirectory(),'PATH','Native context profile parent must be a directory');
 }
 // Record both owned hashes before replacement so an interrupted update is recoverable.
 const check=()=>readRegistration({codexHome}),writeReceipt=value=>replaceOwnedFile(paths.ownership_receipt_path,JSON.stringify(value)+'\n',check);
 writeReceipt({schema_version:1,owner,name:NATIVE_BUILTINS_PROFILE_NAME,sha256:receipt?.sha256??hash,pending_sha256:hash});
 replaceOwnedFile(paths.profile_path,template,check);
 writeReceipt({schema_version:1,owner,name:NATIVE_BUILTINS_PROFILE_NAME,sha256:hash});
 return {...verifyInstalledNativeContextProfile(NATIVE_BUILTINS_PROFILE_NAME,{codexHome}),changed:!profile?.equals(template)};
}
export function cleanupNativeContextProfile(options={}){
 const {paths,profile,receipt}=readRegistration(options);
 if(profile){safePath(paths.profile_path);unlinkSync(paths.profile_path);}
 if(receipt){safePath(paths.ownership_receipt_path);unlinkSync(paths.ownership_receipt_path);}
 return {name:NATIVE_BUILTINS_PROFILE_NAME,removed:Boolean(profile),ownership_receipt_removed:Boolean(receipt)};
}
