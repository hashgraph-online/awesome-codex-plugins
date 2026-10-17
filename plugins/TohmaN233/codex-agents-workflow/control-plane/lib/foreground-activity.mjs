import {AsyncLocalStorage} from 'node:async_hooks';
import {resolve,isAbsolute} from 'node:path';

const contexts=new AsyncLocalStorage(), roots=new Map(), priorities=new Map(), preparations=new WeakMap();
let acceptingPriorities=true;
const key=root=>process.platform==='win32'?resolve(root).toLowerCase():resolve(root);
const stateFor=root=>{
 const rootKey=key(root);let state=roots.get(rootKey);
 if(!state){state={active:0,pending:new Set(),handoffs:new Map()};roots.set(rootKey,state);}
 return state;
};
const priorityFor=(root,runId)=>{
 const rootKey=key(root);let runs=priorities.get(rootKey);
 if(!runs){runs=new Map();priorities.set(rootKey,runs);}
 if(!runs.has(runId))runs.set(runId,{controllers:new Map(),attempts:new Map()});
 return runs.get(runId);
};
const attemptScope=identity=>JSON.stringify([identity.controller_binding_hash,identity.node_id,identity.attempt_id,identity.lease_generation]);
function flushIdle(root){
 const rootKey=key(root),state=roots.get(rootKey);if(!state||state.active||state.handoffs.size)return;
 const pending=[...state.pending];state.pending.clear();roots.delete(rootKey);
 const failures=[];
 contexts.exit(()=>{for(const registration of pending)try{registration.flush();}catch(error){failures.push(error);}});
 if(failures.length)throw new AggregateError(failures,'Foreground activity release failed');
}

export function foregroundActivityCount(root){const state=roots.get(key(root));return state?(state.active+state.handoffs.size):0;}
export function inForegroundActivity(root){
 const scope=contexts.getStore();return Boolean(scope?.active&&scope.root===key(root));
}

// The private handoff registry is scheduling preference only. Its fixed exact
// identities contain neither controller tokens nor task/semantic contents.
// A fence invalidates preparations already awaiting I/O, including before the
// first retained handoff; no wall-clock expiry can replace a lease generation.
export function foregroundPriorityPreparation(root,runId){
 const rootKey=key(root),epochs=priorities.get(rootKey)?.get(runId),preparation=Object.freeze({});
 // Capture before authorization without guessing the eventual execution
 // identity. Only that validated identity's immutable epoch snapshot matters.
 preparations.set(preparation,{root:rootKey,runId,controllers:new Map(epochs?.controllers),attempts:new Map(epochs?.attempts)});
 return preparation;
}
export function retainedForegroundPriority(root,runId){return roots.get(key(root))?.handoffs.get(runId);}
export function retainForegroundPriority(root,identity,preparation){
 const snapshot=preparations.get(preparation),epochs=priorities.get(key(root))?.get(identity.run_id),scope=attemptScope(identity);
 if(!acceptingPriorities||!snapshot||snapshot.root!==key(root)||snapshot.runId!==identity.run_id
  ||snapshot.controllers.get(identity.controller_binding_hash)!==epochs?.controllers.get(identity.controller_binding_hash)
  ||snapshot.attempts.get(scope)!==epochs?.attempts.get(scope))
  throw Object.assign(new Error('Main handoff was fenced during preparation'),{code:'ATTEMPT_STOPPED'});
 const held=retainedForegroundPriority(root,identity.run_id);
 if(held&&['run_id','node_id','attempt_id','lease_generation','controller_binding_hash'].every(field=>held[field]===identity[field]))return;
 stateFor(root).handoffs.set(identity.run_id,Object.freeze({run_id:identity.run_id,node_id:identity.node_id,
  attempt_id:identity.attempt_id,lease_generation:identity.lease_generation,controller_binding_hash:identity.controller_binding_hash}));
}
export function fenceForegroundPriority(root,{run_id,controller_binding_hash,node_id,attempt_id,lease_generation}){
 const state=roots.get(key(root)),held=state?.handoffs.get(run_id);
 const epochs=priorityFor(root,run_id);
 if(node_id===undefined)epochs.controllers.set(controller_binding_hash,{});
 else{
  if(attempt_id===undefined||lease_generation===undefined)throw new TypeError('Foreground attempt fence needs its exact attempt and lease generation');
  epochs.attempts.set(attemptScope({controller_binding_hash,node_id,attempt_id,lease_generation}),{});
 }
 if(held&&(held.controller_binding_hash!==controller_binding_hash
  ||node_id!==undefined&&held.node_id!==node_id||attempt_id!==undefined&&held.attempt_id!==attempt_id
  ||lease_generation!==undefined&&held.lease_generation!==lease_generation))return;
 state?.handoffs.delete(run_id);flushIdle(root);
}
export function reconcileForegroundPriority(root,state,controllerBindingHash,expected){
 const held=roots.get(key(root))?.handoffs.get(state.run_id);
 if(held!==expected)return; // A later validated handoff owns its own settlement.
 if(!held){if(['succeeded','failed','cancelled','interrupted','paused'].includes(state.status))
  fenceForegroundPriority(root,{run_id:state.run_id,controller_binding_hash:controllerBindingHash});return;}
 const node=state.nodes[held.node_id],attempt=node?.attempts.find(item=>item.id===held.attempt_id);
 if(state.status==='running'&&held.controller_binding_hash===controllerBindingHash
  &&node?.active_attempt_id===held.attempt_id&&['claimed','running'].includes(node.status)
  &&['claimed','running'].includes(attempt?.status)&&(attempt.lease_generation??0)===held.lease_generation)return;
 if(['succeeded','failed','cancelled','interrupted','paused'].includes(state.status))
  fenceForegroundPriority(root,{run_id:state.run_id,controller_binding_hash:controllerBindingHash});
 // A superseded exact handoff cannot fence pending work under another node,
 // attempt, controller or generation that has not retained its own hold yet.
 if(retainedForegroundPriority(root,state.run_id)===held)fenceForegroundPriority(root,held);
}
export function stopForegroundPriorityRetains(){acceptingPriorities=false;}
export function releaseForegroundPriorities(){
 const failures=[];
 for(const [root,state] of roots){state.handoffs.clear();try{flushIdle(root);}catch(error){failures.push(error);}}
 priorities.clear();
 if(failures.length)throw new AggregateError(failures,'Foreground handoff shutdown failed');
}

// One registration per maintenance manager; callbacks grant no authority.
export function onForegroundIdle(root,flush){
 const state=roots.get(key(root));
 if(!state?.active&&!state?.handoffs.size){contexts.exit(flush);return ()=>{};}
 const registration={flush};state.pending.add(registration);
 return ()=>state.pending.delete(registration);
}

export async function withForegroundActivity(root,action){
 if(!isAbsolute(root)||typeof action!=='function')throw new TypeError('Foreground activity needs an absolute root and action');
 const rootKey=key(root);
 if(inForegroundActivity(root))return action();
 const state=stateFor(root);
 const scope={root:rootKey,active:true};state.active++;
 let result,failure,rejected=false;const failures=[];
 try{result=await contexts.run(scope,action);}catch(error){failure=error;rejected=true;}
 finally{
  scope.active=false;state.active--;
  // Only synchronous scheduling occurs; the original manager owns launched
  // promises, outside the completed request's async-local activity scope.
  try{flushIdle(root);}catch(error){failures.push(...error.errors);}
 }
 if(failures.length)throw new AggregateError([...(rejected?[failure]:[]),...failures],'Foreground activity release failed');
 if(rejected)throw failure;
 return result;
}
