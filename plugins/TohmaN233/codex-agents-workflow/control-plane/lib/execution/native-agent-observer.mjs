import { homedir } from 'node:os';
import { watch } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { createCodexClient } from './codex-app-server-client.mjs';
import { discoverLocalCodex } from './local-codex-catalog.mjs';
import { createNativeLifecycleReader } from './native-agent-lifecycle.mjs';
import { validateData } from '../workflow-data-schema.mjs';

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

function finalPayload(turn,resultSchema,perItemResult=false) {
  const messages=(turn.items??[]).filter(item=>item.type==='agentMessage' && item.phase==='final_answer');
  if(messages.length!==1) return {status:'invalid',reason:`Native Agent turn ${turn.id} has no unique final answer`};
  let value,syntaxRepairs=0,hostProjected=false;
  try { ({value,syntax_repairs:syntaxRepairs}=parseFinalJSON(messages[0].text)); }
  catch { return {status:'invalid',reason:`Native Agent turn ${turn.id} final answer is not JSON`}; }
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
  parentThreadId,timeoutMs=NATIVE_EVENT_WAIT_MS,signal,watchImpl=watch}={}) {
  if(!Number.isSafeInteger(timeoutMs)||timeoutMs<1||timeoutMs>NATIVE_EVENT_WAIT_MS)
    throw identityError('NATIVE_AGENT_WAIT_CONFIG','Native Agent event timeout must be an integer from 1 to 3600000 ms');
  if(!Array.isArray(threadIds)||threadIds.some(id=>typeof id!=='string'||!id))
    throw identityError('NATIVE_AGENT_WAIT_CONFIG','Native Agent event identities must be nonempty strings');
  const controller=new AbortController();
  const abort=()=>controller.abort(signal?.reason??identityError('NATIVE_AGENT_WAIT_CANCELLED','Native Agent event wait was cancelled'));
  if(signal?.aborted)abort();else signal?.addEventListener('abort',abort,{once:true});
  const timer=setTimeout(()=>controller.abort(identityError('NATIVE_AGENT_WAIT_TIMEOUT',
    `Native Agent produced no lifecycle event within ${timeoutMs} ms`)),timeoutMs);
  // This pending Host call owns the deadline even when a nonpersistent watcher
  // is the process's only other handle. Release it only when the wait settles.
  try{
    const events=watchImpl(resolve(home,'sessions'),{recursive:true,persistent:false,signal:controller.signal});
    for await(const event of events){
      const filename=event?.filename===null||event?.filename===undefined?'':String(event.filename);
      if(filename&&parentThreadId&&filename.includes(parentThreadId))continue;
      if(threadIds.length&&filename&&!threadIds.some(id=>filename.includes(id)))continue;
      return {event_type:event?.eventType??'change',filename};
    }
    throw identityError('NATIVE_AGENT_WAIT_CLOSED','Native Agent lifecycle watcher closed before an event');
  }catch(error){
    if(controller.signal.aborted)throw controller.signal.reason??identityError('NATIVE_AGENT_WAIT_CANCELLED','Native Agent event wait was cancelled');
    if(error.code?.startsWith('NATIVE_AGENT_'))throw error;
    throw Object.assign(new Error(`Native Agent lifecycle watch failed: ${error.code??error.message??'WATCH_ERROR'}`,{cause:error}),
      {code:'NATIVE_AGENT_WAIT_FAILED'});
  }finally{
    clearTimeout(timer);signal?.removeEventListener('abort',abort);
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

async function inspectResolvedNativeAgent(client,agentId,threadId,{parentThreadId,afterTurnId,rejectedTurnIds=[],readLifecycle,onIdentityEvent=async()=>{},reported=new Set(),terminalSnapshots=new Map(),terminalAttempts=7,resultSchema,perItemResult=false}={}) {
  const read=await observerRead(client,'thread/read',{threadId,includeTurns:false},agentId,'OBSERVATION');
  if(read?.thread?.id!==threadId) throw identityError('NATIVE_AGENT_IDENTITY_SCHEMA',`Native Agent identity mismatch: ${agentId} expected thread ${threadId}`);
  if(parentThreadId && read.thread.parentThreadId!==parentThreadId)
    throw identityError('NATIVE_AGENT_IDENTITY_PARENT',`Native Agent ${agentId} has a different parent task; expected ${parentThreadId}`);
  const turn=await latestNativeTurn(client,threadId,agentId,'summary');
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
  return {...finalPayload(full,resultSchema,perItemResult),agent_id:agentId,turn_id:turn.id};
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
  resultSchema,perItemResult=false,readLifecycle=createNativeLifecycleReader({home:lifecycleHome??client.nativeObserverHome}),
  waitForTerminal=false,waitTimeoutMs=NATIVE_EVENT_WAIT_MS,waitForChange=waitForNativeSessionEvent,signal}={}) {
  if(!Array.isArray(agentIds)||!agentIds.length) throw new Error('Native Agent inspection requires at least one recorded Agent ID');
  if(!Number.isSafeInteger(pollIntervalMs)||pollIntervalMs<=0) throw new Error('Native Agent final projection interval must be a positive integer');
  if(!Number.isSafeInteger(identityAttempts)||identityAttempts<1||identityAttempts>60)throw new Error('Native Agent identity attempts must be an integer from 1 to 60');
  if(!Number.isSafeInteger(terminalAttempts)||terminalAttempts<1||terminalAttempts>60)throw new Error('Native Agent terminal snapshot attempts must be an integer from 1 to 60');
  if(typeof waitForTerminal!=='boolean'||typeof waitForChange!=='function')
    throw identityError('NATIVE_AGENT_WAIT_CONFIG','Native Agent event wait configuration is invalid');
  const reported=new Set(),terminalSnapshots=new Map(),resolvedThreads=new Map();
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
          reported,terminalSnapshots,terminalAttempts,resultSchema,perItemResult});
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
    const eventController=new AbortController();
    const relayAbort=()=>eventController.abort(signal?.reason??identityError('NATIVE_AGENT_WAIT_CANCELLED','Native Agent event wait was cancelled'));
    if(signal?.aborted)relayAbort();else signal?.addEventListener('abort',relayAbort,{once:true});
    const outcome=Promise.resolve(waitForChange({home:lifecycleHome??client.nativeObserverHome,
      threadIds:[...resolvedThreads.values()],parentThreadId,timeoutMs:waitTimeoutMs,signal:eventController.signal}))
      .then(value=>({value}),error=>({error}));
    // Close the inspect-to-sleep race: the watcher is live before this exact
    // second read. A terminal result cancels the now-unneeded watcher.
    const rechecked=await inspectOnce();
    if(rechecked.status!=='pending'){
      eventController.abort(identityError('NATIVE_AGENT_WAIT_COMPLETE','Native Agent became terminal while the event wait was armed'));
      await outcome;signal?.removeEventListener('abort',relayAbort);return rechecked;
    }
    const event=await outcome;signal?.removeEventListener('abort',relayAbort);
    if(event.error)throw event.error;
    await checkActive();observed=await inspectOnce();
  }
  return observed;
}

export async function withNativeAgentObserver(action,{env=process.env,clientFactory=createCodexClient}={}) {
  const source=await discoverLocalCodex({env});
  const home=env.CODEX_HOME || join(homedir(),'.codex');
  const client=clientFactory(source.binary,{home,cwd:home,env});
  client.nativeObserverHome=home;
  try {
    await client.call('initialize',{clientInfo:{name:'codex_workflow_native_observer',version:'1.0.0'},capabilities:{experimentalApi:true}});
    client.initialized();
    return await action(client);
  } finally { await client.close(); }
}
