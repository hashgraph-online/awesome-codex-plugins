import { workflowToolDefinitions } from '../workflow-tools.mjs';
import { validateData } from '../workflow-data-schema.mjs';
import { canonicalJSON } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { randomUUID } from 'node:crypto';
import { STARTUP_REFERENCE_PATTERN } from './prepared-startup-record.mjs';
import { WORKFLOW_CALL_DEFAULTS, WORKFLOW_LONG_CALL_TOOLS, WORKFLOW_CALL_PRAGMA, WORKFLOW_EXECUTION_TOOL_NAMESPACE, validateWorkflowMcpTransport } from '../workflow-call-policy.mjs';
export { WORKFLOW_CALL_DEFAULTS, WORKFLOW_LONG_CALL_TOOLS } from '../workflow-call-policy.mjs';

// Pure direct and legacy formatters are separate. The launching Host chooses
// one immutable family before any model-facing projection is constructed.
const schemas = new Map(workflowToolDefinitions().filter(tool => WORKFLOW_LONG_CALL_TOOLS.includes(tool.name))
  .map(tool => [tool.name, tool.inputSchema]));
const pragma = WORKFLOW_CALL_PRAGMA;
// Only the exact plain MCP text envelope can be presented without its wrapper.
// Rich results retain their complete original value; text itself stays opaque.
const presentResult = 'const exact=(v,k)=>v&&typeof v==="object"&&Reflect.ownKeys(v).length===k.length&&k.every(x=>Object.hasOwn(v,x));'
  + 'const c=exact(result,["content"])?result.content:null;'
  + 'text(Array.isArray(c)&&c.length===1&&exact(c,["0","length"])&&exact(c[0],["type","text"])&&c[0].type==="text"&&typeof c[0].text==="string"?c[0].text:result);';

/** A management continuation embeds the exact Host-owned controller authority. */
export function workflowControllerAdapterDescriptor(operation, authority) {
  noOptions(arguments.length, 2);
  requireValue(['drive','resume','cancel'].includes(operation), 'WORKFLOW_CONTROLLER_OPERATION', 'Unsupported Workflow controller continuation');
  const toolName=`workflow_${operation}`;
  const args={run_id:authority.run_id,control_token:authority.control_token};
  validateData(args,workflowToolDefinitions().find(tool=>tool.name===toolName).inputSchema);
  const json=canonicalJSON(args).replaceAll('\u2028','\\u2028').replaceAll('\u2029','\\u2029');
  return {schema_version:1,kind:'functions_exec',tool_name:toolName,slot:'none',scope:'workflow_controller_only',
    code:pragma+'const workflowData = JSON.parse(Function.prototype.toString.call(()=> ('+json+')).slice(6,-1));\n'
      +`const result = await tools.mcp__codex_agents_workflow__${toolName}(workflowData);\n`+presentResult};
}

/** Preserve the published authoring descriptor and its narrower scope. */
export function workflowAuthoringControllerAdapterDescriptor(operation, authority) {
  noOptions(arguments.length, 2);
  requireValue(['drive','resume','cancel'].includes(operation), 'AUTHORING_CONTROLLER_OPERATION', 'Unsupported authoring controller continuation');
  return {...workflowControllerAdapterDescriptor(operation,authority),scope:'authoring_controller_only'};
}

function noOptions(actual, expected) {
  requireValue(actual === expected, 'WORKFLOW_CALL_OPTIONS', 'Workflow call adapter accepts business arguments only');
}
function schemaFor(toolName) {
  requireValue(typeof toolName === 'string' && schemas.has(toolName), 'WORKFLOW_CALL_TOOL', 'This tool is not a supported public long Workflow call');
  return schemas.get(toolName);
}

/**
 * Explicit legacy executable template: the sole slot is canonical JSON from
 * workflowCallArguments. Prefix/suffix own the tool, parsing and budget.
 * The descriptor is useful only when the caller actually executes this source.
 */
export function workflowLegacyCallAdapterDescriptor(toolName) {
  noOptions(arguments.length, 1); schemaFor(toolName);
  const orchestration = toolName === 'workflow_orchestration_complete';
  return { schema_version: 1, kind: 'functions_exec', tool_name: toolName,
    // The fixed arrow is never called. Read its exact source after the six-byte
    // `()=> (` prefix and before `)`, then parse JSON as data. Evaluating an
    // object literal would lose own __proto__ keys; a JSON string would require
    // the caller to escape a second layer. This keeps only one JSON encoding.
    code_prefix: pragma + 'const workflowData = JSON.parse(Function.prototype.toString.call(()=> (',
    code_suffix: ')).slice(6,-1));\n' + `const result = await tools.mcp__codex_agents_workflow__${toolName}(${orchestration ? '{output:workflowData}' : 'workflowData'});\n` + presentResult,
    slot: orchestration ? 'output' : 'arguments',
    arguments_encoding: orchestration ? 'canonical_semantic_output_json' : 'canonical_business_json', scope: 'adopted_invocations_only' };
}

/** Validate real public business args and encode data, never executable source. */
export function workflowCallArguments(toolName, businessArgs) {
  noOptions(arguments.length, 2);
  const schema = schemaFor(toolName), json = canonicalJSON(businessArgs);
  validateData(JSON.parse(json), schema);
  // Encode data once. Quotes, backticks, interpolation and line separators stay
  // inert, without asking the model to hand-escape a JSON string inside JSON.
  return (toolName === 'workflow_orchestration_complete' ? canonicalJSON(JSON.parse(json).output) : json)
    .replaceAll('\u2028', '\\u2028').replaceAll('\u2029', '\\u2029');
}

/** Generate one actual functions.exec invocation with no caller options. */
export function workflowCallInvocation(toolName, businessArgs) {
  noOptions(arguments.length, 2);
  const descriptor = workflowLegacyCallAdapterDescriptor(toolName);
  return descriptor.code_prefix + workflowCallArguments(toolName, businessArgs) + descriptor.code_suffix;
}

/** Spawn acknowledgement reuses this exact Host batch, including after errors. */
export function workflowLegacyNativeSpawnBatchAdapterDescriptor(batchId){
  noOptions(arguments.length,1);
  requireValue(typeof batchId==='string'&&/^[a-f0-9]{64}$/.test(batchId),'NATIVE_AGENT_BATCH_ID',
    'Native spawn adapter requires its exact Host-generated batch identity');
  return {schema_version:1,kind:'functions_exec',tool_name:'workflow_native_spawned_batch',slot:'none',
    code:workflowCallInvocation('workflow_native_spawned_batch',{batch_id:batchId}),scope:'adopted_invocations_only'};
}

/** Host pins startup business data; the caller authors only the first semantic result. */
export function workflowLegacyStartupAdapterDescriptor(businessArgs, revisionHash) {
  noOptions(arguments.length, 2);
  requireValue(typeof revisionHash === 'string' && /^[a-f0-9]{64}$/.test(revisionHash),
    'WORKFLOW_STARTUP_REVISION', 'Startup adapter requires an exact Host revision');
  requireValue(!Object.hasOwn(businessArgs, 'initial_output') && !Object.hasOwn(businessArgs, 'revision_hash') && !Object.hasOwn(businessArgs, 'launch_key'),
    'WORKFLOW_STARTUP_FIELDS', 'Startup business arguments cannot replace the Host pin or semantic slot');
  const json = workflowCallArguments('workflow_start', { ...businessArgs, revision_hash: revisionHash, launch_key: randomUUID() });
  const descriptor = workflowLegacyCallAdapterDescriptor('workflow_start');
  return { ...descriptor, slot: 'initial_output', arguments_encoding: 'canonical_semantic_output_json',
    code_suffix: ')).slice(6,-1));\n' +
      'const workflowArgs = JSON.parse(Function.prototype.toString.call(()=> (' + json + ')).slice(6,-1));\n' +
      'workflowArgs.initial_output = workflowData;\n' +
      'const result = await tools.mcp__codex_agents_workflow__workflow_start(workflowArgs);\n' + presentResult };
}

/** Typed semantic preparation returns a whole Host-generated call, not a source slot. */
export function workflowLegacyPreparedStartupAdapterDescriptor(businessArgs, revisionHash, initialOutput) {
  noOptions(arguments.length, 3);
  requireValue(typeof revisionHash === 'string' && /^[a-f0-9]{64}$/.test(revisionHash),
    'WORKFLOW_STARTUP_REVISION', 'Startup adapter requires an exact Host revision');
  requireValue(!['initial_output','revision_hash','launch_key'].some(key => Object.hasOwn(businessArgs,key)),
    'WORKFLOW_STARTUP_FIELDS', 'Startup business arguments cannot replace the Host pin or semantic output');
  return {schema_version:1,kind:'functions_exec',tool_name:'workflow_start',slot:'none',
    code:workflowCallInvocation('workflow_start',{...businessArgs,revision_hash:revisionHash,
      launch_key:randomUUID(),initial_output:initialOutput}),scope:'adopted_invocations_only'};
}

export function workflowLegacyOrdinaryStartupAdapterDescriptor(businessArgs){
  noOptions(arguments.length,1);
  for(const field of ['revision_hash','startup_inputs_sha256','initial_output','launch_key'])
    requireValue(!Object.hasOwn(businessArgs,field),'WORKFLOW_STARTUP_FIELDS','Ordinary startup binds its current revision in the Host and returns the real initial Main handoff');
  return {schema_version:1,kind:'functions_exec',tool_name:'workflow_start',slot:'none',
    code:workflowCallInvocation('workflow_start',{...businessArgs,launch_key:randomUUID()}),scope:'adopted_invocations_only'};
}

/** Normal preparation embeds only an opaque Host reference; semantic JSON is data. */
export function workflowLegacyStartupReferenceAdapterDescriptor(startupReference, typed) {
  noOptions(arguments.length,2);
  requireValue(typeof startupReference==='string' && STARTUP_REFERENCE_PATTERN.test(startupReference),
    'WORKFLOW_PREPARATION_REFERENCE','Startup adapter requires an exact Host preparation UUID');
  requireValue(typeof typed==='boolean','WORKFLOW_PREPARATION_FIELDS','Preparation mode must be explicit');
  const toolName='workflow_start_prepared';
  if(typed)return {schema_version:1,kind:'functions_exec',tool_name:toolName,slot:'none',
    code:workflowCallInvocation(toolName,{startup_reference:startupReference}),scope:'adopted_invocations_only'};
  const descriptor=workflowLegacyCallAdapterDescriptor(toolName);
  return {...descriptor,slot:'initial_output',arguments_encoding:'canonical_semantic_output_json',
    code_suffix:')).slice(6,-1));\n'
      + `const result = await tools.mcp__codex_agents_workflow__${toolName}({startup_reference:${JSON.stringify(startupReference)},initial_output:workflowData});\n` + presentResult};
}

function directDescriptor(toolName, fixedArgs, slot) {
  const schema = schemaFor(toolName);
  const args = JSON.parse(canonicalJSON(fixedArgs));
  validateData(args, schema);
  return { schema_version: 2, kind: 'direct_mcp', tool_name: toolName,
    tool: WORKFLOW_EXECUTION_TOOL_NAMESPACE + toolName, arguments: args, slot,
    ...(slot === 'none' ? {} : { slot_schema: JSON.parse(canonicalJSON(slot === 'arguments' ? schema : schema.properties[slot])) }),
    scope: 'direct_mcp_only' };
}

/** A typed direct call whose sole unfilled slot is public business/semantic data. */
export function workflowCallAdapterDescriptor(toolName) {
  noOptions(arguments.length, 1);
  const schema = schemaFor(toolName), orchestration = toolName === 'workflow_orchestration_complete';
  // Required arguments are supplied by the caller's slot, not fabricated here.
  return { schema_version: 2, kind: 'direct_mcp', tool_name: toolName,
    tool: WORKFLOW_EXECUTION_TOOL_NAMESPACE + toolName, arguments: {},
    slot: orchestration ? 'output' : 'arguments',
    slot_schema: JSON.parse(canonicalJSON(orchestration ? schema.properties.output : schema)), scope: 'direct_mcp_only' };
}

/** Validate the actual public argument envelope before a direct MCP submission. */
export function workflowDirectCallInvocation(toolName, businessArgs) {
  noOptions(arguments.length, 2);
  const descriptor = directDescriptor(toolName, businessArgs, 'none');
  return { tool: descriptor.tool, arguments: descriptor.arguments };
}

export function workflowNativeSpawnBatchAdapterDescriptor(batchId) {
  noOptions(arguments.length, 1);
  requireValue(typeof batchId === 'string' && /^[a-f0-9]{64}$/.test(batchId), 'NATIVE_AGENT_BATCH_ID',
    'Native spawn adapter requires its exact Host-generated batch identity');
  return directDescriptor('workflow_native_spawned_batch', { batch_id: batchId }, 'none');
}

export function workflowStartupAdapterDescriptor(businessArgs, revisionHash) {
  noOptions(arguments.length, 2);
  requireValue(typeof revisionHash === 'string' && /^[a-f0-9]{64}$/.test(revisionHash),
    'WORKFLOW_STARTUP_REVISION', 'Startup adapter requires an exact Host revision');
  requireValue(!['initial_output', 'revision_hash', 'launch_key'].some(key => Object.hasOwn(businessArgs, key)),
    'WORKFLOW_STARTUP_FIELDS', 'Startup business arguments cannot replace the Host pin or semantic slot');
  return directDescriptor('workflow_start', { ...businessArgs, revision_hash: revisionHash, launch_key: randomUUID() }, 'initial_output');
}

export function workflowPreparedStartupAdapterDescriptor(businessArgs, revisionHash, initialOutput) {
  noOptions(arguments.length, 3);
  const descriptor = workflowStartupAdapterDescriptor(businessArgs, revisionHash);
  return directDescriptor('workflow_start', { ...descriptor.arguments, initial_output: initialOutput }, 'none');
}

export function workflowOrdinaryStartupAdapterDescriptor(businessArgs) {
  noOptions(arguments.length, 1);
  for (const field of ['revision_hash', 'startup_inputs_sha256', 'initial_output', 'launch_key'])
    requireValue(!Object.hasOwn(businessArgs, field), 'WORKFLOW_STARTUP_FIELDS', 'Ordinary startup binds its current revision in the Host and returns the real initial Main handoff');
  return directDescriptor('workflow_start', { ...businessArgs, launch_key: randomUUID() }, 'none');
}

/** Prepared startup exposes only its opaque reference and fresh semantic slot. */
export function workflowStartupReferenceAdapterDescriptor(startupReference, typed) {
  noOptions(arguments.length, 2);
  requireValue(typeof startupReference === 'string' && STARTUP_REFERENCE_PATTERN.test(startupReference),
    'WORKFLOW_PREPARATION_REFERENCE', 'Startup adapter requires an exact Host preparation UUID');
  requireValue(typeof typed === 'boolean', 'WORKFLOW_PREPARATION_FIELDS', 'Preparation mode must be explicit');
  return directDescriptor('workflow_start_prepared', { startup_reference: startupReference }, typed ? 'none' : 'initial_output');
}

/** Host-selected protocol binding; never inspect caller data or tool failures. */
export function workflowInvocationAdapters(transport) {
  noOptions(arguments.length, 1); validateWorkflowMcpTransport(transport);
  return Object.freeze(transport === 'direct_mcp' ? {
    call: workflowCallAdapterDescriptor, nativeSpawnBatch: workflowNativeSpawnBatchAdapterDescriptor,
    startupReference: workflowStartupReferenceAdapterDescriptor,
  } : {
    call: workflowLegacyCallAdapterDescriptor, nativeSpawnBatch: workflowLegacyNativeSpawnBatchAdapterDescriptor,
    startupReference: workflowLegacyStartupReferenceAdapterDescriptor,
  });
}

/** Encode semantic output only; the adapter owns its public tool envelope. */
export function workflowOrchestrationArguments(output) {
  noOptions(arguments.length, 1);
  return workflowCallArguments('workflow_orchestration_complete', { output });
}

/** Complete orchestration without asking the caller to author protocol fields. */
export function workflowOrchestrationInvocation(output) {
  noOptions(arguments.length, 1);
  return workflowCallInvocation('workflow_orchestration_complete', { output });
}

/**
 * Resume the exact cell ID returned by functions.exec. The caller must supply
 * that real receipt; a standalone formatter cannot attest its provenance.
 */
export function workflowCallResume(cellId) {
  noOptions(arguments.length, 1);
  requireValue(typeof cellId === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(cellId), 'WORKFLOW_CALL_CELL', 'Resume requires the exact cell ID returned by functions.exec');
  return { tool: 'functions.wait', arguments: { cell_id: cellId, yield_time_ms: WORKFLOW_CALL_DEFAULTS.yield_time_ms,
    max_tokens: WORKFLOW_CALL_DEFAULTS.max_output_tokens } };
}
