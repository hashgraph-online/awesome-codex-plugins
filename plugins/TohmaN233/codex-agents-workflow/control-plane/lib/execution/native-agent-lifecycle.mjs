import {lstat,open} from 'node:fs/promises';
import {homedir} from 'node:os';
import {isAbsolute,join,relative,sep} from 'node:path';
import {canonicalSessionPath} from './local-session-path.mjs';

const fail=(code,message,diagnostic)=>{throw Object.assign(new Error(diagnostic?`${message}; ${JSON.stringify(diagnostic)}`:message),{code,...(diagnostic?{diagnostic}:{})});};
const samePath=(a,b)=>process.platform==='win32'?a.toLowerCase()===b.toLowerCase():a===b;
const fileKey=stat=>[stat.dev,stat.ino,stat.birthtimeMs].join(':');
const inside=(root,path)=>{const rel=relative(root,path);return rel!==''&&rel!=='..'&&!rel.startsWith('..'+sep)&&!isAbsolute(rel);};
const threadUuid=value=>typeof value==='string'&&/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value);
const nonLifecycleRecords=new Set(['response_item','turn_context','compacted','world_state','inter_agent_communication_metadata','token_usage_record']);

// A foreign App Server reconstructs unfinished durable turns as interrupted.
// Only the native owner's exact rollout terminal events establish termination.
// The reader retains identities, lifecycle states and an incomplete line, never
// prompts, tool bodies, final answers or a copy of the transcript.
export function createNativeLifecycleReader({home=process.env.CODEX_HOME||join(homedir(),'.codex'),maxLineBytes=4*1024*1024,maxPartialReads=7}={}) {
  if(!isAbsolute(home)||!Number.isSafeInteger(maxLineBytes)||maxLineBytes<256||!Number.isSafeInteger(maxPartialReads)||maxPartialReads<1)
    fail('NATIVE_AGENT_LIFECYCLE_CONFIG','Invalid native lifecycle reader bounds or Codex home');
  const states=new Map(),observations=new Map();
  async function readLifecycleOnce({thread,agentId,parentThreadId}) {
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
      const diagnostic=guard=>({guard,thread_id:thread.id,expected_key:state.key,actual_key:fileKey(stat),observed_offset:state.offset,
        listed:{dev:listed.dev,ino:listed.ino,birthtime_ms:listed.birthtimeMs,size:listed.size},
        opened:{dev:stat.dev,ino:stat.ino,birthtime_ms:stat.birthtimeMs,size:stat.size}});
      if(fileKey(stat)!==fileKey(listed))fail('NATIVE_AGENT_LIFECYCLE_CHANGED','Native rollout identity changed between listing and open',diagnostic('listed_identity'));
      if(state.key&&state.key!==fileKey(stat))fail('NATIVE_AGENT_LIFECYCLE_CHANGED','Native rollout identity changed from its retained observation',diagnostic('retained_identity'));
      if(stat.size<state.offset)fail('NATIVE_AGENT_LIFECYCLE_CHANGED','Native rollout is shorter than its observed offset',diagnostic('observed_size'));
      state.key=fileKey(stat);
      const startOffset=state.offset;
      const advanceRecord=()=>{
        if(!state.checked)fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Native rollout must begin with its exact owned session metadata');
        const inherited=state.ordinal<state.historyStartOrdinal;state.ordinal++;
        if(!Number.isSafeInteger(state.ordinal))fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Native rollout record ordinal exceeds its exact integer bound');
        return inherited;
      };
      const consume=line=>{
        if(!line.length)return;
        const header=line.subarray(0,4096).toString('utf8'),outer=/"type"\s*:\s*"([^"]+)"/.exec(header)?.[1];
        if(!['session_meta','event_msg'].includes(outer)&&!nonLifecycleRecords.has(outer))
          fail('NATIVE_AGENT_LIFECYCLE_SCHEMA',`Unsupported native rollout record type: ${/^[a-z_]{1,64}$/.test(outer??'')?outer:'unknown'}`);
        const event=/"payload"\s*:\s*\{\s*"type"\s*:\s*"([^"]+)"/.exec(header)?.[1];
        if(outer==='event_msg'&&!event)fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Unsupported native event payload header');
        const structural=outer==='session_meta'||outer==='event_msg'&&['task_started','task_complete','turn_aborted'].includes(event);
        const inherited=state.checked?advanceRecord():false;
        if(!structural){
          if(!state.checked||inherited&&!state.ancestors.size)fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Inherited history must begin with its exact fork parent metadata');
          return;
        }
        if(line.length>maxLineBytes)fail('NATIVE_AGENT_LIFECYCLE_LINE_LIMIT','Native lifecycle structural record exceeds its bounded line size');
        let row;try{row=JSON.parse(line.toString('utf8'));}catch{fail('NATIVE_AGENT_LIFECYCLE_SCHEMA','Malformed native lifecycle JSON record');}
        const payload=row.payload;
        if(outer==='session_meta'){
          const spawn=payload?.source?.subagent?.thread_spawn;
          if(!state.checked){
            if(payload?.id!==thread.id||payload.parent_thread_id!==parentThreadId||payload.agent_path!==expectedPath||
              spawn?.parent_thread_id!==parentThreadId||spawn.agent_path!==expectedPath)
              fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Native rollout session UUID, parent UUID or Agent path does not match thread/read and the recorded receipt');
            const ordinal=Object.hasOwn(payload,'subagent_history_start_ordinal')?payload.subagent_history_start_ordinal:0,fork=payload.forked_from_id??null;
            if(!Number.isSafeInteger(ordinal)||ordinal<0||fork!==null&&(!Object.hasOwn(payload,'subagent_history_start_ordinal')||fork!==parentThreadId||thread.forkedFromId!==fork)||
              ordinal>0&&fork===null||thread.forkedFromId!=null&&thread.forkedFromId!==fork)
              fail('NATIVE_AGENT_LIFECYCLE_BOUNDARY','Native inherited history requires its exact SDK fork parent and nonnegative typed record boundary');
            state.checked=true;state.ordinal=0;state.historyStartOrdinal=ordinal;state.nextAncestor=ordinal?fork:null;
            state.nextAncestorPath=expectedPath.slice(0,expectedPath.lastIndexOf('/'));state.ancestors=new Set();return;
          }
          // Forked native journals put the owned header first, then a copied
          // ancestor prefix. Only the owner's typed ordinal excludes that
          // prefix; timestamps and the copied parent's unfinished turns cannot
          // establish child ownership or termination.
          if(!inherited||payload?.id!==state.nextAncestor||state.ancestors.has(payload.id)||state.ancestors.size>=128)
            fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Native copied metadata is outside its exact inherited prefix or fork ancestry');
          const ancestorFork=payload.forked_from_id??null;
          const ancestorPath=payload.agent_path??'/root';
          if(ancestorPath!==state.nextAncestorPath||ancestorPath!=='/root'&&
            (spawn?.agent_path!==ancestorPath||spawn?.parent_thread_id!==payload.parent_thread_id||ancestorFork!==null&&ancestorFork!==payload.parent_thread_id))
            fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Native copied metadata Agent path or spawn parent differs from its fork ancestry');
          if(ancestorFork!==null&&(!threadUuid(ancestorFork)||ancestorFork===thread.id||state.ancestors.has(ancestorFork)))
            fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Native copied metadata has an invalid fork ancestry');
          state.ancestors.add(payload.id);state.nextAncestor=ancestorFork;
          state.nextAncestorPath=ancestorPath==='/root'?'/root':ancestorPath.slice(0,ancestorPath.lastIndexOf('/'));return;
        }
        if(inherited){
          if(!state.ancestors.size)fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Inherited lifecycle must follow its exact fork parent metadata');
          return;
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
        if(!bytesRead)fail('NATIVE_AGENT_LIFECYCLE_CHANGED','Native rollout ended while reading its observed bytes',diagnostic('read_eof'));
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
            const inherited=advanceRecord();
            if(inherited&&!state.ancestors.size)fail('NATIVE_AGENT_LIFECYCLE_IDENTITY','Inherited history must follow its exact fork parent metadata');
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
        bytes_read:state.offset-startOffset,retained_bytes:state.pending.length,...(state.historyStartOrdinal?{inherited_records:state.historyStartOrdinal}:{})};
    } catch(error) {
      if(error.code?.startsWith('NATIVE_AGENT_'))throw error;
      throw Object.assign(new Error(`Native lifecycle read failed for thread ${thread.id}: ${error.code??'READ_ERROR'}`,{cause:error}),{code:'NATIVE_AGENT_LIFECYCLE_READ'});
    } finally {if(file)await file.close();}
  }
  return async function readLifecycle(args) {
    // Watcher predicates and the post-arm recheck share this parser. Hold one
    // thread's entire observation through handle closure so they cannot read
    // and advance the same offset twice. Independent child threads stay parallel.
    const key=args?.thread?.id,previous=observations.get(key)??Promise.resolve();
    const observation=previous.then(()=>readLifecycleOnce(args));
    // A failed observation still rejects its caller; only queue settlement is
    // neutral, allowing the next exact binding to run its original fresh checks.
    const settled=observation.then(()=>{},()=>{});observations.set(key,settled);
    try{return await observation;}finally{if(observations.get(key)===settled)observations.delete(key);}
  };
}
