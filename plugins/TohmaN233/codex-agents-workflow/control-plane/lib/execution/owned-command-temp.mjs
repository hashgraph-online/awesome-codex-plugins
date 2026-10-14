import {mkdtemp,lstat,readFile,writeFile,rm} from 'node:fs/promises';
import {realpath} from 'node:fs';
import {promisify} from 'node:util';
import {tmpdir} from 'node:os';
import {join,resolve,dirname} from 'node:path';
import {randomUUID} from 'node:crypto';
import {canonicalJSON,digest} from '../workflow-revisions.mjs';
import {noSymlinks,requireValue} from '../workflow-paths.mjs';
const physical=promisify(realpath.native);
const identity=stat=>({dev:String(stat.dev),ino:String(stat.ino)});
export async function prepareOwnedCommandTemp({workspace,spool}){
 const configured=resolve(tmpdir());const baseStat=await lstat(configured);
 requireValue(baseStat.isDirectory()&&!baseStat.isSymbolicLink(),'CODEX_COMMAND_TEMP_BASE','Platform temporary boundary must be an existing physical directory');
 const parent=await physical(configured);const path=await mkdtemp(join(parent,'wf-cmd-'));
 try{
 await noSymlinks(path);const initial=identity(await lstat(path,{bigint:true}));
 const owner={schema_version:1,broker_id:randomUUID(),workspace:resolve(workspace),spool_root:resolve(spool),path,identity:initial};
 const bytes=Buffer.from(canonicalJSON(owner)),marker=join(path,'.host-command-temp-owner.json');
 // Failures preserve the uniquely allocated leaf for explicit diagnosis; never
 // delete a directory whose complete owner record was not sealed successfully.
 await writeFile(marker,bytes,{flag:'wx',mode:0o600});
 const summary=Object.freeze({path,parent,broker_id:owner.broker_id,owner_sha256:digest(bytes),identity:initial});
 let closed=false;
 return {path,parent,summary,async assertOwned(){
   requireValue(!closed,'CODEX_COMMAND_TEMP_CLOSED','Owned command temporary workspace is already closed');
   await noSymlinks(path);await noSymlinks(marker);
   const stat=await lstat(path,{bigint:true});requireValue(stat.isDirectory()&&canonicalJSON(identity(stat))===canonicalJSON(initial),'CODEX_COMMAND_TEMP_OWNER','Owned temporary directory identity changed');
   requireValue((await readFile(marker)).equals(bytes),'CODEX_COMMAND_TEMP_OWNER','Owned temporary directory owner bytes changed');
 },async close(){if(closed)return;await this.assertOwned();requireValue(dirname(path)===parent,'CODEX_COMMAND_TEMP_OWNER','Owned temporary leaf left its exact platform parent');await rm(path,{recursive:true});closed=true;}};
 }catch(error){throw Object.assign(error,{retained_at:path,temporary_parent:parent});}
}
