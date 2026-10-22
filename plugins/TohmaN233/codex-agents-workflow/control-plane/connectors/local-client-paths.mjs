import {delimiter,join,isAbsolute} from 'node:path';
export function pathClientCandidates(name,env=process.env,platform=process.platform){
  const filename=platform==='win32'?name+'.exe':name;
  return [...new Set((env.PATH ?? env.Path ?? '').split(delimiter).filter(isAbsolute).map(dir=>join(dir,filename)))].slice(0,128);
}
export const CLIENT_MANAGED_MODELS=Object.freeze({source:'client_managed',available:null,selected:null,reason:'The current connector does not expose an authoritative model inventory.'});
