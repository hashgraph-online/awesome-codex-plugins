import {readFile} from 'node:fs/promises';

export const PLUGIN_REPOSITORY='https://github.com/TohmaN233/codex-agents-workflow';
export const PLUGIN_VERSION_URL='https://raw.githubusercontent.com/TohmaN233/codex-agents-workflow/main/plugins/codex-agents-workflow/control-plane/package.json';
function parts(version){
  if(typeof version!=='string'||!/^\d+\.\d+(?:\.\d+)?$/.test(version))throw new Error('Plugin update metadata has an invalid version');
  return version.split('.').map(Number).concat([0]).slice(0,3);
}
export function comparePluginVersions(left,right){
  const a=parts(left),b=parts(right);for(let i=0;i<3;i++)if(a[i]!==b[i])return Math.sign(a[i]-b[i]);return 0;
}
// Console-only, shared by HTTP and the MCP App. No Run or bootstrap calls it.
// Concurrent openings share one request; there is no timer or polling loop.
export function createPluginUpdateChecker({installedVersion,fetchImpl=globalThis.fetch,now=Date.now}){
  parts(installedVersion);let pending,expires=0;
  return async()=>{
    if(pending&&now()<expires)return pending;
    expires=now()+5*60*1000;
    pending=(async()=>{
      const response=await fetchImpl(PLUGIN_VERSION_URL,{headers:{accept:'application/json'},signal:AbortSignal.timeout(5000)});
      if(!response.ok)throw new Error(`GitHub version check returned HTTP ${response.status}`);
      const remote=await response.json(),difference=comparePluginVersions(remote.version,installedVersion);
      return {status:difference>0?'update_available':difference<0?'ahead':'current',installed_version:installedVersion,latest_version:remote.version,repository:PLUGIN_REPOSITORY};
    })();
    try{return await pending;}catch(error){pending=undefined;throw error;}
  };
}
const checkers=new WeakMap();
export async function pluginUpdateStatus(fetchImpl=globalThis.fetch){
  if(!checkers.has(fetchImpl)){
    const {version}=JSON.parse(await readFile(new URL('../package.json',import.meta.url),'utf8'));
    checkers.set(fetchImpl,createPluginUpdateChecker({installedVersion:version,fetchImpl}));
  }
  return checkers.get(fetchImpl)();
}
