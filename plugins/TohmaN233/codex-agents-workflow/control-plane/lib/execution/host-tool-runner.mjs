import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { validateData, validateDataSchema } from '../workflow-data-schema.mjs';
import { intersectBoundaries, pathBoundaries } from '../workflow-bindings.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { isAbsolute,resolve } from 'node:path';
import { lstat,realpath } from 'node:fs/promises';

const MAX_INPUT = 128 * 1024;
const MAX_OUTPUT = 1024 * 1024;
const statusValues = new Set(['succeeded', 'failed', 'timed_out', 'cancelled']);
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const credentialKey = /(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|cookie|secret)/i;
const credentialText = /(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|cookie|secret)\s*[:=]\s*(?:"[^"]*"|'[^']*'|\S+)/i;
function stringArray(value, field, max = 64) { requireValue(Array.isArray(value) && value.length <= max && value.every(item => typeof item === 'string' && item.length > 0 && item.length <= 1024), 'HOST_TOOL_CONTRACT', `${field} needs bounded strings`); return [...new Set(value)]; }
function redactValue(value) {
  if (Array.isArray(value)) return value.map(redactValue);
  if (object(value)) return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, credentialKey.test(key) ? '[redacted]' : redactValue(item)]));
  return value;
}
function safeDiagnostic(value, cap = 2048) {
  const text = String(value ?? '');
  try { return JSON.stringify(redactValue(JSON.parse(text))).slice(0, cap); }
  catch { return text.replace(/((?:["']?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|cookie|secret)["']?\s*[:=]\s*)(?:"[^"]*"|'[^']*'|\S+))/ig, (_all, prefix) => `${prefix}[redacted]`).replace(/\bBearer\s+\S+/ig, 'Bearer [redacted]').slice(0, cap); }
}
function noCredential(value, code = 'HOST_TOOL_SECRET') {
  const visit = item => {
    if (Array.isArray(item)) return item.forEach(visit);
    if (object(item)) return Object.entries(item).forEach(([key, nested]) => { requireValue(!credentialKey.test(key), code, 'Host tool input/output contains a credential-shaped key'); visit(nested); });
    if (typeof item === 'string') requireValue(!credentialText.test(item) && !/\bBearer\s+\S+/i.test(item), code, 'Host tool input/output contains credential-shaped text');
  };
  visit(value);
}
function boundedEffects(raw, permissions) {
  requireValue(object(raw) && raw.observed === true && Array.isArray(raw.changed_paths) && Array.isArray(raw.outside_paths) && Array.isArray(raw.artifacts) && Object.keys(raw).every(key => ['observed', 'changed_paths', 'outside_paths', 'artifacts'].includes(key)), 'HOST_TOOL_EFFECT_OBSERVATION', 'Qualified broker must attest observed paths and artifact references');
  const changed = pathBoundaries(raw.changed_paths);
  requireValue(changed.every(path => permissions.write_paths.some(root => root === '.' || path === root || path.startsWith(root + '/'))), 'HOST_TOOL_SCOPE', 'Broker observed a write outside the effective host-tool scope');
  requireValue(raw.outside_paths.every(path => typeof path === 'string' && path.length > 0 && path.length <= 4096), 'HOST_TOOL_EFFECT_OBSERVATION', 'Outside-path observations must be bounded strings');
  requireValue(raw.artifacts.length <= 64 && raw.artifacts.every(item => object(item) && typeof item.id === 'string' && /^[a-f0-9]{64}$/.test(item.sha256) && Number.isSafeInteger(item.bytes) && item.bytes >= 0 && item.bytes <= 32 * 1024 * 1024 && Object.keys(item).every(key => ['id', 'sha256', 'bytes'].includes(key))), 'HOST_TOOL_EFFECT_OBSERVATION', 'Broker artifact references must be bounded content identities');
  return { observed: true, changed_paths: changed, outside_paths: [...raw.outside_paths], artifacts: structuredClone(raw.artifacts) };
}
function resourceProgramScratch(contract) {
  if (contract.identity?.name !== 'workflow-resource-program') return null;
  requireValue(contract.argv.length >= 3, 'WORKFLOW_RESOURCE_CONTRACT', 'Workflow resource program needs an executable, resource and Host scratch path');
  const [scratch] = pathBoundaries([contract.argv[2]]);
  requireValue(scratch !== '.', 'WORKFLOW_RESOURCE_CONTRACT', 'Workflow resource scratch must be a dedicated workspace path');
  return scratch;
}
function effectivePermissions(contract, context) {
  const node = context?.permissions;
  requireValue(object(node) && ['read_only', 'bounded_write'].includes(node.access) && Array.isArray(node.allowed_paths), 'HOST_TOOL_PERMISSION_CONTEXT', 'Host tool requires exact Run/node permission context');
  const nodePaths = pathBoundaries(node.allowed_paths);
  const writes = contract.permissions.write_paths.length ? intersectBoundaries(contract.permissions.write_paths, nodePaths) : [];
  const scratch = resourceProgramScratch(contract);
  const scratchPaths = scratch ? intersectBoundaries([scratch], nodePaths) : [];
  requireValue(node.access === 'bounded_write' || contract.permissions.write_paths.length === 0 && !scratch, 'HOST_TOOL_PERMISSION', 'A read-only node cannot invoke a write-capable host tool');
  requireValue(!contract.permissions.write_paths.length || writes.length, 'HOST_TOOL_PERMISSION', 'Pinned host-tool write scope has no Run/node intersection');
  requireValue(!scratch || scratchPaths.length, 'WORKFLOW_RESOURCE_SCOPE', 'Host scratch path is outside the Run/node write scope');
  return { network: contract.permissions.network, read_paths: [...contract.permissions.read_paths], write_paths: pathBoundaries([...writes, ...scratchPaths]) };
}

export function requireHostToolExecutionScope(contract, permissions) {
  return effectivePermissions(validateHostToolContract(contract), { permissions });
}
async function declaredWorkspace(input, context) {
  if (!Object.hasOwn(input, 'workspace')) return;
  requireValue(typeof input.workspace === 'string' && isAbsolute(input.workspace), 'HOST_TOOL_WORKSPACE_REQUIRED', 'Host tool workspace input must be an absolute physical path');
  requireValue(typeof context?.workspace === 'string' && isAbsolute(context.workspace), 'HOST_TOOL_WORKSPACE_REQUIRED', 'Host tool requires its exact Run/node workspace context');
  const root=async path=>{const absolute=resolve(path),entry=await lstat(absolute);requireValue(entry.isDirectory()&&!entry.isSymbolicLink(),'HOST_TOOL_WORKSPACE_SYMLINK','Declared host-tool workspace must be a real directory, not a link');return realpath(absolute);};
  let declared; let authorized;
  try { [declared, authorized] = await Promise.all([root(input.workspace), root(context.workspace)]); }
  catch (error) { throw Object.assign(new Error(`Host tool workspace contains a symlink/reparse escape: ${error.message}`), { code: 'HOST_TOOL_WORKSPACE_SYMLINK' }); }
  requireValue(declared === authorized, 'HOST_TOOL_WORKSPACE_MISMATCH', 'Declared host-tool workspace differs from the exact Run/node-authorized workspace');
}
function qualifiedBroker(registered, pinned) {
  requireValue(registered && typeof registered.execute === 'function' && typeof registered.cancel === 'function' && canonicalJSON(registered.identity) === canonicalJSON(pinned.identity), 'HOST_TOOL_UNAVAILABLE', 'No exact registered host implementation matches the pinned tool identity');
  const attestation = registered.attestation;
  requireValue(object(attestation) && attestation.qualified === true && attestation.cancellable === true && attestation.effect_observation === true && canonicalJSON(attestation.tool_identity) === canonicalJSON(pinned.identity) && typeof attestation.broker_id === 'string' && attestation.broker_id.length > 0 && /^[a-f0-9]{64}$/.test(attestation.evidence_sha256), 'HOST_TOOL_BROKER_UNQUALIFIED', 'Host tool requires an exact qualified cancellable/effect-observing broker attestation');
  return attestation;
}
function reconciliation(raw, status) {
  requireValue(object(raw) && raw.termination_confirmed === true && Array.isArray(raw.evidence) && raw.evidence.length > 0 && raw.evidence.length <= 32 && raw.evidence.every(item => object(item) && typeof item.kind === 'string' && /^[a-f0-9]{64}$/.test(item.sha256) && Object.keys(item).every(key => ['kind', 'sha256'].includes(key))), 'HOST_TOOL_CANCELLATION_UNCONFIRMED', 'Timeout/cancellation requires broker-confirmed termination evidence');
  return { status, termination_confirmed: true, evidence: structuredClone(raw.evidence), effects: raw.effects };
}

export function validateHostToolContract(contract) {
  requireValue(object(contract) && Object.keys(contract).every(key => ['id', 'identity', 'argv', 'input_schema', 'output_schema', 'env_allow', 'permissions', 'output_cap_bytes', 'deadline_ms', 'idempotency', 'implements', 'host_owned_item_fields'].includes(key)), 'HOST_TOOL_CONTRACT', 'Host tool contract has unsupported fields');
  requireValue(typeof contract.id === 'string' && /^[a-z][a-z0-9_-]{0,127}$/.test(contract.id), 'HOST_TOOL_CONTRACT', 'Host tool needs a stable lowercase ID');
  requireValue(object(contract.identity) && typeof contract.identity.name === 'string' && contract.identity.name.length > 0 && contract.identity.name.length <= 256 && typeof contract.identity.version === 'string' && contract.identity.version.length > 0 && contract.identity.version.length <= 128 && /^[a-f0-9]{64}$/.test(contract.identity.sha256) && Object.keys(contract.identity).every(key => ['name', 'version', 'sha256'].includes(key)), 'HOST_TOOL_CONTRACT', 'Host tool needs an exact name/version/content identity');
  const argv = stringArray(contract.argv, 'argv', 32); requireValue(!argv.some(item => /[\x00-\x1f]/.test(item)), 'HOST_TOOL_CONTRACT', 'Host argv cannot include control characters');
  validateDataSchema(contract.input_schema ?? {}); validateDataSchema(contract.output_schema ?? {});
  const env_allow = stringArray(contract.env_allow, 'env_allow'); requireValue(env_allow.every(name => /^[A-Z_][A-Z0-9_]{0,127}$/.test(name)), 'HOST_TOOL_CONTRACT', 'Host environment allowlist contains an invalid variable');
  requireValue(object(contract.permissions) && typeof contract.permissions.network === 'boolean' && Object.keys(contract.permissions).every(key => ['network', 'read_paths', 'write_paths'].includes(key)), 'HOST_TOOL_CONTRACT', 'Host tool permissions need an explicit network/read/write contract');
  const scratch = resourceProgramScratch({...contract,argv});
  const permissions = { network: contract.permissions.network, read_paths: pathBoundaries(stringArray(contract.permissions.read_paths, 'read_paths')),
    write_paths: pathBoundaries(stringArray(contract.permissions.write_paths, 'write_paths')).filter(path=>path!==scratch) };
  requireValue(Number.isInteger(contract.output_cap_bytes) && contract.output_cap_bytes > 0 && contract.output_cap_bytes <= MAX_OUTPUT, 'HOST_TOOL_CONTRACT', 'Host output cap must be a bounded positive byte count');
  requireValue(Number.isInteger(contract.deadline_ms) && contract.deadline_ms > 0 && contract.deadline_ms <= 300000, 'HOST_TOOL_CONTRACT', 'Host deadline must be between 1ms and 5 minutes');
  requireValue(object(contract.idempotency) && ['safe', 'reconcile_required', 'non_idempotent'].includes(contract.idempotency.mode) && Object.keys(contract.idempotency).length === 1, 'HOST_TOOL_CONTRACT', 'Host tool must declare one retry/idempotency mode');
  const implementsRequirements=contract.implements === undefined ? [] : stringArray(contract.implements,'implements',256);
  requireValue(implementsRequirements.every(id=>/^[a-zA-Z][a-zA-Z0-9_-]{0,127}$/.test(id)),'HOST_TOOL_CONTRACT','Host tool implemented requirement IDs must be stable identifiers');
  const hostOwnedItemFields=contract.host_owned_item_fields===undefined?[]:contract.host_owned_item_fields;
  requireValue(Array.isArray(hostOwnedItemFields)&&hostOwnedItemFields.length<=64,'HOST_TOOL_CONTRACT','Host-owned item fields need a bounded declaration list');
  const seenHostOutputs=new Set();
  const normalizedHostOwnedItemFields=hostOwnedItemFields.map(entry=>{
    requireValue(object(entry)&&Object.keys(entry).every(key=>['output','fields','from_inputs'].includes(key))&&typeof entry.output==='string'&&/^[A-Za-z][A-Za-z0-9_-]{0,127}$/.test(entry.output)&&!seenHostOutputs.has(entry.output),'HOST_TOOL_CONTRACT','Host-owned item fields need one unique output name');
    seenHostOutputs.add(entry.output);
    const fields=stringArray(entry.fields,'host_owned_item_fields.fields',128),fromInputs=stringArray(entry.from_inputs,'host_owned_item_fields.from_inputs',128);
    requireValue(fields.length>0&&fromInputs.length>0&&fields.every(name=>/^[A-Za-z][A-Za-z0-9_-]{0,127}$/.test(name))&&fromInputs.every(name=>/^[A-Za-z][A-Za-z0-9_-]{0,127}$/.test(name)),'HOST_TOOL_CONTRACT','Host-owned item provenance needs portable nonempty field and input names');
    const output=contract.output_schema?.properties?.[entry.output],item=output?.items,inputProperties=contract.input_schema?.properties??{},requiredInputs=new Set(contract.input_schema?.required??[]),requiredFields=new Set(item?.required??[]);
    requireValue(output?.type==='array'&&item?.type==='object'&&fields.every(name=>Object.hasOwn(item.properties??{},name)&&requiredFields.has(name)),'HOST_TOOL_CONTRACT','Host-owned item fields must be required fields on the declared output item schema');
    requireValue(fromInputs.every(name=>Object.hasOwn(inputProperties,name)&&requiredInputs.has(name)),'HOST_TOOL_CONTRACT','Host-owned item provenance inputs must be required Host-tool inputs');
    return {output:entry.output,fields,from_inputs:fromInputs};
  });
  return { id: contract.id, identity: structuredClone(contract.identity), argv, input_schema: structuredClone(contract.input_schema ?? {}), output_schema: structuredClone(contract.output_schema ?? {}), env_allow, permissions, output_cap_bytes: contract.output_cap_bytes, deadline_ms: contract.deadline_ms, idempotency: structuredClone(contract.idempotency), ...(implementsRequirements.length?{implements:implementsRequirements}:{}), ...(normalizedHostOwnedItemFields.length?{host_owned_item_fields:normalizedHostOwnedItemFields}:{}) };
}
export function hostToolContracts(workflow) {
  requireValue(workflow.host_tools === undefined || Array.isArray(workflow.host_tools), 'HOST_TOOL_CONTRACT', 'Workflow host tools must be an array'); const contracts = new Map();
  for (const raw of workflow.host_tools ?? []) { const contract = validateHostToolContract(raw); requireValue(!contracts.has(contract.id), 'HOST_TOOL_CONTRACT', 'Workflow cannot register a host tool twice'); contracts.set(contract.id, contract); }
  return contracts;
}
function registryEntry(registry, id, identity) {
  return registry instanceof Map ? registry.get(id) ?? registry.get(identity?.name)
    : registry?.[id] ?? registry?.[identity?.name];
}

export function hostToolBindingIssues(workflow, registry = {}) {
  const issues = [];
  for (const raw of workflow?.host_tools ?? []) {
    let contract;
    try { contract = validateHostToolContract(raw); }
    catch (error) {
      issues.push({ code: error.code ?? 'HOST_TOOL_CONTRACT', message: error.message, host_tool_id: raw?.id ?? null });
      continue;
    }
    try { qualifiedBroker(registryEntry(registry, contract.id, contract.identity), contract); }
    catch (error) {
      issues.push({ code: error.code ?? 'HOST_TOOL_UNAVAILABLE', message: error.message, host_tool_id: contract.id,
        pinned_identity: structuredClone(contract.identity) });
    }
  }
  return issues;
}

export function requireHostToolBindings(workflow, registry = {}) {
  const issues = hostToolBindingIssues(workflow, registry);
  requireValue(issues.length === 0, 'HOST_TOOL_BINDING_STALE', 'Workflow host-tool bindings do not match the registered qualified implementations', { issues });
}

/** A qualified broker receives AbortSignal and must attest effects/cancellation. */
export class HostToolRunner {
  constructor({ registry = {}, env = process.env, now = () => Date.now() } = {}) { this.registry = registry; this.env = env; this.now = now; }
  async execute(contract, input, context, { signal, assertActive } = {}) {
      const pinned = validateHostToolContract(contract); validateData(input, pinned.input_schema); requireValue(Buffer.byteLength(canonicalJSON(input)) <= MAX_INPUT, 'HOST_TOOL_INPUT_LIMIT', 'Host input exceeds the bounded durable receipt limit'); noCredential(input); await declaredWorkspace(input, context); const registered = registryEntry(this.registry, pinned.id, pinned.identity); const attestation = qualifiedBroker(registered, pinned); const permissions = effectivePermissions(pinned, context);
    const env = Object.fromEntries(pinned.env_allow.filter(key => Object.hasOwn(this.env, key)).map(key => [key, this.env[key]])); const started = this.now(); const started_at = new Date(started).toISOString(); const controller = new AbortController(); let timer; let abortListener;
    const inputSha = digest(canonicalJSON(input)); const base = { run_id: context.run_id, node_id: context.node_id, attempt_id: context.attempt_id, tool: pinned.id, contract_sha256: digest(canonicalJSON(pinned)), input_sha256: inputSha, broker: { id: attestation.broker_id, evidence_sha256: attestation.evidence_sha256 }, started_at };
    const brokerContext = {
      run_id: context.run_id,
      node_id: context.node_id,
      attempt_id: context.attempt_id,
      workspace: context.workspace,
      resources: context.resources,
      task_root: context.task_root,
      ...(context.prepareRuntimeEnvironment ? {prepareRuntimeEnvironment:context.prepareRuntimeEnvironment} : {}),
      ...(context.runtime_environment ? { runtime_environment: structuredClone(context.runtime_environment) } : {}),
      ...(context.execution_binding ? { execution_binding: structuredClone(context.execution_binding) } : {}),
    };
    const stop = async (status, reason) => {
      controller.abort(reason); const cancelled = await registered.cancel({ context: { run_id: context.run_id, node_id: context.node_id, attempt_id: context.attempt_id }, reason, signal: controller.signal }); const recon = reconciliation(cancelled, status); const effects = boundedEffects(recon.effects, permissions); const finished = this.now(); const message = safeDiagnostic(reason?.message ?? reason);
      return { receipt: { ...base, output_sha256: null, output_ref: null, diagnostics: { message, sha256: digest(message) }, status, exit_code: null, finished_at: new Date(finished).toISOString(), duration_ms: finished - started, effects, reconciliation: { status: recon.status, termination_confirmed: true, evidence: recon.evidence } }, output: null };
    };
    const admitted = () => {
      try { assertActive?.(); } catch (error) { controller.abort(error); }
      return !signal?.aborted && !controller.signal.aborted;
    };
    try {
      if (!admitted()) return await stop('cancelled', signal?.reason ?? controller.signal.reason ?? new Error('Host tool cancelled'));
      // The final admission check and broker invocation share one synchronous
      // microtask. A signal revoked before that microtask cannot enqueue work.
      const operation = Promise.resolve().then(() => admitted()
        ? registered.execute({ input: structuredClone(input), argv: [...pinned.argv], env, permissions: structuredClone(permissions), context: brokerContext, signal: controller.signal })
        : { cancelledBeforeStart: true });
      operation.catch(() => undefined);
      const outcome = await Promise.race([
        operation.then(response => ({ kind: 'response', response })),
        new Promise(resolve => { timer = setTimeout(() => resolve({ kind: 'timeout' }), pinned.deadline_ms); }),
        ...(signal ? [new Promise(resolve => { abortListener = () => resolve({ kind: 'cancelled', reason: signal.reason }); signal.addEventListener('abort', abortListener, { once: true }); })] : []),
      ]);
      if (outcome.kind === 'timeout') return await stop('timed_out', Object.assign(new Error('Host tool deadline elapsed'), { code: 'HOST_TOOL_TIMEOUT' }));
      if (outcome.kind === 'cancelled') return await stop('cancelled', outcome.reason ?? new Error('Host tool cancelled'));
      const response = outcome.response;
      if (response?.cancelledBeforeStart) return await stop('cancelled', signal?.reason ?? controller.signal.reason ?? new Error('Host tool cancelled'));
      requireValue(object(response) && Object.keys(response).every(key => ['exit_code', 'output', 'diagnostic', 'effects'].includes(key)), 'HOST_TOOL_RESULT', 'Host tool returned unsupported fields'); requireValue(Number.isInteger(response.exit_code), 'HOST_TOOL_RESULT', 'Host tool result needs an integer exit code');
      const effects = boundedEffects(response.effects, permissions); const diagnostic = safeDiagnostic(response.diagnostic); const succeeded = response.exit_code === 0;
      if (succeeded) { validateData(response.output, pinned.output_schema); requireValue(Buffer.byteLength(canonicalJSON(response.output)) <= pinned.output_cap_bytes, 'HOST_TOOL_OUTPUT_LIMIT', 'Host structured output exceeds the pinned cap'); noCredential(response.output); }
      const finished = this.now(); return { receipt: { ...base, output_sha256: succeeded ? digest(canonicalJSON(response.output)) : null, output_ref: null, diagnostics: { message: diagnostic, sha256: digest(diagnostic) }, status: succeeded ? 'succeeded' : 'failed', exit_code: response.exit_code, finished_at: new Date(finished).toISOString(), duration_ms: finished - started, effects, reconciliation: null }, output: succeeded ? structuredClone(response.output) : null };
    } finally { if (timer) clearTimeout(timer); if (signal && abortListener) signal.removeEventListener('abort', abortListener); }
  }
}
export function validateHostToolReceipt(receipt) {
  const fields = ['run_id', 'node_id', 'attempt_id', 'tool', 'contract_sha256', 'input_sha256', 'broker', 'started_at', 'finished_at', 'duration_ms', 'output_sha256', 'output_ref', 'diagnostics', 'status', 'exit_code', 'effects', 'reconciliation'];
  requireValue(object(receipt) && Object.keys(receipt).every(key => fields.includes(key)) && statusValues.has(receipt.status) && typeof receipt.run_id === 'string' && typeof receipt.node_id === 'string' && typeof receipt.attempt_id === 'string' && typeof receipt.tool === 'string' && /^[a-f0-9]{64}$/.test(receipt.contract_sha256) && /^[a-f0-9]{64}$/.test(receipt.input_sha256) && object(receipt.broker) && typeof receipt.broker.id === 'string' && /^[a-f0-9]{64}$/.test(receipt.broker.evidence_sha256) && typeof receipt.started_at === 'string' && typeof receipt.finished_at === 'string' && (receipt.output_sha256 === null || /^[a-f0-9]{64}$/.test(receipt.output_sha256)) && (receipt.output_ref === null || object(receipt.output_ref) && typeof receipt.output_ref.artifact === 'string' && /^[a-f0-9]{64}$/.test(receipt.output_ref.sha256) && Number.isSafeInteger(receipt.output_ref.bytes) && receipt.output_ref.bytes >= 0) && object(receipt.diagnostics) && typeof receipt.diagnostics.message === 'string' && /^[a-f0-9]{64}$/.test(receipt.diagnostics.sha256) && object(receipt.effects) && receipt.effects.observed === true && Array.isArray(receipt.effects.changed_paths) && Array.isArray(receipt.effects.outside_paths) && Array.isArray(receipt.effects.artifacts) && (receipt.reconciliation === null || object(receipt.reconciliation) && receipt.reconciliation.termination_confirmed === true && Array.isArray(receipt.reconciliation.evidence)) && (receipt.exit_code === null || Number.isInteger(receipt.exit_code)) && Number.isFinite(receipt.duration_ms) && receipt.duration_ms >= 0, 'HOST_TOOL_RECEIPT', 'Host receipt is incomplete or malformed');
  requireValue(digest(receipt.diagnostics.message) === receipt.diagnostics.sha256, 'HOST_TOOL_RECEIPT', 'Host receipt diagnostic hash differs from its bounded diagnostic');
  requireValue(receipt.status !== 'succeeded' || receipt.exit_code === 0, 'HOST_TOOL_RECEIPT', 'A successful host receipt must attest exit code zero');
  requireValue(receipt.status !== 'failed' || Number.isInteger(receipt.exit_code) && receipt.exit_code !== 0, 'HOST_TOOL_RECEIPT', 'A failed host receipt must attest a nonzero exit code');
  requireValue(!['timed_out', 'cancelled'].includes(receipt.status) || receipt.exit_code === null, 'HOST_TOOL_RECEIPT', 'A stopped host receipt cannot report a process exit code');
  noCredential(receipt, 'HOST_TOOL_SECRET');
  requireValue(receipt.status !== 'succeeded' || receipt.output_ref && receipt.output_sha256, 'HOST_TOOL_RECEIPT', 'Successful host receipt needs one durable output reference');
  requireValue(!['timed_out', 'cancelled'].includes(receipt.status) || receipt.reconciliation?.termination_confirmed === true, 'HOST_TOOL_RECEIPT', 'Timeout/cancellation receipt needs confirmed termination evidence'); return receipt;
}
