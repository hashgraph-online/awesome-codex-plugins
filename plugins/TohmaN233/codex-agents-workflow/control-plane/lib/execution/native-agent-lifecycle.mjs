import {lstat,open} from 'node:fs/promises';
import {homedir} from 'node:os';
import {isAbsolute,join,relative,sep} from 'node:path';
import {canonicalSessionPath} from './local-session-path.mjs';

const fail=(code,message)=>{throw Object.assign(new Error(message),{code});};
const samePath=(a,b)=>process.platform==='win32'?a.toLowerCase()===b.toLowerCase():a===b;
const fileKey=stat=>[stat.dev,stat.ino,stat.birthtimeMs].join(':');
const inside=(root,path)=>{const rel=relative(root,path);return rel!==''&&rel!=='..'&&!rel.startsWith('..'+sep)&&!isAbsolute(rel);};
const nonLifecycleRecords=new Set(['response_item','turn_context','compacted','world_state','inter_agent_communication_metadata','token_usage_record']);

// A foreign App Server reconstructs unfinished durable turns as interrupted.
// Only the native owner's exact rollout terminal events establish termination.
// The reader retains identities, lifecycle states and an incomplete line, never
// prompts, tool bodies, final answers or a copy of the transcript.
export function createNativeLifecycleReader({home=process.env.CODEX_HOME||join(homedir(),'.codex'),maxLineBytes=4*1024*1024,maxPartialReads=7}={}) {
  if(!isAbsolute(home)||!Number.isSafeInteger(maxLineBytes)||maxLineBytes<256||!Number.isSafeInteger(maxPartialReads)||maxPartialReads<1)
    fail('NATIVE_AGENT_LIFECYCLE_CONFIG','Invalid native lifecycle reader bounds or Codex home');
  const states=new Map();
  return async function readLifecycle({thread,agentId,parentThreadId}) {
    const path=thread?.path;
    if(typeof path!=='string'||!isAbsolute(path))
      fail('NATIVE_AGENT_LIFECYCLE_PATH','Native thread/read must provide its exact rollout path inside the configured Codex home sessions directory');
    const expectedPath=agentId?.startsWith('/')?agentId:thread.source?.subAgent?.thread_spawn?.agent_path;
    if(!expectedPath||!parentThreadId)
      fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Native lifecycle observation requires the exact parent UUID and canonical Agent path');
    let state=states.get(thread.id);
    let file;
    try {
      // Validate the original spelling for links before canonicalization. The
      // same non-link Windows file can have short, extended and cased names.
      const {root:canonicalRoot,path:canonicalPath}=await canonicalSessionPath(path,home);
      if(!inside(canonicalRoot,canonicalPath))
        fail('NATIVE_AGENT_LIFECYCLE_PATH','Native thread/read must provide its exact rollout path inside the configured Codex home sessions directory');
      if(state&&(!samePath(state.path,canonicalPath)||state.parent!==parentThreadId||state.agentPath!==expectedPath))
        fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Native rollout binding changed during the pending observation');
      if(!state){
        state={path:canonicalPath,parent:parentThreadId,agentPath:expectedPath,offset:0,pending:Buffer.alloc(0),skipping:false,
          checked:false,partialReads:0,initialReads:0,turns:new Map(),latest:null,key:null};
        states.set(thread.id,state);
      }
      const listed=await lstat(state.path);
      if(!listed.isFile()||listed.nlink!==1)fail('NATIVE_AGENT_LIFECYCLE_PATH','Native rollout must be a regular unlinked file');
      file=await open(state.path,'r');
      const stat=await file.stat();
      if(fileKey(stat)!==fileKey(listed)||state.key&&state.key!==fileKey(stat)||stat.size<state.offset)
        fail('NATIVE_AGENT_LIFECYCLE_CHANGED','Native rollout file identity changed or its observed prefix was truncated');
      state.key=fileKey(stat);
      const startOffset=state.offset;
      const consume=line=>{
        if(!line.length)return;
        const header=line.subarray(0,4096).toString('utf8'),outer=/"type"\s*:\s*"([^"]+)"/.exec(header)?.[1];
        if(!['session_meta','event_msg'].includes(outer)&&!nonLifecycleRecords.has(outer))
          fail('NATIVE_AGENT_LIFECYCLE_SCHEMA',`Unsupported native rollout record type: ${/^[a-z_]{1,64}$/.test(outer??'')?outer:'unknown'}`);
        const event=/"payload"\s*:\s*\{\s*"type"\s*:\s*"([^"]+)"/.exec(header)?.[1];
        if(outer==='event_msg'&&!event)fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Unsupported native event payload header');
        if(outer!=='session_meta'&&(outer!=='event_msg'||!['task_started','task_complete','turn_aborted'].includes(event)))return;
        if(line.length>maxLineBytes)fail('NATIVE_AGENT_LIFECYCLE_LINE_LIMIT','Native lifecycle structural record exceeds its bounded line size');
        let row;try{row=JSON.parse(line.toString('utf8'));}catch{fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Malformed native lifecycle JSON record');}
        const payload=row.payload;
        if(outer==='session_meta'){
          const spawn=payload?.source?.subagent?.thread_spawn;
          if(state.checked||payload?.id!==thread.id||payload.parent_thread_id!==parentThreadId||
            payload.agent_path!==expectedPath||spawn?.parent_thread_id!==parentThreadId||spawn.agent_path!==expectedPath)
            fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Native rollout session UUID, parent UUID or Agent path does not match thread/read and the recorded receipt');
          state.checked=true;return;
        }
        if(!state.checked||typeof payload?.turn_id!=='string'||!payload.turn_id)
          fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Native lifecycle event has no validated session or exact turn ID');
        if(event==='task_started'){
          if(state.turns.has(payload.turn_id))fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Native lifecycle repeats a turn start');
          state.latest=payload.turn_id;state.turns.set(payload.turn_id,{status:'pending',turn_id:payload.turn_id});return;
        }
        const turn=state.turns.get(payload.turn_id);
        if(!turn||turn.status!=='pending')fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Native terminal event has no unique matching active turn');
        turn.status=event==='task_complete'?'completed':'interrupted';
      };
      while(state.offset<stat.size){
        const buffer=Buffer.allocUnsafe(Math.min(65536,stat.size-state.offset));
        const {bytesRead}=await file.read(buffer,0,buffer.length,state.offset);
        if(!bytesRead)fail('NATIVE_AGENT_LIFECYCLE_CHANGED','Native rollout changed while reading its observed prefix');
        state.offset+=bytesRead;
        let bytes=buffer.subarray(0,bytesRead);
        if(state.skipping){
          const end=bytes.indexOf(10);if(end<0)continue;
          state.skipping=false;bytes=bytes.subarray(end+1);
        }
        let joined=state.pending.length?Buffer.concat([state.pending,bytes]):bytes,begin=0,end;
        while((end=joined.indexOf(10,begin))>=0){consume(joined.subarray(begin,end));begin=end+1;}
        state.pending=Buffer.from(joined.subarray(begin));
        if(state.pending.length>maxLineBytes){
          const header=state.pending.subarray(0,4096).toString('utf8'),outer=/"type"\s*:\s*"([^"]+)"/.exec(header)?.[1];
          const event=/"payload"\s*:\s*\{\s*"type"\s*:\s*"([^"]+)"/.exec(header)?.[1];
          if(outer==='event_msg'&&!event)fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Unsupported native event payload header');
          if(nonLifecycleRecords.has(outer)||outer==='event_msg'&&!['task_started','task_complete','turn_aborted'].includes(event)){
            state.pending=Buffer.alloc(0);state.skipping=true;
          }else fail('NATIVE_AGENT_LIFECYCLE_LINE_LIMIT','Native lifecycle structural record exceeds its bounded line size');
        }
      }
      const partial=state.pending.length>0||state.skipping;
      state.partialReads=partial?(state.offset===startOffset?state.partialReads+1:1):0;
      if(state.partialReads>=maxPartialReads)fail('NATIVE_AGENT_LIFECYCLE_PARTIAL','Native rollout has an incomplete line that stopped advancing');
      if(!state.checked&&!partial)fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Native rollout contains no matching session metadata');
      if(!state.latest&&++state.initialReads>=maxPartialReads)
        fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Native rollout did not expose a task_started lifecycle within the bounded initial observations');
      return {...(state.turns.get(state.latest)??{turn_id:null,status:'pending'}),...(partial?{status:'pending'}:{}),
        bytes_read:state.offset-startOffset,retained_bytes:state.pending.length};
    } catch(error) {
      if(error.code?.startsWith('NATIVE_AGENT_'))throw error;
      throw Object.assign(new Error(`Native lifecycle read failed for thread ${thread.id}: ${error.code??'READ_ERROR'}`,{cause:error}),{code:'NATIVE_AGENT_LIFECYCLE_READ'});
    } finally {if(file)await file.close();}
  };
}
