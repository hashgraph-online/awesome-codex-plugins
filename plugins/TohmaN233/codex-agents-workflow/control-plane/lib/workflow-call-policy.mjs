import { requireValue } from './workflow-paths.mjs';

// Portable Host wait policy. Each MCP launcher binds its invocation contract;
// untagged historical management launchers keep their code-mode contract.
export const WORKFLOW_WAIT_SECONDS = 3600;
export const WORKFLOW_EXECUTION_MCP_SERVER = 'caw-execution';
export const WORKFLOW_EXECUTION_TOOL_NAMESPACE = 'mcp__caw_execution__';
export const WORKFLOW_CALL_DEFAULTS = Object.freeze({ yield_time_ms: WORKFLOW_WAIT_SECONDS * 1000, max_output_tokens: 10000 });
export const WORKFLOW_LONG_CALL_TOOLS = Object.freeze(['workflow_start', 'workflow_start_prepared', 'workflow_native_next', 'workflow_native_spawned_batch',
  'workflow_native_followed_up', 'workflow_orchestration_complete']);
export const WORKFLOW_DIRECT_TOOLS = Object.freeze([...WORKFLOW_LONG_CALL_TOOLS, 'workflow_startup_contract']);
export const WORKFLOW_MCP_TRANSPORT_ENV = 'WORKFLOW_MCP_TRANSPORT';
export function validateWorkflowMcpTransport(transport) {
  requireValue(transport === 'code_mode' || transport === 'direct_mcp', 'WORKFLOW_MCP_TRANSPORT',
    'Workflow MCP transport must be the launcher-bound code_mode or direct_mcp contract');
  return transport;
}
export function workflowMcpTransport(env = {}) {
  return validateWorkflowMcpTransport(env[WORKFLOW_MCP_TRANSPORT_ENV] === undefined ? 'code_mode' : env[WORKFLOW_MCP_TRANSPORT_ENV]);
}
export const WORKFLOW_CALL_PRAGMA = `// @exec: ${JSON.stringify({ max_output_tokens: WORKFLOW_CALL_DEFAULTS.max_output_tokens,
  yield_time_ms: WORKFLOW_CALL_DEFAULTS.yield_time_ms })}\n`;

// Exposure belongs to the plugin MCP registration, not these descriptions.
export function workflowInvocationDescription(toolName, description, transport = 'code_mode') {
  validateWorkflowMcpTransport(transport);
  if (!WORKFLOW_LONG_CALL_TOOLS.includes(toolName)) return description;
  if (transport === 'code_mode') return 'Host invocation preset for functions.exec: ' + WORKFLOW_CALL_PRAGMA
    + 'Use the Host-supplied executable adapter and fill only its business or semantic slot. '
    + `If execution yields, resume its exact returned cell_id with functions.wait using yield_time_ms=${WORKFLOW_CALL_DEFAULTS.yield_time_ms} and max_tokens=${WORKFLOW_CALL_DEFAULTS.max_output_tokens}.\n`
    + description;
  return `Direct MCP call: ${WORKFLOW_EXECUTION_TOOL_NAMESPACE}${toolName}. Use its typed business arguments. `
    + 'Host-supplied invocation descriptors bind fixed arguments and identify the semantic slot. '
    + 'If this direct tool is unavailable, report the missing execution interface; no alternate invocation is implied.\n'
    + description;
}
