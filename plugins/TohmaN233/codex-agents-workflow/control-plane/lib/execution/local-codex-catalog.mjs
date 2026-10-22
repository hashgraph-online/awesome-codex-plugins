import { readdir, stat, readFile, realpath } from 'node:fs/promises';
import { join, delimiter, isAbsolute } from 'node:path';
import { homedir } from 'node:os';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { createCodexClient } from './codex-app-server-client.mjs';
import { STRICT_SETTINGS, isolatedEnvironment } from './codex-profile-builder.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { digest } from '../workflow-revisions.mjs';
const exec=promisify(execFile);
export function newestVersion(items) {
  return [...items].sort((a,b)=>{const x=a.version.split('.').map(Number),y=b.version.split('.').map(Number);for(let i=0;i<3;i++){if(x[i]!==y[i])return y[i]-x[i];}return a.binary.localeCompare(b.binary);})[0];
}
export async function discoverLocalCodex({env=process.env,platform=process.platform,extra=[],execImpl=exec}={}) {
  const names=platform==='win32'?['codex.exe']:['codex'];
  const candidates=new Set(extra);
  for(const dir of (env.PATH ?? env.Path ?? '').split(delimiter).filter(isAbsolute)) for(const name of names)candidates.add(join(dir,name));
  if(platform==='win32' && env.LOCALAPPDATA) {
    const root=join(env.LOCALAPPDATA,'OpenAI','Codex','bin');
    let entries;try{entries=await readdir(root,{withFileTypes:true});}catch(error){if(error.code!=='ENOENT')throw error;entries=[];}
    for(const entry of entries.slice(0,100))if(entry.isDirectory())candidates.add(join(root,entry.name,'codex.exe'));
  }
  const found=[],diagnostics=[];
  for(const binary of [...candidates].slice(0,128)) {
    let info;try{info=await stat(binary);}catch(error){if(['ENOENT','ENOTDIR'].includes(error.code))continue;throw error;}
    if(!info.isFile())continue;
    try{const target=await realpath(binary),result=await execImpl(target,['--version'],{timeout:5000,maxBuffer:4096,windowsHide:true});const match=/codex-cli (\d+\.\d+\.\d+)/.exec(result.stdout);requireValue(match,'CODEX_VERSION','Unrecognized Codex version');found.push({binary:target,selected_path:binary,version:match[1]});}
    catch(error){diagnostics.push({binary,code:error.code ?? 'CODEX_VERSION'});}
  }
  requireValue(found.length,'LOCAL_CODEX_MISSING','No local Codex executable was discovered; configure CODEX_CATALOG_BINARY or install Codex',{diagnostics});
  const selected=newestVersion(found);return {...selected,sha256:digest(await readFile(selected.binary)),diagnostics};
}
export async function localCodexCatalog({env=process.env,extra=[],clientFactory=createCodexClient}={}) {
  const override=env.CODEX_CATALOG_BINARY;
  requireValue(!override || isAbsolute(override),'CODEX_CATALOG_PATH','CODEX_CATALOG_BINARY must be absolute');
  const source=await discoverLocalCodex({env:override?{...env,PATH:'',Path:'',LOCALAPPDATA:''}:env,extra:override?[override]:extra});
  const home=env.CODEX_HOME || join(homedir(),'.codex');
  const overrides=Object.entries(STRICT_SETTINGS).filter(([key])=>key!=='cli_auth_credentials_store').map(([key,value])=>key+' = '+JSON.stringify(value));
  const client=clientFactory(source.binary,{home,cwd:home,env:isolatedEnvironment(env,home),overrides,catalogOnly:true});
  try {
    await client.call('initialize',{clientInfo:{name:'codex_workflow_catalog',version:'1.0.0'},capabilities:{experimentalApi:true}});client.initialized();
    const account=await client.call('account/read',{refreshToken:false});
    requireValue(account?.account || account?.requiresOpenaiAuth===false,'HOST_AUTH_UNAVAILABLE','Existing local Codex login is unavailable; no login page was opened');
    const models=[],seen=new Set();let cursor;
    do {const page=await client.call('model/list',{includeHidden:true,limit:100,...(cursor?{cursor}:{})});requireValue(Array.isArray(page.data) && models.length+page.data.length<=1000,'CODEX_MODEL_SCHEMA','Invalid model catalog');models.push(...page.data);cursor=page.nextCursor;requireValue(!cursor || typeof cursor==='string' && !seen.has(cursor) && seen.size<20,'CODEX_MODEL_SCHEMA','Invalid catalog pagination');if(cursor)seen.add(cursor);}while(cursor);
    requireValue(models.every(m=>typeof m.model==='string' && /^[A-Za-z0-9._:/-]{1,128}$/.test(m.model) && Array.isArray(m.supportedReasoningEfforts)) && new Set(models.map(m=>m.model)).size===models.length,'CODEX_MODEL_SCHEMA','Model entries require unique identities and supported efforts');
    return {source,models:models.map(m=>({model:m.model,displayName:m.displayName,defaultReasoningEffort:m.defaultReasoningEffort,supportedReasoningEfforts:m.supportedReasoningEfforts})),model_calls:0};
  } finally {await client.close();}
}
