import {timingSafeEqual} from 'node:crypto';
import {canonicalJSON,digest} from './workflow-revisions.mjs';
import {requireValue} from './workflow-paths.mjs';

// This contract grants only a bounded journal observation, never execution.
export const CODEX_EVENT_FIELDS=Object.freeze(['method', 'thread_id', 'turn_id', 'item_type', 'item_id','call_id','process_id','tool_name','tool_server','arguments_sha256','duration_ms','web_operation','web_terms_count', 'status', 'error_code', 'diagnostic', 'usage_available',
  'input_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'output_tokens', 'reasoning_output_tokens',
  'total_input_tokens', 'total_cached_input_tokens', 'total_cache_write_input_tokens', 'total_output_tokens', 'total_reasoning_output_tokens',
  'usage_basis', 'usage_unavailable_reason', 'usage_update_count',
  'usage_baseline_input_tokens', 'usage_baseline_cached_input_tokens', 'usage_baseline_cache_write_input_tokens', 'usage_baseline_output_tokens', 'usage_baseline_reasoning_output_tokens',
  'usage_total_input_tokens', 'usage_total_cached_input_tokens', 'usage_total_cache_write_input_tokens', 'usage_total_output_tokens', 'usage_total_reasoning_output_tokens']);
export function isExecutorObservation(event){
  return event?.kind==='codex_event'&&['item/started','item/completed','thread/tokenUsage/updated'].includes(event.metadata?.method);
}
export function validateExecutorObservation(event){
  requireValue(isExecutorObservation(event),'EXECUTOR_OBSERVATION_KIND','Only exact pure Codex notifications may append an observation');
  requireValue(event.metadata&&Object.keys(event.metadata).every(key=>CODEX_EVENT_FIELDS.includes(key))&&
    Object.values(event.metadata).every(value=>value===null||typeof value==='boolean'||typeof value==='string'&&value.length<=4096||Number.isSafeInteger(value))&&
    Buffer.byteLength(canonicalJSON(event))<=32000,'EXECUTOR_EVENT_SCHEMA','Executor events accept bounded metadata only, never raw auth/model payloads');
  validateCodexEventMetadata(event.metadata);
}
export function validateCodexEventMetadata(metadata){
  if(Object.hasOwn(metadata,'web_operation'))requireValue(['search','openPage','findInPage'].includes(metadata.web_operation),
    'EXECUTOR_EVENT_SCHEMA','Web metadata accepts recognized operation types only');
  if(Object.hasOwn(metadata,'web_terms_count'))requireValue(metadata.web_operation==='search'
    &&Number.isSafeInteger(metadata.web_terms_count)&&metadata.web_terms_count>=0,
    'EXECUTOR_EVENT_SCHEMA','Web term counts require an observed search operation');
}
export function authorizeRunController(state,token){
  requireValue(typeof state.control_hash==='string'&&/^[a-f0-9]{64}$/.test(state.control_hash),'RUN_STATE_CORRUPT','Run authority digest is invalid');
  requireValue(typeof token==='string'&&token.length<=256&&timingSafeEqual(Buffer.from(digest(token),'hex'),Buffer.from(state.control_hash,'hex')),
    'RUN_AUTHORITY','This action requires the Run main-controller capability');
}
export function executionAttempt(state,nodeId,attemptId,token,{active=true}={}){
  const node=state.nodes[nodeId];
  const attempt=node?.attempts.find(item=>item.id===attemptId);
  requireValue(attempt&&typeof token==='string'&&token.length<=256&&digest(token)===attempt.lease_hash,'LEASE_INVALID','Execution lease is invalid');
  if(active)requireValue(node.active_attempt_id===attemptId&&['claimed','running'].includes(node.status)&&['claimed','running'].includes(attempt.status),
    'STALE_LEASE','Execution lease is no longer active');
  return {node,attempt};
}
