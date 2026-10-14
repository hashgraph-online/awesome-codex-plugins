import { requireValue } from '../workflow-paths.mjs';

// This metadata comes only from the authenticated caller's physical rollout,
// alongside model/effort selection. Workflow inputs never select permissions.
export function mainExecutionContext(payload, parentThreadId) {
  if (!Object.hasOwn(payload, 'sandbox_policy')) return undefined;
  const policy = payload.sandbox_policy;
  requireValue(policy && typeof policy === 'object' && !Array.isArray(policy)
    && ['read-only', 'workspace-write', 'danger-full-access'].includes(policy.type),
  'MAIN_EXECUTION_POLICY', 'Caller turn has an unknown sandbox policy');
  requireValue(policy.type !== 'danger-full-access' || Object.keys(policy).every(key => key === 'type'),
    'MAIN_EXECUTION_POLICY', 'Caller unrestricted policy contains contradictory restrictions');
  return { parent_thread_id: parentThreadId, sandbox_type: policy.type };
}

export function cooperativeExecutionPolicy(access, context) {
  requireValue(['read_only', 'bounded_write'].includes(access), 'CODEX_ACCESS_MODE', 'Unknown node access mode');
  if (context !== undefined) {
    requireValue(context && typeof context.parent_thread_id === 'string' && context.parent_thread_id.length > 0
      && ['read-only', 'workspace-write', 'danger-full-access'].includes(context.sandbox_type),
    'MAIN_EXECUTION_POLICY', 'Host caller execution metadata is invalid');
    requireValue(access !== 'bounded_write' || context.sandbox_type !== 'read-only',
      'MAIN_EXECUTION_POLICY', 'Writable Main node contradicts the caller read-only policy');
  }
  const inherited = access === 'bounded_write' && context?.sandbox_type === 'danger-full-access';
  return Object.freeze({
    basis: inherited ? 'authenticated_parent_turn_context' : 'node_access',
    ...(context ? { parent_thread_id: context.parent_thread_id, parent_sandbox_type: context.sandbox_type } : {}),
    thread_sandbox: inherited ? 'danger-full-access' : access === 'read_only' ? 'read-only' : 'workspace-write',
    thread_type: inherited ? 'dangerFullAccess' : access === 'read_only' ? 'readOnly' : 'workspaceWrite',
    command_type: inherited ? 'dangerFullAccess' : 'workspaceWrite',
    command_boundary: access === 'read_only' ? 'capture_spool_only' : 'host_allowed_paths_and_workspace_audit',
    os_read_isolation: 'not_claimed',
  });
}
