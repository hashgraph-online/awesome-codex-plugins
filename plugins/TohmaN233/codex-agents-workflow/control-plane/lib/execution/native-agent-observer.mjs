import { homedir } from 'node:os';
import { AsyncLocalStorage } from 'node:async_hooks';
import { performance } from 'node:perf_hooks';
import { watch } from 'node:fs/promises';
import { join, resolve, dirname, basename, isAbsolute } from 'node:path';
import { createCodexClient } from './codex-app-server-client.mjs';
import { discoverLocalCodex } from './local-codex-catalog.mjs';
import { createNativeLifecycleReader } from './native-agent-lifecycle.mjs';
import { validateData } from '../workflow-data-schema.mjs';
import {assertOutsideHostRunTransaction} from '../workflow-run-store.mjs';

function parseFinalJSON(text) {
  try { return {value:JSON.parse(text),syntax_repairs:0}; }
  catch (originalError) {
    // Native Agents sometimes insert a closing delimiter that cannot close the
    // current JSON container while serializing a long batch. Remove only those
    // impossible closers. Never invent a missing quote, comma, value or closer;
    // the repaired text must still parse and pass the pinned result schema.
    const pairs={'}':'{',']':'['},stack=[];let quoted=false,escaped=false,repairs=0,repaired='';
    for(const char of text){
      if(quoted){
        repaired+=char;
        if(escaped)escaped=false;
        else if(char==='\\')escaped=true;
        else if(char==='"')quoted=false;
        continue;
      }
      if(char==='"'){quoted=true;repaired+=char;continue;}
      if(char==='{'||char==='['){stack.push(char);repaired+=char;continue;}
      if(char==='}'||char===']'){
        if(stack.at(-1)===pairs[char]){stack.pop();repaired+=char;}
        else repairs++;
        continue;
      }
      repaired+=char;
    }
    if(!repairs||quoted||stack.length)throw originalError;
    return {value:JSON.parse(repaired),syntax_repairs:repairs};
  }
}

function finalPayload(turn,resultSchema,perItemResult=false,textAmendment=false) {
  const messages=(turn.items??[]).filter(item=>item.type==='agentMessage' && item.phase==='final_answer');
  if(messages.length!==1) return {status:'invalid',reason:`Native Agent turn ${turn.id} has no unique final answer`};
  let value,syntaxRepairs=0,hostProjected=false;
  try { ({value,syntax_repairs:syntaxRepairs}=parseFinalJSON(messages[0].text)); }
  catch { return {status:'invalid',reason:`Native Agent turn ${turn.id} final answer is not JSON`}; }
  if(textAmendment){
    if(syntaxRepairs)throw identityError('NATIVE_TEXT_AMENDMENT','Text amendments require exact valid JSON without syntax normalization');
    return {status:'amendment',amendment:value,result_shape:'text_amendment'};
  }
  if(perItemResult&&value&&typeof value==='object'&&!Array.isArray(value)&&Array.isArray(value.items)){
    const extras=Object.keys(value).filter(key=>key!=='items');
    const hostOwned=key=>/(?:^|_)(?:id|ids|path|paths|sha256|hash|hashes|checksum|checksums|token|tokens|index|indices|revision|receipt|receipts|timestamp|timestamps|uuid|uuids|nonce|nonces|seed|seeds|encoding|encoded)$/.test(key);
    if(extras.length&&extras.every(hostOwned)){hostProjected=true;value={items:value.items};}
  }
  if(value?.outcome==='blocked' && typeof value.block_reason==='string' && value.block_reason)
    return {status:'blocked',reason:value.block_reason,result_shape:'completion_envelope'};
  if(value?.outcome==='completed' && Object.hasOwn(value,'result'))
    return {status:'completed',result:value.result,result_shape:'completion_envelope'};
  if(value && typeof value==='object' && !Array.isArray(value) &&
    !['outcome','result','block_reason'].some(key=>Object.hasOwn(value,key)) &&
    resultSchema?.type==='object' && resultSchema.properties &&
    Array.isArray(resultSchema.required) && resultSchema.required.length &&
    resultSchema.required.every(key=>Object.hasOwn(resultSchema.properties,key))){
    try {
      // Per-item entries are journaled independently by the Host. Preserve valid
      // entries even if another entry needs a field-level repair.
      validateData(value,perItemResult
        ? {type:'object',properties:{items:{type:'array'}},required:['items'],additionalProperties:false}
        : resultSchema);
      const normalized=syntaxRepairs||hostProjected;
      return {status:'completed',result:value,
        result_shape:normalized?'bare_semantic_result_host_normalized':'bare_semantic_result',
        ...(normalized?{normalization:{syntax_repairs:syntaxRepairs,host_projected:hostProjected}}:{})};
    } catch(error) {
      if(error.code!=='DATA_INVALID')throw error;
      return {status:'invalid',reason:`Native Agent turn ${turn.id} bare semantic result is invalid: ${error.message}`};
    }
  }
  return {status:'invalid',reason:`Native Agent turn ${turn.id} has no valid outcome/result envelope`};
}

const identityError=(code,message)=>Object.assign(new Error(message),{code});
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const threadUuid=value=>typeof value==='string'&&/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value);
const NATIVE_EVENT_WAIT_MS=60*60*1000;

// Wait on Codex's durable session journal. The watcher is armed before the
// caller rechecks lifecycle state, so a terminal append cannot be lost between
// inspection and sleep. Only the target child journal wakes a resolved wait;
// unresolved registration wakes on a non-parent session event and immediately
// re-runs the exact parent-scoped identity lookup.
export async function waitForNativeSessionEvent({home=process.env.CODEX_HOME||join(homedir(),'.codex'),threadIds=[],
  parentThreadId,timeoutMs=NATIVE_EVENT_WAIT_MS,signal,watchImpl=watch,runJournalPath,onChange}={}) {
  if(!Number.isSafeInteger(timeoutMs)||timeoutMs<1||timeoutMs>NATIVE_EVENT_WAIT_MS)
    throw identityError('NATIVE_AGENT_WAIT_CONFIG','Native Agent event timeout must be an integer from 1 to 3600000 ms');
  if(!Array.isArray(threadIds)||threadIds.some(id=>typeof id!=='string'||!id))
    throw identityError('NATIVE_AGENT_WAIT_CONFIG','Native Agent event identities must be nonempty strings');
  if(runJournalPath!==undefined&&(typeof runJournalPath!=='string'||!isAbsolute(runJournalPath))||onChange!==undefined&&typeof onChange!=='function')
    throw identityError('NATIVE_AGENT_WAIT_CONFIG','Native wait requires an exact absolute Run journal and callable lifecycle predicate');
  const controller=new AbortController();
  const abort=()=>controller.abort(signal?.reason??identityError('NATIVE_AGENT_WAIT_CANCELLED','Native Agent event wait was cancelled'));
  if(signal?.aborted)abort();else signal?.addEventListener('abort',abort,{once:true});
  const timer=setTimeout(()=>controller.abort(identityError('NATIVE_AGENT_WAIT_TIMEOUT',
    `Native Agent produced no lifecycle event within ${timeoutMs} ms`)),timeoutMs);
  // This pending Host call owns the deadline even when a nonpersistent watcher
  // is the process's only other handle. Release it only when the wait settles.
  const streams=[];
  const next=stream=>stream.pending=Promise.resolve(stream.iterator.next()).then(value=>({stream,value}),error=>({stream,error}));
  try{
    streams.push({scope:'child',iterator:watchImpl(resolve(home,'sessions'),{recursive:true,persistent:false,signal:controller.signal})[Symbol.asyncIterator]()});
    if(runJournalPath)streams.push({scope:'run',iterator:watchImpl(dirname(runJournalPath),{persistent:false,signal:controller.signal})[Symbol.asyncIterator]()});
    streams.forEach(next);
    while(true){
      const received=await Promise.race(streams.map(stream=>stream.pending));
      if(received.error)throw received.error;
      if(received.value.done)throw identityError('NATIVE_AGENT_WAIT_CLOSED','Native Agent lifecycle watcher closed before an event');
      const {stream}=received,event=received.value.value;next(stream);
      const filename=event?.filename===null||event?.filename===undefined?'':String(event.filename);
      if(stream.scope==='run'){if(filename&&filename!==basename(runJournalPath))continue;}
      else{
        if(filename&&parentThreadId&&filename.includes(parentThreadId))continue;
        if(threadIds.length&&filename&&!threadIds.some(id=>filename.includes(id)))continue;
      }
      const observed={event_type:event?.eventType??'change',filename,event_scope:stream.scope};
      if(onChange){const changed=await onChange(observed);
        if(typeof changed!=='boolean')throw identityError('NATIVE_AGENT_WAIT_CONFIG','Native lifecycle predicate must return a boolean');
        if(!changed)continue;
      }
      return observed;
    }
  }catch(error){
    if(controller.signal.aborted)throw controller.signal.reason??identityError('NATIVE_AGENT_WAIT_CANCELLED','Native Agent event wait was cancelled');
    if(error.code?.startsWith('NATIVE_AGENT_'))throw error;
    throw Object.assign(new Error(`Native Agent lifecycle watch failed: ${error.code??error.message??'WATCH_ERROR'}`,{cause:error}),
      {code:'NATIVE_AGENT_WAIT_FAILED'});
  }finally{
    clearTimeout(timer);signal?.removeEventListener('abort',abort);controller.abort();
    await Promise.all(streams.map(async stream=>{await stream.pending;await stream.iterator.return?.();}));
  }
}

export function nativeParentThreadId(identity,{required=true}={}) {
  const supplied=identity.native_parent_thread_id,pinned=identity.constraints?.native_parent_thread_id;
  const hasSupplied=Object.hasOwn(identity,'native_parent_thread_id'),hasPinned=Object.hasOwn(identity.constraints??{},'native_parent_thread_id');
  if(hasSupplied&&hasPinned&&supplied!==pinned)
    throw identityError('NATIVE_AGENT_IDENTITY_PARENT','Conflicting native parent thread identities in launch fields and constraints');
  const explicit=hasSupplied?supplied:pinned;
  if(hasSupplied||hasPinned){
    if(!threadUuid(explicit))throw identityError('NATIVE_AGENT_IDENTITY_PARENT','native_parent_thread_id must be the actual controller thread UUID, not its logical main_actor label');
    return explicit;
  }
  if(required)throw identityError('NATIVE_AGENT_IDENTITY_PARENT',
    'Native execution requires an explicit native_parent_thread_id from the current controller thread before releasing any spawn packet');
}

export async function inspectNativeParent(client,parentThreadId) {
  nativeParentThreadId({native_parent_thread_id:parentThreadId});
  const read=await observerRead(client,'thread/read',{threadId:parentThreadId,includeTurns:false},parentThreadId,'PARENT');
  if(read?.thread?.id!==parentThreadId)
    throw identityError('NATIVE_AGENT_IDENTITY_PARENT',`Native parent verification returned a different thread; expected ${parentThreadId}`);
  const spawn=read.thread?.source?.subAgent?.thread_spawn??read.thread?.source?.subagent?.thread_spawn;
  const agentPath=spawn?.agent_path??'/root';
  if(agentPath!=='/root'&&(!agentPath.startsWith('/root/')||agentPath.split('/').slice(1).some(part=>!part||part==='.'||part==='..'||/\s/.test(part))))
    throw identityError('NATIVE_AGENT_IDENTITY_SCHEMA',`Native parent ${parentThreadId} has an invalid canonical Agent path`);
  return {thread_id:parentThreadId,agent_path:agentPath};
}

async function observerRead(client,method,params,agentId,phase) {
  try { return await client.call(method,params); }
  catch(error) { throw Object.assign(new Error(`Native Agent ${phase==='IDENTITY'?'identity lookup':phase==='PARENT'?'parent verification':'observation'} ${method} failed for ${agentId}: ${error.message}`,{cause:error}),
    {code:`NATIVE_AGENT_${phase}_RPC`}); }
}

async function latestNativeTurn(client,threadId,agentId,itemsView) {
  const page=await observerRead(client,'thread/turns/list',{threadId,limit:1,sortDirection:'desc',itemsView},agentId,'OBSERVATION');
  if(!Array.isArray(page?.data)||page.data.length>1||page.data.some(turn=>typeof turn?.id!=='string'||!turn.id||
    typeof turn.status!=='string'||!Array.isArray(turn.items)))
    throw identityError('NATIVE_AGENT_OBSERVATION_SCHEMA','Native turn lookup returned an unsupported single-turn page');
  return page.data[0];
}

// Native spawn receipts can contain a canonical collaboration path instead of a
// thread UUID. Query only this parent's indexed children; never scan rollout
// history or choose a same-named child from a different task.
async function findNativeThread(client,agentId,parentThreadId,checkActive) {
  nativeParentThreadId({native_parent_thread_id:parentThreadId});
  const matches=new Set(),cursors=new Set();let cursor;
  for(let pageIndex=0;pageIndex<20;pageIndex++){
    await checkActive();
    const page=await observerRead(client,'thread/list',{parentThreadId,sourceKinds:['subAgentThreadSpawn'],modelProviders:[],
      limit:100,useStateDbOnly:true,...(cursor?{cursor}:{})},agentId,'IDENTITY');
    await checkActive();
    if(!Array.isArray(page?.data))
      throw identityError('NATIVE_AGENT_IDENTITY_SCHEMA',`Native Agent identity lookup returned no child index for parent ${parentThreadId}`);
    for(const thread of page.data){
      const spawn=thread?.source?.subAgent?.thread_spawn;
      if(spawn?.agent_path!==agentId)continue;
      if(thread.parentThreadId!==parentThreadId||spawn.parent_thread_id!==parentThreadId)
        throw identityError('NATIVE_AGENT_IDENTITY_PARENT',`Native Agent path ${agentId} has inconsistent parent metadata; expected ${parentThreadId}`);
      if(!threadUuid(thread.id))
        throw identityError('NATIVE_AGENT_IDENTITY_SCHEMA',`Native Agent path ${agentId} has no valid indexed thread UUID`);
      matches.add(thread.id);
      if(matches.size>1)throw identityError('NATIVE_AGENT_IDENTITY_AMBIGUOUS',
        `Native Agent path ${agentId} identifies multiple children under parent ${parentThreadId}; cannot select a thread`);
    }
    if(page.nextCursor===null||page.nextCursor===undefined)return [...matches][0]??null;
    if(typeof page.nextCursor!=='string'||!page.nextCursor||cursors.has(page.nextCursor))
      throw identityError('NATIVE_AGENT_IDENTITY_SCHEMA',`Native Agent child index returned an invalid pagination cursor for parent ${parentThreadId}`);
    cursor=page.nextCursor;cursors.add(cursor);
  }
  throw identityError('NATIVE_AGENT_IDENTITY_LIMIT',`Native Agent identity lookup exceeded 20 filtered child pages for parent ${parentThreadId}`);
}

async function resolveNativeThread(client,agentId,{parentThreadId,identityAttempts=1,pollIntervalMs=5000,checkActive=async()=>{},onIdentityEvent=async()=>{}}={}) {
  if(typeof agentId!=='string'||!agentId)throw identityError('NATIVE_AGENT_IDENTITY_SCHEMA','Native Agent receipt requires a nonempty Agent ID');
  if(!agentId.startsWith('/'))return agentId;
  if(!agentId.startsWith('/root/')||agentId.split('/').slice(1).some(part=>!part||part==='.'||part==='..'||/\s/.test(part)))
    throw identityError('NATIVE_AGENT_IDENTITY_SCHEMA',`Invalid canonical native Agent path: ${agentId}`);
  for(let attempt=1;attempt<=identityAttempts;attempt++){
    const threadId=await findNativeThread(client,agentId,parentThreadId,checkActive);
    if(threadId){
      await onIdentityEvent({status:'native_identity_resolved',code:'NATIVE_AGENT_IDENTITY_RESOLVED',
        diagnostic:`Native Agent ${agentId} under parent ${parentThreadId} resolved to thread ${threadId}`});
      await checkActive();return threadId;
    }
    if(attempt===identityAttempts)throw identityError('NATIVE_AGENT_IDENTITY_NOT_FOUND',
      `Native Agent path ${agentId} is not registered under parent ${parentThreadId} after ${identityAttempts} indexed lookup(s)`);
    if(attempt===1)await onIdentityEvent({status:'waiting_native_registration',code:'NATIVE_AGENT_IDENTITY_PENDING',
      diagnostic:`Native Agent ${agentId} awaits registration under parent ${parentThreadId}; at most ${identityAttempts} indexed lookups, ${pollIntervalMs} ms apart`});
    await checkActive();await sleep(pollIntervalMs);
  }
}

async function inspectResolvedNativeAgent(client,agentId,threadId,{parentThreadId,afterTurnId,rejectedTurnIds=[],readLifecycle,onIdentityEvent=async()=>{},onThreadRead=()=>{},reported=new Set(),terminalSnapshots=new Map(),terminalAttempts=7,resultSchema,perItemResult=false,textAmendment=false}={}) {
  const read=await observerRead(client,'thread/read',{threadId,includeTurns:false},agentId,'OBSERVATION');
  if(read?.thread?.id!==threadId) throw identityError('NATIVE_AGENT_IDENTITY_SCHEMA',`Native Agent identity mismatch: ${agentId} expected thread ${threadId}`);
  if(parentThreadId && read.thread.parentThreadId!==parentThreadId)
    throw identityError('NATIVE_AGENT_IDENTITY_PARENT',`Native Agent ${agentId} has a different parent task; expected ${parentThreadId}`);
  const turn=await latestNativeTurn(client,threadId,agentId,'summary');
  onThreadRead(agentId,read.thread,turn);
  const lifecycle=await readLifecycle({thread:read.thread,agentId,parentThreadId,turn});
  const pendingFinal=async()=>{
    const key=agentId+':'+lifecycle.turn_id,count=(terminalSnapshots.get(key)??0)+1;terminalSnapshots.set(key,count);
    if(count>=terminalAttempts)throw identityError('NATIVE_AGENT_FINAL_UNAVAILABLE',
      `Native Agent ${agentId} owner ended turn ${lifecycle.turn_id}, but its exact full RPC result remains unavailable after ${count} reads`);
    if(count===1)await onIdentityEvent({status:'waiting_native_final',code:'NATIVE_AGENT_FINAL_PENDING',
      diagnostic:`Native Agent ${agentId} owner ended turn ${lifecycle.turn_id}; waiting for the exact full RPC snapshot, at most ${terminalAttempts} reads`});
    return {status:'pending',pending_phase:'final_snapshot',agent_id:agentId};
  };
  if(lifecycle.status==='pending'){
    const key=agentId+':'+turn?.id;
    if(turn&&!['pending','inProgress'].includes(turn.status)&&!reported.has(key)){
      reported.add(key);await onIdentityEvent({status:'waiting_native_terminal',code:'NATIVE_AGENT_TERMINAL_UNCONFIRMED',
        diagnostic:`Native Agent ${agentId} RPC projects turn ${turn.id} as ${turn.status}; the exact owner rollout has no terminal event for its current turn. Host remains pending.`});
    }
    return {status:'pending',pending_phase:'running',agent_id:agentId};
  }
  if(!turn||turn.id!==lifecycle.turn_id)return pendingFinal();
  if(turn.id===afterTurnId||rejectedTurnIds.includes(turn.id))return {status:'pending',pending_phase:'awaiting_new_turn',agent_id:agentId};
  if(lifecycle.status==='interrupted')return {status:'blocked',agent_id:agentId,turn_id:turn.id,reason:'Native Agent owner recorded turn_aborted (interrupted)'};
  if(lifecycle.status!=='completed')throw identityError('NATIVE_AGENT_LIFECYCLE_SCHEMA','Unsupported native lifecycle state');
  const full=turn.itemsView==='full'&&turn.items.some(item=>item.type==='agentMessage'&&item.phase==='final_answer')?turn:
    await latestNativeTurn(client,threadId,agentId,'full');
  if(full?.id!==turn.id)return pendingFinal();
  if(full.itemsView!=='full')
    throw identityError('NATIVE_AGENT_TURN_IDENTITY','Native final answer requires the exact completed turn with full, untruncated items');
  if(!full.items?.some(item=>item.type==='agentMessage'&&item.phase==='final_answer'))return pendingFinal();
  const confirmed=await readLifecycle({thread:read.thread,agentId,parentThreadId,turn:full});
  if(confirmed.turn_id!==turn.id||confirmed.status!=='completed')return {status:'pending',pending_phase:'final_snapshot',agent_id:agentId};
  return {...finalPayload(full,resultSchema,perItemResult,textAmendment),agent_id:agentId,turn_id:turn.id};
}

export async function inspectNativeAgent(client,agentId,options={}) {
  const threadId=await resolveNativeThread(client,agentId,options);
  const readLifecycle=options.readLifecycle??createNativeLifecycleReader({home:options.lifecycleHome??client.nativeObserverHome});
  return inspectResolvedNativeAgent(client,agentId,threadId,{...options,readLifecycle});
}

// The low-level inspector remains one-shot for diagnostics. Production passes
// waitForTerminal so the same Host call owns one durable event wait and returns
// only after a child terminal event or an explicit timeout/cancellation.
export async function inspectNativeAgents(client,agentIds,{pollIntervalMs=250,identityAttempts=1,terminalAttempts=7,
  checkActive=async()=>{},onIdentityEvent=async()=>{},parentThreadId,afterTurnIds={},rejectedTurnIds={},lifecycleHome,
  resultSchema,perItemResult=false,textAmendments={},readLifecycle=createNativeLifecycleReader({home:lifecycleHome??client.nativeObserverHome}),
  waitForTerminal=false,waitTimeoutMs=NATIVE_EVENT_WAIT_MS,waitForChange=waitForNativeSessionEvent,signal,runJournalPath}={}) {
  if(!Array.isArray(agentIds)||!agentIds.length) throw new Error('Native Agent inspection requires at least one recorded Agent ID');
  if(!Number.isSafeInteger(pollIntervalMs)||pollIntervalMs<=0) throw new Error('Native Agent final projection interval must be a positive integer');
  if(!Number.isSafeInteger(identityAttempts)||identityAttempts<1||identityAttempts>60)throw new Error('Native Agent identity attempts must be an integer from 1 to 60');
  if(!Number.isSafeInteger(terminalAttempts)||terminalAttempts<1||terminalAttempts>60)throw new Error('Native Agent terminal snapshot attempts must be an integer from 1 to 60');
  if(typeof waitForTerminal!=='boolean'||typeof waitForChange!=='function')
    throw identityError('NATIVE_AGENT_WAIT_CONFIG','Native Agent event wait configuration is invalid');
  const reported=new Set(),terminalSnapshots=new Map(),resolvedThreads=new Map(),knownThreads=new Map();
  const deadline=performance.now()+waitTimeoutMs;
  const lifecycleChanged=async event=>{
    signal?.throwIfAborted();
    if(event?.event_scope==='run'){await checkActive();return false;}
    if(!event)return true; // Explicit injected one-shot observer notification.
    for(const agentId of agentIds){
      const known=knownThreads.get(agentId);if(!known)return true;
      const state=await readLifecycle({thread:known.thread,turn:known.turn,agentId,parentThreadId});
      if(state.status!=='pending'&&state.turn_id!==afterTurnIds[agentId]&&!rejectedTurnIds[agentId]?.includes(state.turn_id))return true;
    }
    return false;
  };
  const inspectOnce=async()=>{
    let sawRegistrationPending=false;
    for(const agentId of agentIds){
      await checkActive();let threadId=resolvedThreads.get(agentId);
      if(!threadId)try {
        threadId=await resolveNativeThread(client,agentId,{parentThreadId,identityAttempts,checkActive,onIdentityEvent});
        resolvedThreads.set(agentId,threadId);
      }catch(error){
        if(error.code!=='NATIVE_AGENT_IDENTITY_NOT_FOUND')throw error;
        sawRegistrationPending=true;
        await onIdentityEvent({status:'waiting_native_registration',code:'NATIVE_AGENT_IDENTITY_PENDING',diagnostic:error.message});
        continue;
      }
      for(let snapshot=1;snapshot<=terminalAttempts;snapshot++){
        const result=await inspectResolvedNativeAgent(client,agentId,threadId,{parentThreadId,
          afterTurnId:afterTurnIds[agentId],rejectedTurnIds:rejectedTurnIds[agentId],readLifecycle,onIdentityEvent,
          onThreadRead:(id,thread,turn)=>knownThreads.set(id,{thread,turn}),
          reported,terminalSnapshots,terminalAttempts,resultSchema,perItemResult,textAmendment:textAmendments[agentId]===true});
        await checkActive();
        if(result.status!=='pending')return result;
        if(result.pending_phase!=='final_snapshot'||snapshot===terminalAttempts)break;
        await sleep(pollIntervalMs);
      }
    }
    return {status:'pending',pending_phase:sawRegistrationPending?'registration':'running',agent_ids:[...agentIds]};
  };
  let observed=await inspectOnce();
  if(!waitForTerminal||observed.status!=='pending')return observed;
  await onIdentityEvent({status:'waiting_native_event',code:'NATIVE_AGENT_EVENT_WAIT',
    diagnostic:`Host armed one event wait for ${agentIds.length} recorded native Agent(s), timeout ${waitTimeoutMs} ms`});
  while(observed.status==='pending'){
    await checkActive();
    const remaining=Math.ceil(deadline-performance.now());
    if(remaining<1)throw identityError('NATIVE_AGENT_WAIT_TIMEOUT','Native Agent terminal wait reached its original deadline');
    const eventController=new AbortController();
    const relayAbort=()=>eventController.abort(signal?.reason??identityError('NATIVE_AGENT_WAIT_CANCELLED','Native Agent event wait was cancelled'));
    if(signal?.aborted)relayAbort();else signal?.addEventListener('abort',relayAbort,{once:true});
    const outcome=Promise.resolve().then(()=>waitForChange({home:lifecycleHome??client.nativeObserverHome,
      threadIds:[...resolvedThreads.values()],parentThreadId,timeoutMs:remaining,signal:eventController.signal,runJournalPath,onChange:lifecycleChanged}))
      .then(value=>({value}),error=>({error}));
    // Close the inspect-to-sleep race: the watcher is live before this exact
    // second read. A terminal result cancels the now-unneeded watcher.
    try{
      // Let the scheduled waiter arm both durable streams before checking the
      // Run fence. A quiet authority commit before arm has no future event.
      await Promise.resolve();
      await checkActive();
      const rechecked=await lifecycleChanged({event_scope:'child'})?await inspectOnce():observed;
      if(rechecked.status!=='pending')return rechecked;
      const event=await outcome;
      if(event.error)throw event.error;
      if(!await lifecycleChanged(event.value))continue;
      await checkActive();observed=await inspectOnce();
    }finally{
      eventController.abort(identityError('NATIVE_AGENT_WAIT_COMPLETE','The exact native event wait has settled'));
      await outcome;signal?.removeEventListener('abort',relayAbort);
    }
  }
  return observed;
}

const observerDrives=new AsyncLocalStorage();

// One public native collection owns this connection. Recursive collection can
// reuse transport initialization; every identity/turn/lifecycle read stays fresh.
// This is neither a global client nor a cache spanning model tool calls.
export async function withNativeAgentObserverDrive(action,{env=process.env,clientFactory=createCodexClient,
  discoverImpl=discoverLocalCodex,onObservation=async()=>{}}={}) {
  const inherited=observerDrives.getStore();
  if(inherited){
    requireObserverDrive(inherited,env,clientFactory,discoverImpl);
    return action();
  }
  const started=performance.now(),pending=new Set(),failures=[];
  const owner={active:true,env,clientFactory,discoverImpl,pending,failures,client:null,opening:null,
    report:{schema_version:1,connections:0,actions:0,rpc:{},phases_ms:{}}};
  let result;
  try {result=await observerDrives.run(owner,action);}
  catch(error){failures.push(error);}
  finally {
    owner.active=false;
    // Already-started actions own their full wait. Closing a shared connection
    // while another action is outstanding would manufacture interrupted turns.
    await Promise.allSettled([...pending]);
    if(owner.client){
      const closeStarted=performance.now();
      try{await owner.client.close();}catch(error){failures.push(error);}
      owner.report.phases_ms.close=performance.now()-closeStarted;
    }
    owner.report.total_ms=performance.now()-started;
    owner.report.status=failures.length?'failed':'succeeded';
    owner.report.error_codes=[...new Set(failures.map(error=>error.code??'NATIVE_AGENT_OBSERVER_FAILED'))];
    const lifecycleChanges=[...new Set(failures)].filter(error=>error.code==='NATIVE_AGENT_LIFECYCLE_CHANGED'&&error.diagnostic).map(error=>error.diagnostic);
    if(lifecycleChanges.length)owner.report.lifecycle_changes=structuredClone(lifecycleChanges);
    try{await onObservation(structuredClone(owner.report));}catch(error){failures.push(error);}
  }
  const unique=[...new Set(failures)];
  if(unique.length===1)throw unique[0];
  if(unique.length)throw new AggregateError(unique,'Native observer drive or owned shutdown failed');
  return result;
}

function requireObserverDrive(owner,env,clientFactory,discoverImpl){
  if(!owner.active)throw identityError('NATIVE_AGENT_OBSERVER_SCOPE_EXPIRED','Native observer drive already settled');
  if(owner.env!==env||owner.clientFactory!==clientFactory||owner.discoverImpl!==discoverImpl)
    throw identityError('NATIVE_AGENT_OBSERVER_SCOPE','Native observer cannot reuse a drive with a different environment or client contract');
}

async function openObserver(owner){
  if(!owner.opening)owner.opening=(async()=>{
    let started=performance.now();
    const source=await owner.discoverImpl({env:owner.env});
    owner.report.phases_ms.discovery=performance.now()-started;
    const home=owner.env.CODEX_HOME||join(homedir(),'.codex');
    started=performance.now();
    const client=owner.client=owner.clientFactory(source.binary,{home,cwd:home,env:owner.env});
    owner.report.phases_ms.spawn=performance.now()-started;
    owner.report.connections++;
    const originalCall=client.call.bind(client);
    client.call=async(method,...args)=>{
      const rpcStarted=performance.now(),stats=owner.report.rpc[method]??={calls:0,failed:0,total_ms:0,max_ms:0};
      stats.calls++;
      try{return await originalCall(method,...args);}catch(error){stats.failed++;throw error;}
      finally{const elapsed=performance.now()-rpcStarted;stats.total_ms+=elapsed;stats.max_ms=Math.max(stats.max_ms,elapsed);}
    };
    client.nativeObserverHome=home;
    started=performance.now();
    await client.call('initialize',{clientInfo:{name:'codex_workflow_native_observer',version:'1.0.0'},capabilities:{experimentalApi:true}});
    client.initialized();
    owner.report.phases_ms.initialize=performance.now()-started;
    return client;
  })();
  return owner.opening;
}

export function withNativeAgentObserver(action,{env=process.env,clientFactory=createCodexClient,
  discoverImpl=discoverLocalCodex,onObservation=async()=>{}}={}) {
  assertOutsideHostRunTransaction();
  const owner=observerDrives.getStore();
  if(!owner)return withNativeAgentObserverDrive(()=>withNativeAgentObserver(action,{env,clientFactory,discoverImpl}),
    {env,clientFactory,discoverImpl,onObservation});
  try{requireObserverDrive(owner,env,clientFactory,discoverImpl);}catch(error){
    const rejected=Promise.reject(error);rejected.catch(()=>{});return rejected;
  }
  owner.report.actions++;
  const operation=(async()=>{
    const started=performance.now();
    try{return await action(await openObserver(owner));}
    catch(error){owner.failures.push(error);throw error;}
    finally{owner.report.phases_ms.actions=(owner.report.phases_ms.actions??0)+performance.now()-started;}
  })();
  owner.pending.add(operation);
  // Install both handlers immediately, including for a caller that fails to
  // await its operation. The drive still reports its failure before returning.
  operation.then(()=>owner.pending.delete(operation),()=>owner.pending.delete(operation));
  return operation;
}
