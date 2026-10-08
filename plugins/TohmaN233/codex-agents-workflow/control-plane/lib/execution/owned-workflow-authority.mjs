import {readFile, rename, unlink, writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {randomBytes} from 'node:crypto';
import {digest} from '../workflow-revisions.mjs';
import {requireValue} from '../workflow-paths.mjs';

// Host-local continuation authority. Never included in Run exports or model results.
export async function retainOwnedAuthority(runtime, run) {
  await runtime.authorizeController(run.run_id, {control_token:run.control_token});
  const path=join(runtime.runs.directory(run.run_id),'host-authority.json');
  const authority={run_id:run.run_id,control_token:run.control_token};
  try { await writeFile(path,JSON.stringify(authority),{flag:'wx',mode:0o600}); }
  catch(error){
    if(error.code!=='EEXIST')throw error;
    const existing=JSON.parse(await readFile(path,'utf8'));
    requireValue(existing.run_id===authority.run_id&&existing.control_token===authority.control_token,
      'RUN_AUTHORITY','Existing retained Host authority differs from this Run');
  }
}

// Controller recovery rotates the capability in the Run journal. Replace the
// Host-only copy in the same operation so model-facing continuations never
// need to receive or transcribe that capability.
export async function replaceOwnedAuthority(runtime,run){
  await runtime.authorizeController(run.run_id,{control_token:run.control_token});
  const path=join(runtime.runs.directory(run.run_id),'host-authority.json');
  try{
    const existing=JSON.parse(await readFile(path,'utf8'));
    requireValue(existing.run_id===run.run_id,'RUN_AUTHORITY','Existing retained Host authority belongs to another Run');
  }catch(error){if(error.code!=='ENOENT')throw error;}
  const temporary=`${path}.${process.pid}.${randomBytes(8).toString('hex')}.tmp`;
  try{
    await writeFile(temporary,JSON.stringify({run_id:run.run_id,control_token:run.control_token}),{flag:'wx',mode:0o600});
    await rename(temporary,path);
  }catch(error){try{await unlink(temporary);}catch(cleanup){if(cleanup.code!=='ENOENT')error.cleanup_error=cleanup.message;}throw error;}
}
export async function readOwnedAuthority(runtime, runId) {
  const record=await runtime.runs.read(runId);
  const authority=JSON.parse(await readFile(join(runtime.runs.directory(runId),'host-authority.json'),'utf8'));
  requireValue(authority.run_id===runId && typeof authority.control_token==='string'
    && digest(authority.control_token)===record.state.control_hash,
    'RUN_AUTHORITY','Retained Host authority is stale or belongs to another Run');
  return {...authority,owner:record.state.main_actor};
}

const TERMINAL_RUN_STATUSES=new Set(['succeeded','failed','cancelled','interrupted']);

// Codex supplies the authenticated current conversation in MCP request metadata.
// Resolve its one active Run from durable journals so a fresh MCP request or a
// restarted WorkflowService never needs the model to repeat a Run ID or token.
export async function readOwnedAuthorityForThread(runtime,threadId){
  requireValue(typeof threadId==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(threadId),
    'MODEL_THREAD_ID','Workflow continuation requires the authenticated Codex thread metadata');
  const matches=[];
  for(const summary of await runtime.runs.list()){
    if(TERMINAL_RUN_STATUSES.has(summary.status))continue;
    const record=await runtime.runs.read(summary.run_id);
    if(record.state.constraints?.native_parent_thread_id===threadId)matches.push(record);
  }
  requireValue(matches.length===1,'MODEL_RUN_AUTHORITY',matches.length
    ?'More than one active Workflow Run is bound to this model session'
    :'No active Workflow Run is bound to this model session');
  return readOwnedAuthority(runtime,matches[0].state.run_id);
}
