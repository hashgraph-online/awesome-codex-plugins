import {canonicalJSON,digest} from '../workflow-revisions.mjs';
import {requireValue} from '../workflow-paths.mjs';
import {leaseToken} from '../workflow-execution-envelope.mjs';

const batchId=id=>typeof id==='string'&&/^[a-f0-9]{64}$/.test(id);

// Identity is authored by the Host before it releases spawn packets. Keeping
// the complete window makes a partially committed acknowledgement resumable.
export function nativeSpawnBatchIdentity(state,attempt,{node_id,spawns}){
  return {run_id:state.run_id,pins_hash:state.pins_hash,parent_thread_id:state.constraints.native_parent_thread_id,
    startup_key:state.constraints.host_startup_key??null,startup_sha256:state.constraints.host_startup_sha256??null,
    controller_binding:digest(state.control_hash),node_id,attempt_id:attempt.id,lease_generation:attempt.lease_generation??0,
    lease_binding:digest(attempt.lease_hash),dispatch_request_id:attempt.dispatch.request_id,
    envelope_hash:attempt.dispatch.envelope_hash,spawns:structuredClone(spawns)};
}

export function nativeSpawnBatchBinding(record,{batch_id,control_token,parent_thread_id}){
  const {state,pins}=record;
  requireValue(parent_thread_id===state.constraints.native_parent_thread_id,'NATIVE_AGENT_BATCH_PARENT',
    'Native batch acknowledgement requires its exact authenticated initiating conversation');
  requireValue(digest(control_token)===state.control_hash,'RUN_AUTHORITY','Native batch controller authority changed');
  const candidates=Object.entries(state.nodes).flatMap(([node_id,node])=>node.attempts.flatMap(attempt=>
    Object.values(attempt.native_spawn_batches??{}).map(receipt=>({node_id,node,attempt,receipt}))));
  if(batch_id===undefined){
    requireValue(candidates.length>0,'NATIVE_AGENT_BATCH_MISSING','No durable native spawn batch awaits acknowledgement');
    requireValue(candidates.length===1,'NATIVE_AGENT_BATCH_AMBIGUOUS',
      'Use the exact Host-generated batch adapter when more than one durable native spawn batch exists');
  }
  else requireValue(batchId(batch_id),'NATIVE_AGENT_BATCH_ID','Native batch identity must be the exact Host-generated digest');
  const matches=batch_id===undefined?candidates:candidates.filter(item=>item.receipt.batch_id===batch_id);
  requireValue(matches.length===1,'NATIVE_AGENT_BATCH_MISSING','No unique exact durable native spawn batch matches this acknowledgement');
  const {node_id,node,attempt,receipt}=matches[0];
  const definition=pins.root.workflow.nodes.find(item=>item.id===node_id);
  const provider=pins.providers.find(item=>item.id===definition?.executor?.provider_id);
  requireValue(provider?.kind==='native_agent'&&attempt.dispatch&&batchId(receipt.batch_id)&&
    digest(canonicalJSON(receipt.identity))===receipt.batch_id,'NATIVE_AGENT_BATCH_IDENTITY','Native batch receipt identity is invalid');
  const identity=nativeSpawnBatchIdentity(state,attempt,{node_id,spawns:receipt.identity.spawns});
  requireValue(canonicalJSON(identity)===canonicalJSON(receipt.identity),'NATIVE_AGENT_BATCH_STALE',
    'Native batch startup, controller, parent, lease generation or dispatch authority changed');
  requireValue(node.active_attempt_id===attempt.id,'NATIVE_AGENT_BATCH_STALE','Native batch attempt was superseded or released for retry');
  const spawns=receipt.identity.spawns;
  requireValue(Array.isArray(spawns)&&spawns.length>0&&spawns.length<=32&&spawns.every((spawn,index)=>
    Number.isSafeInteger(spawn.index)&&spawn.index>=0&&(index===0||spawns[index-1].index<spawn.index)&&
    typeof spawn.task_name==='string'&&/^[a-z0-9_]{1,64}$/.test(spawn.task_name)&&
    typeof spawn.agent_id==='string'&&spawn.agent_id.endsWith('/'+spawn.task_name)&&spawn.agent_id.length<=256)&&
    new Set(spawns.map(spawn=>spawn.agent_id)).size===spawns.length&&Array.isArray(receipt.acknowledged_indices)&&
    new Set(receipt.acknowledged_indices).size===receipt.acknowledged_indices.length&&
    receipt.acknowledged_indices.every(index=>spawns.some(spawn=>spawn.index===index)),
    'NATIVE_AGENT_BATCH_IDENTITY','Native batch receipt has invalid or conflicting slots');
  requireValue(spawns.every(spawn=>receipt.acknowledged_indices.includes(spawn.index))||
    ['claimed','running'].includes(node.status)&&['claimed','running'].includes(attempt.status),
    'NATIVE_AGENT_BATCH_STALE','An inactive native lease cannot acknowledge an uncommitted batch slot');
  for(const spawn of spawns){
    const acknowledged=receipt.acknowledged_indices.includes(spawn.index);
    requireValue(acknowledged?attempt.native_agents?.[spawn.index]===spawn.agent_id:
      attempt.native_pending_spawns?.[spawn.index]?.agent_id===spawn.agent_id&&
      attempt.native_pending_spawns[spawn.index].task_name===spawn.task_name,
      'NATIVE_AGENT_BATCH_CONFLICT','Native batch slot differs from its exact pending intent or acknowledgement');
  }
  return {definition,attempt,receipt,binding:{run_id:state.run_id,node_id,attempt_id:attempt.id,control_token,
    lease_token:leaseToken(control_token,state.run_id,node_id,attempt.id,attempt.lease_generation??0)}};
}
