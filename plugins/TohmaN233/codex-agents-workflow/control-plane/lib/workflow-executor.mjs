import { buildCodexThreadAdapter, buildProviderAdapter, invokeOpenAICompatible } from './providers.mjs';
import { renderTemplate } from './templates.mjs';
import { requireValue } from './workflow-paths.mjs';
import { canonicalJSON, digest } from './workflow-revisions.mjs';
import { isEnvironmentDisabled } from './config.mjs';
import { controllerAttempt, reattachAttempt } from './workflow-recovery.mjs';
import { leaseToken, nodePermissions } from './workflow-execution-envelope.mjs';
import { threadHandoff } from './thread-handoff.mjs';
import { HostToolRunner, hostToolContracts } from './execution/host-tool-runner.mjs';
import { AttemptAdmissionRegistry } from './execution/attempt-admission.mjs';
import { confirmConnectorExecutionQuiescent } from '../connectors/registry.mjs';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

function promptInputs(inputs) {
  const displayed=structuredClone(inputs ?? {});
  for(const [name,value] of Object.entries(displayed)) if(name.endsWith('_json') && typeof value==='string') {
    try { displayed[name]=JSON.parse(value); } catch { /* invalid JSON remains visible as its exact string */ }
  }
  return displayed;
}

export function compilePrompt(envelope, max) {
  const input = envelope.inputs ?? {};
  const template = envelope.prompt_template ?? '';
  const nodePrompt = renderTemplate(template, {
    task: typeof input === 'string' ? input : input?.task,
    context: input?.context, constraints: envelope.constraints, verification: input?.verification,
    task_type_id: envelope.workflow_id, stage_id: envelope.node_id, provider_name: envelope.provider?.name ?? 'Main agent',
  }, max);
  // A bound value already expanded in the instruction template is not another
  // model input. Keep every unexpanded binding, including empty values, exact.
  const prompt=nodePrompt;
  const displayed = promptInputs(envelope.inputs);
  const expanded = ['task', 'context', 'verification'].filter(name =>
    Object.hasOwn(displayed, name) && input?.[name] !== undefined && input?.[name] !== null && input?.[name] !== ''
    && new RegExp('\\{\\{\\s*' + name + '\\s*\\}\\}').test(template));
  for (const name of expanded) delete displayed[name];
  const extra = '\n\nNode ' + envelope.node_id + ' only. The bound task may describe downstream work; return this node\'s declared output.'
    + (expanded.length ? '\nInputs already expanded in the instruction template: ' + expanded.join(', ') + '.' : '')
    + (Object.keys(displayed).length ? '\nInputs:\n' + canonicalJSON(displayed) : '')
    + (envelope.context_projection?.references?.length ? '\nResources:\n' + canonicalJSON(envelope.context_projection.references) : '')
    + (envelope.completion_contract ? '\nCompletion:\n' + canonicalJSON(envelope.completion_contract) : '');
  requireValue(prompt.length + extra.length <= max, 'PROMPT_LIMIT', 'Node context exceeds the configured prompt limit');
  return prompt + extra;
}
const receiptIdentity = task => ({ task_id: task.task_id, connector: task.connector, ...(task.remote_identity ? { remote_identity: task.remote_identity } : {}) });
// Recovery adds observation metadata without changing the remote task identity.
// Preserve stored receipts; ignore only this documented mutable annotation when
// comparing, while retaining every session/run/agent/transport identity field.
function comparableReceipt(receipt) {
  const result = structuredClone(receipt);
  if (result?.remote_identity) delete result.remote_identity.recovered_attachment;
  return canonicalJSON(result);
}
const sameReceipt = (left, right) => comparableReceipt(left) === comparableReceipt(right);
function normalizedUsage(raw) {
  const usage = raw && typeof raw === 'object' ? raw : null;
  if (!usage) return { unknown: true };
  const field = (...names) => names.map(name => usage[name]).find(Number.isSafeInteger);
  const cost = field('cost_micros');
  return { unknown: !Number.isSafeInteger(cost), ...(Number.isSafeInteger(field('input_tokens', 'prompt_tokens')) ? { input_tokens: field('input_tokens', 'prompt_tokens') } : {}), ...(Number.isSafeInteger(field('output_tokens', 'completion_tokens')) ? { output_tokens: field('output_tokens', 'completion_tokens') } : {}), ...(Number.isSafeInteger(field('cached_input_tokens', 'cached_tokens')) ? { cached_input_tokens: field('cached_input_tokens', 'cached_tokens') } : {}), ...(Number.isSafeInteger(field('cache_write_input_tokens')) ? { cache_write_input_tokens: field('cache_write_input_tokens') } : {}), ...(Number.isSafeInteger(field('reasoning_output_tokens')) ? { reasoning_output_tokens: field('reasoning_output_tokens') } : {}), ...(Number.isSafeInteger(field('visual_input_units', 'image_tokens')) ? { visual_input_units: field('visual_input_units', 'image_tokens') } : {}), ...(Number.isSafeInteger(cost) ? { cost_micros: cost } : {}) };
}
const TERMINAL_CONNECTOR_STATES = new Set(['completed', 'failed', 'cancelled', 'scope_violation', 'abandoned']);

function hostNativeExecutionOwner(args, receipt) {
  if (args.host_managed_native !== true) return null;
  if (receipt?.executor === 'codex-app-server-managed-native') return 'managed_native_codex';
  if (receipt?.executor === 'codex-app-server') return 'strict_codex';
  requireValue(false, 'MANAGED_NATIVE_RECEIPT', 'The existing native dispatch receipt has no supported Host execution owner');
}

export class WorkflowExecutor {
  constructor({ runtime, getConfig, registry, strictManager, managedNativeManager, hostToolRunner, attemptAdmission, env = process.env, fetchImpl = globalThis.fetch }) {
    this.runtime = runtime; this.getConfig = getConfig; this.registry = registry; this.env = env; this.fetchImpl = fetchImpl;
    this.strictManager = strictManager; this.managedNativeManager = managedNativeManager; this.hostToolRunner = hostToolRunner ?? new HostToolRunner({ env });
    this.attemptAdmission = attemptAdmission ?? new AttemptAdmissionRegistry();
    this.hostExecutions = this.attemptAdmission.entries;
  }

  // A terminal connector observation is the final chance to close the exact
  // paid-call reservation.  Do this before changing Run/node state so a crash
  // cannot leave a known terminal remote task looking in-flight forever.
  async recordConnectorTerminalUsage(runId, args, attempt, task) {
    if (!TERMINAL_CONNECTOR_STATES.has(task?.state)) return false;
    requireValue(attempt?.dispatch?.request_id, 'DISPATCH_INTENT_MISSING', 'Terminal connector usage needs its exact dispatch request');
    const lease_token = args.lease_token ?? leaseToken(args.control_token, runId, args.node_id, args.attempt_id, attempt.lease_generation ?? 0);
    await this.runtime.recordUsage(runId, { ...args, run_id: runId, lease_token, request_id: attempt.dispatch.request_id, usage: normalizedUsage(task.usage) });
    return true;
  }

  async cancelPendingHostTools(runId, controlToken) {
    await this.runtime.authorizeController(runId, { control_token: controlToken });
    this.attemptAdmission.fenceRun(runId);
    try {
      const entries = await this.attemptAdmission.wait(runId, 'host_tool');
      return { cancelled_attempts: entries.map(entry => ({ node_id: entry.node_id, attempt_id: entry.attempt_id })) };
    } catch (error) { throw Object.assign(error, { code: 'HOST_TOOL_CANCEL_INCOMPLETE' }); }
  }

  async executeHostTool(runId, args, { assertActive = () => {} } = {}) {
    // Own the attempt before the first await. Cancellation can otherwise miss
    // an operation paused in Run/pin I/O and let it start after the scan.
    const activeHost = this.attemptAdmission.begin(runId, args.node_id, args.attempt_id, 'host_tool');
    activeHost.intent_pending = false;
    activeHost.receipt_recorded = false;
    const { controller } = activeHost;
    const assertAdmission = () => {
      activeHost.assertActive();
      assertActive();
    };
    let activeError = null;
    try {
      assertAdmission();
      const envelope = await this.runtime.execution(runId, args);
      assertAdmission();
      requireValue(envelope.executor.kind === 'tool', 'HOST_TOOL_NODE', 'This node is not a host-tool node');
      const record = await this.runtime.runs.read(runId);
      assertAdmission();
      const attempt = record.state.nodes[args.node_id]?.attempts.find(item => item.id === args.attempt_id);
      requireValue(attempt, 'HOST_TOOL_NODE', 'Host tool attempt is missing');
      const contract = hostToolContracts(record.pins.root.workflow).get(envelope.executor.tool);
      requireValue(contract, 'HOST_TOOL_CONTRACT', 'Tool node has no pinned host contract');
      const definition=record.pins.root.workflow.nodes.find(node=>node.id===args.node_id);
      const resources=await Promise.all((definition?.resources??[]).map(async path=>{
        const pin=record.pins.root.resources.find(item=>item.path===path);
        requireValue(pin,'WORKFLOW_RESOURCE_PIN',`Host tool resource is absent from the Run pin: ${path}`);
        const bytes=await readFile(join(this.runtime.runs.directory(runId),'objects',pin.sha256));
        requireValue(digest(bytes)===pin.sha256,'WORKFLOW_RESOURCE_PIN',`Host tool resource differs from its Run pin: ${path}`);
        return {path,sha256:pin.sha256,bytes};
      }));
      let receipt = attempt.host_tool?.receipt ?? null; let output = null;
      if (!receipt) {
        const preparedEnvironment = await this.runtime.ensureRuntimeEnvironment(runId, {control_token:args.control_token});
        if (attempt.host_tool) requireValue(attempt.host_tool.idempotency === 'safe', 'HOST_TOOL_RECONCILIATION_REQUIRED', 'Host tool has an uncertain intent and is not declared safe to replay');
        assertAdmission();
        activeHost.intent_pending = true;
        try { await this.runtime.recordHostToolIntent(runId, { ...args, contract, input: envelope.inputs }); }
        catch (error) {
          // These transition errors prove the intent was rejected before any
          // broker ownership existed; an I/O failure remains uncertain.
          if (['STALE_LEASE', 'RUN_NOT_RUNNING', 'PARENT_RUN_INACTIVE', 'PARENT_LEASE_INACTIVE'].includes(error.code)) activeHost.intent_pending = false;
          throw error;
        }
        // Once intent is durable, a revoked attempt still needs a qualified
        // cancellation receipt. The runner must not invoke the broker's work.
        const fence = () => { try { assertActive(); } catch (error) { controller.abort(error); } };
        const executed = await this.hostToolRunner.execute(contract, envelope.inputs, {
          run_id: runId,
          node_id: args.node_id,
          attempt_id: args.attempt_id,
          workspace: envelope.workspace,
          resources,
          task_root: record.state.constraints?.task_workspace ?? envelope.workspace,
          permissions: { access: envelope.access, allowed_paths: envelope.effective_allowed_paths },
          runtime_environment: structuredClone(preparedEnvironment.environment),
          prepareRuntimeEnvironment: () => this.runtime.ensureRuntimeEnvironment(runId, {control_token:args.control_token}),
          execution_binding: structuredClone(record.state.constraints?.execution_binding ?? null),
        }, { signal: controller.signal, assertActive: fence });
        receipt = executed.receipt; output = executed.output;
        if (receipt.status === 'succeeded') {
          requireValue(output !== null && digest(canonicalJSON(output)) === receipt.output_sha256, 'HOST_TOOL_OUTPUT_CORRUPT', 'Qualified broker output differs from its attested digest');
          const stored = await this.runtime.runs.saveExecutorResult(runId, args.attempt_id, { kind: 'host_tool_output', output });
          receipt = { ...receipt, output_ref: { ...stored, bytes: Buffer.byteLength(canonicalJSON({ kind: 'host_tool_output', output })) } };
        }
        await this.runtime.recordHostToolReceipt(runId, { ...args, receipt });
        activeHost.receipt_recorded = true;
      }
      if (receipt.status !== 'succeeded') {
        const cancelled = await this.runtime.get(runId); const current = cancelled.nodes[args.node_id]?.attempts.find(item => item.id === args.attempt_id);
        if (cancelled.status === 'cancelled' || current?.status === 'cancelled') return cancelled;
        return this.runtime.failNode(runId, { ...args, error: { code: receipt.status === 'timed_out' ? 'HOST_TOOL_TIMEOUT' : receipt.status === 'cancelled' ? 'HOST_TOOL_CANCELLED' : 'HOST_TOOL_FAILED', message: receipt.diagnostics.message || `Host tool ${receipt.tool} exited ${receipt.exit_code}` } });
      }
      if (output === null) {
        const stored = await this.runtime.runs.readExecutorResult(runId, args.attempt_id, receipt.output_ref.sha256);
        requireValue(stored?.kind === 'host_tool_output' && digest(canonicalJSON(stored.output)) === receipt.output_sha256, 'HOST_TOOL_OUTPUT_CORRUPT', 'Durable host output differs from its receipt'); output = stored.output;
      }
      const cancelled = await this.runtime.get(runId); const current = cancelled.nodes[args.node_id]?.attempts.find(item => item.id === args.attempt_id);
      if (cancelled.status === 'cancelled' || current?.status === 'cancelled') return cancelled;
      return this.runtime.completeNode(runId, { ...args, completion: { status: 'succeeded', summary: `Host tool ${receipt.tool} completed`, structured_output: output,
        artifacts: receipt.effects.artifacts, evidence: [{ kind: 'host_tool_receipt', receipt }], changed_paths: receipt.effects.changed_paths, outside_paths: receipt.effects.outside_paths } });
    } catch (error) { activeError = error; throw error; }
    finally { activeHost.settle(activeError && activeHost.intent_pending && !activeHost.receipt_recorded ? { error: activeError } : {}); }
  }

  async externalCall(runId, _args, envelope, request, call, { cancellationKind = null, signal = null } = {}) {
    try { return await call(); }
    catch (cause) {
      if (cancellationKind === 'connector' && signal?.aborted && cause.cancellation_confirmed === true) throw cause;
      if (cancellationKind === 'direct_api' && signal?.aborted && ['ATTEMPT_STOPPED', 'DIRECT_API_CANCELLED'].includes(cause.code)) {
        // A rejected AbortSignal confirms local HTTP/body settlement. An
        // already-submitted request may still be charged; journal unknown use.
        if (cause.code === 'DIRECT_API_CANCELLED') await this.runtime.recordUsage(runId, { ...request, usage: { unknown: true } });
        throw Object.assign(cause, { cancellation_confirmed: true });
      }
      let message = String(cause.message ?? cause);
      const secret = this.env[envelope.provider?.config?.api_key_env];
      if (secret) message = message.split(secret).join('[redacted]');
      message = message.replace(/\bBearer\s+[^\s]+/gi, 'Bearer [redacted]').replace(/((?:api[-_]?key|token|secret|password)\s*[:=]\s*)[^\s]+/gi, '$1[redacted]').slice(-2000);
      const error = Object.assign(new Error(message), { code: 'DISPATCH_UNCERTAIN', cause });
      try {
        // An attempted paid call can have been charged even if its transport
        // failed. Record usage now; the graph failure is committed only after
        // the dispatch owner has settled and exact cleanup is confirmed.
        await this.runtime.recordUsage(runId, { ...request, usage: { unknown: true } });
        // A connector start error may be a lost receipt after remote submit.
        // Its exact task must be reconciled, never failed from a transport
        // exception. A settled direct-API transport has no retained local
        // connector owner and can commit its advisory failure after settlement.
        if (cancellationKind === 'direct_api') error.failureCommit = { code: error.code, message };
      }
      catch (auditError) { throw Object.assign(new AggregateError([error, auditError], 'External dispatch failed and its usage could not be committed; inspect the existing intent before any retry'), { code: 'DISPATCH_AUDIT_FAILED' }); }
      throw error;
    }
  }

  async prepare(runId, args) {
    const envelope = await this.runtime.execution(runId, args);
    const config = await this.getConfig();
    requireValue(config.global.enabled && !isEnvironmentDisabled(this.env), 'CONTROL_DISABLED', 'Workflow execution is disabled');
    if (envelope.provider) {
      const current = config.providers.find(provider => provider.id === envelope.provider.id);
      requireValue(current?.enabled, 'PROVIDER_DISABLED', 'Pinned Provider was removed or disabled');
      requireValue(current.capabilities.read && (envelope.access === 'read_only' || current.capabilities.write), 'PROVIDER_CAPABILITY', 'Pinned Provider capability was revoked');
      requireValue(!current.requires_user_approval || envelope.provider.requires_user_approval, 'PROVIDER_POLICY_CHANGED', 'Provider now requires an approval absent from this pinned revision; start a new Run');
    }
    // Logical Main is executed by the Host Main manager in its own compact
    // App Server lane. It is neither a Provider nor the foreground Codex task.
    // This branch must precede Strict dispatch so Main never falls back to the
    // ordinary full-context session manager.
    if (envelope.executor.kind === 'main' && args.host_managed_main === true) {
      return { envelope, adapter: { execution: envelope.executor.mode === 'orchestration' ? 'current_main_orchestration' : 'host_isolated_main', read_only: envelope.access === 'read_only' }, prompt: compilePrompt(envelope, config.global.max_prompt_chars) };
    }
    if (envelope.skill_policy.mode === 'strict') {
      requireValue(this.strictManager, 'STRICT_EXECUTOR_REQUIRED', 'This host has no qualified Strict session manager');
      const adapter = await this.strictManager.prepare(this.runtime, runId, args, envelope);
      return { envelope, adapter, prompt: compilePrompt(envelope, config.global.max_prompt_chars) };
    }
    requireValue(envelope.executor.kind !== 'main','HOST_MAIN_BRIDGE_REQUIRED','Logical Main dispatch requires the Host-isolated Main lane');
    let adapter = envelope.executor.kind === 'provider' ? buildProviderAdapter(envelope.provider, { access: envelope.access }, { env: this.env, allowDirectApi: config.global.allow_direct_api })
      : envelope.executor.kind === 'thread' ? buildCodexThreadAdapter(envelope.provider, envelope, { env: this.env, allowDirectApi: config.global.allow_direct_api })
      : { execution: 'host_tool', tool: envelope.executor.tool ?? null, read_only: envelope.access === 'read_only' };
    if(adapter.execution==='native_agent' && args.host_managed_native===true){
      requireValue(this.managedNativeManager,'MANAGED_NATIVE_REQUIRED','Host-owned native dispatch requires its session manager');
      adapter=await this.managedNativeManager.prepare(this.runtime,runId,args,envelope);
    }
    requireValue(envelope.skill_policy.mode === 'cooperative', 'STRICT_EXECUTOR_REQUIRED', 'This adapter cannot run Strict nodes');
    if (adapter.execution === 'direct_api') requireValue(config.global.allow_direct_api && envelope.access === 'read_only' && adapter.credential_ready, 'DIRECT_API_DISABLED', 'Direct API requires enabled advisory access and available environment credentials');
    // A fan-out's complete input is a Host routing manifest, not one Agent's
    // context. Compile only after partition projection in nativeAgentHandoff.
    const prompt = ['native_agent','managed_native_codex'].includes(adapter.execution) && envelope.subagents?.fanout
      ? envelope.prompt_template ?? '' : compilePrompt(envelope, config.global.max_prompt_chars);
    const thread_resources = adapter.execution === 'codex_thread'
      ? await this.runtime.threadResourcePacket(runId, args, { max_chars: config.global.max_prompt_chars })
      : [];
    const prepared = { envelope, adapter, prompt };
    if (adapter.execution === 'codex_thread') prepared.thread_handoff = threadHandoff(adapter, envelope, prompt, { resources: thread_resources, max_chars: config.global.max_prompt_chars });
    return prepared;
  }

  async dispatch(runId, args) {
    const initial = await this.runtime.execution(runId, args, { allowInactive: true });
    if (initial.executor?.kind === 'tool') return this.executeHostTool(runId, args);
    const externalKind = initial.provider?.kind === 'builtin_connector' ? 'connector'
      : initial.provider?.kind === 'openai_compatible' ? 'direct_api' : null;
    let admission = null;
    if (externalKind) try { admission = this.attemptAdmission.begin(runId, args.node_id, args.attempt_id, externalKind); }
    catch (error) {
      if (error.code === 'ATTEMPT_DUPLICATE') throw Object.assign(new Error('Dispatch is already in flight for this exact attempt'), { code: 'DISPATCH_UNCERTAIN' });
      if (error.code === 'ATTEMPT_STOPPED') {
        const record = await this.runtime.runs.read(runId);
        const attempt = record.state.nodes[args.node_id]?.attempts.find(item => item.id === args.attempt_id);
        if (record.state.status === 'failed' && attempt?.dispatch && !attempt.dispatch.receipt)
          throw Object.assign(new Error('The exact external dispatch still requires reconciliation'), { code: 'DISPATCH_UNCERTAIN' });
      }
      throw error;
    }
    let dispatchError = null; let dispatched;
    try { dispatched = await this.dispatchPrepared(runId, args, initial, admission); }
    catch (error) {
      if (externalKind === 'direct_api' && admission?.controller.signal.aborted && error.code === 'ATTEMPT_STOPPED') error.cancellation_confirmed = true;
      dispatchError = error;
    }
    finally { admission?.settle(dispatchError && !dispatchError.cancellation_confirmed ? { error: dispatchError } : {}); }
    if (dispatchError?.failureCommit) {
      try {
        requireValue(this.coordinator, 'EXECUTION_COORDINATOR_REQUIRED', 'External failure requires exact cleanup coordination');
        await this.coordinator.failAttemptAfterQuiescence(runId, args, dispatchError.failureCommit);
      } catch (auditError) {
        throw Object.assign(new AggregateError([dispatchError, auditError], 'External dispatch failed and exact cleanup/failure could not be committed'), { code: 'DISPATCH_AUDIT_FAILED' });
      }
    }
    if (dispatchError) throw dispatchError;
    return dispatched;
  }

  async dispatchPrepared(runId, args, initial, admission) {
    admission?.assertActive();
    if (initial.subworkflow) {
      const config = await this.getConfig();
      admission?.assertActive();
      requireValue(config.global.enabled && !isEnvironmentDisabled(this.env), 'CONTROL_DISABLED', 'Workflow execution is disabled');
      await this.runtime.parallelManager?.ensureNode(this.runtime, runId, args);
      return this.runtime.startSubworkflow(runId, args);
    }
    const current = await this.runtime.get(runId);
    admission?.assertActive();
    const existing = current.nodes[args.node_id].attempts.find(item => item.id === args.attempt_id)?.dispatch;
    if (existing) {
      requireValue(existing.receipt, 'DISPATCH_UNCERTAIN', 'Dispatch already has a committed intent without a receipt; reconcile before retrying');
      return { dispatched: false, idempotent: true, receipt: existing.receipt,
        ...(args.host_managed_native === true ? {execution_owner:hostNativeExecutionOwner(args,existing.receipt)} : {}) };
    }
    // Reconstruct all policy and prompt data from the committed claim, never from
    // a caller-supplied Provider/envelope. Intent creation is the dispatch election.
    await this.runtime.parallelManager?.ensureNode(this.runtime, runId, args);
    admission?.assertActive();
    const prepared = await this.prepare(runId, args);
    admission?.assertActive();
    const requestId = `dispatch-${prepared.envelope.attempt_id}`;
    const request = { ...args, request_id: requestId, envelope_hash: digest(canonicalJSON(prepared)) };
    const intent = prepared.envelope.executor.kind==='main'
      ? await this.runtime.recordHostMainDispatchIntent(runId,request)
      : await this.runtime.recordDispatchIntent(runId, request);
    admission?.assertActive();
    if (intent.idempotent) {
      const receipt = intent.nodes[args.node_id].attempts.find(item => item.id === args.attempt_id).dispatch.receipt;
      requireValue(receipt, 'DISPATCH_UNCERTAIN', 'Dispatch already has a committed intent without a receipt; reconcile before retrying');
      return { dispatched: false, idempotent: true, receipt,
        ...(args.host_managed_native === true ? {execution_owner:hostNativeExecutionOwner(args,receipt)} : {}) };
    }
    const { envelope, adapter, prompt } = prepared;
    if (adapter.execution === 'strict_codex') return this.strictManager.launch(this.runtime, runId, args, prepared);
    if (adapter.execution === 'managed_native_codex') return this.managedNativeManager.launch(this.runtime,runId,args,prepared);
    if (adapter.execution === 'builtin_connector') {
      admission?.assertActive();
      const task = await this.externalCall(runId, args, envelope, request, () => this.registry.start({ provider: envelope.provider,
        stage: { id: envelope.node_id, read_only: envelope.access === 'read_only', requires_user_approval: envelope.provider.requires_user_approval },
        taskId: envelope.attempt_id, taskTypeId: envelope.workflow_id, stageId: envelope.node_id,
        prompt, workspace: envelope.workspace, allowedPaths: envelope.effective_allowed_paths, userApproved: true,
        assertActive: admission?.assertActive, signal: admission?.controller.signal, registerCleanup: admission?.registerCleanup,
      }), { cancellationKind: 'connector', signal: admission?.controller.signal });
      const receipt = receiptIdentity(task); await this.runtime.recordDispatchReceipt(runId, { ...request, receipt });
      const recorded = await this.runtime.runs.read(runId);
      const attempt = recorded.state.nodes[args.node_id]?.attempts.find(item => item.id === args.attempt_id);
      await this.recordConnectorTerminalUsage(runId, args, attempt, task);
      return { dispatched: true, receipt, task };
    }
    if (adapter.execution === 'direct_api') {
      admission?.assertActive();
      const response = await this.externalCall(runId, args, envelope, request, () => invokeOpenAICompatible(envelope.provider, prompt, { env: this.env, fetchImpl: this.fetchImpl,
        assertActive: admission?.assertActive, signal: admission?.controller.signal }), { cancellationKind: 'direct_api', signal: admission?.controller.signal });
      const receipt = { invocation_id: requestId, provider_response_id: response.provider_response_id };
      const completion = { status: 'succeeded', summary: 'Advisory response received', structured_output: { text: response.text }, artifacts: [], evidence: [{ kind: 'provider_response', ...receipt, model: response.model }], changed_paths: [], outside_paths: [] };
      const durable = await this.runtime.runs.saveExecutorResult(runId, args.attempt_id, { kind: 'direct_api_response', completion });
      await this.runtime.recordExecutorEvent(runId, { ...args, event: { kind: 'result_proposed', metadata: { ...durable, final_acceptance_required: envelope.role === 'finalizer' } } });
      await this.runtime.recordDispatchReceipt(runId, { ...request, receipt });
      await this.runtime.recordUsage(runId, { ...request, usage: normalizedUsage(response.usage) });
      const state = await this.runtime.completeNode(runId, { ...args, completion });
      return { dispatched: true, receipt, state };
    }
    if (adapter.execution === 'codex_thread') {
      return { dispatched: false, handoff_required: true, request_id: requestId,
        adapter, compiled_prompt: prompt, envelope, thread_handoff: prepared.thread_handoff,
        completion_contract: { required: ['status', 'summary', 'structured_output', 'artifacts', 'evidence', 'changed_paths', 'outside_paths'], final_acceptance: false },
      };
    }
    // Native, main, MCP and review packets are handed to the authorized host.
    // It must persist the returned exact task identity before reporting completion.
    return { dispatched: false, handoff_required: true, request_id: requestId,
      adapter, compiled_prompt: prompt, envelope,
      completion_contract: { required: ['status', 'summary', 'structured_output', 'artifacts', 'evidence', 'changed_paths', 'outside_paths'], final_acceptance: envelope.role === 'finalizer' },
    };
  }

  async reconcileConnector(runId, args) {
    await this.runtime.execution(runId, args, { allowInactive: true });
    const { state, pins } = await this.runtime.runs.read(runId);
    // Authentication also permits interrupted leases for exact-identity receipts.
    const node = state.nodes[args.node_id]; const attempt = node?.attempts.find(item => item.id === args.attempt_id);
    requireValue(attempt?.dispatch, 'DISPATCH_INTENT_MISSING', 'No persisted dispatch intent exists');
    const definition = pins.root.workflow.nodes.find(item => item.id === args.node_id);
    const provider = pins.providers.find(item => item.id === definition?.executor?.provider_id);
    requireValue(provider?.kind === 'builtin_connector', 'CONNECTOR_REQUIRED', 'Reconciliation requires a pinned connector node');
    // The preallocated attempt UUID is the connector task key even if a crash
    // occurred before its receipt reached the Run journal. Never select latest.
    const task = await this.registry.status(attempt.id, 0);
    requireValue(task.task_id === attempt.id && task.provider_id === provider.id && task.stage_id === args.node_id && task.task_type_id === state.workflow_id,
      'CONNECTOR_IDENTITY', 'Connector returned a different pinned task');
    const receipt = attempt.dispatch.receipt ?? receiptIdentity(task);
    requireValue(sameReceipt(receiptIdentity(task), receipt), 'CONNECTOR_IDENTITY', 'Connector remote identity differs from the committed receipt');
    await this.runtime.recordDispatchReceipt(runId, { ...args, request_id: attempt.dispatch.request_id, receipt });
    await this.recordConnectorTerminalUsage(runId, args, attempt, task);
    if (attempt.dispatch.cancellation_pending && ['completed','cancelled'].includes(task.state)) {
      await this.runtime.runs.mutate(runId, 'connector_control', state => {
        requireValue(state.control_hash === digest(args.control_token), 'RUN_AUTHORITY', 'Controller changed while observing cancellation');
        const current = state.nodes[args.node_id].attempts.find(item => item.id === args.attempt_id);
        current.dispatch.cancellation_pending = false; current.connector_control = { action: 'observe', phase: 'observed', state: task.state, at: new Date().toISOString() };
      });
    }
    return { task, receipt, requires_explicit_retry: ['interrupted', 'failed'].includes(node.status) };
  }

  async collectConnector(runId, args) {
    const envelope = await this.runtime.execution(runId, args);
    requireValue(envelope.provider?.kind === 'builtin_connector', 'CONNECTOR_REQUIRED', 'Collection requires a connector node');
    const { task, receipt } = await this.reconcileConnector(runId, args);
    requireValue(task.provider_id === envelope.provider.id && task.stage_id === envelope.node_id && task.task_type_id === envelope.workflow_id, 'CONNECTOR_IDENTITY', 'Connector task belongs to a different pinned node');
    if (task.state === 'completed') {
      await confirmConnectorExecutionQuiescent(this.registry, args.attempt_id);
      requireValue(task.terminal_evidence && task.scope?.compliant === true && Array.isArray(task.scope.changed_paths) && Array.isArray(task.scope.outside_paths), 'CONNECTOR_EVIDENCE', 'Connector completion lacks observed terminal/scope evidence');
      return this.runtime.completeNode(runId, { ...args, completion: { status: 'succeeded', summary: 'Connector result and workspace scope verified', structured_output: task.result,
        artifacts: task.result?.artifact_path ? [task.result.artifact_path] : [], evidence: [{ kind: 'connector_terminal', receipt, terminal: task.terminal_evidence, scope: task.scope }], changed_paths: task.scope.changed_paths, outside_paths: task.scope.outside_paths } });
    }
    if (['failed', 'cancelled', 'scope_violation', 'abandoned'].includes(task.state)) {
      await confirmConnectorExecutionQuiescent(this.registry, args.attempt_id);
      return this.runtime.failNode(runId, { ...args, error: { code: task.error?.code ?? 'CONNECTOR_FAILED', message: task.error?.message ?? `Connector reached ${task.state}` } });
    }
    return { pending: true, task, receipt };
  }

  async recoveryPreparation(runId, args) {
    const record = await controllerAttempt(this.runtime, runId, args);
    requireValue(record.node.status === 'interrupted', 'RECOVERY_ATTEMPT_STATE', 'Fence the old attempt before recovery');
    const config = await this.getConfig();
    requireValue(config.global.enabled && !isEnvironmentDisabled(this.env), 'CONTROL_DISABLED', 'Workflow execution is disabled');
    const provider = record.pins.providers.find(item => item.id === record.definition.executor?.provider_id);
    if (provider) {
      const current = config.providers.find(item => item.id === provider.id);
      requireValue(current?.enabled && current.capabilities.read && (nodePermissions(record.definition, record.state).access !== 'bounded_write' || current.capabilities.write), 'PROVIDER_DISABLED', 'Pinned Provider permission was revoked');
      requireValue(!current.requires_user_approval || provider.requires_user_approval, 'PROVIDER_POLICY_CHANGED', 'Provider approval requirements changed');
    }
    return { ...record, provider };
  }
  async controlConnector(runId, args) {
    const envelope = await this.runtime.execution(runId, args, { allowInactive: true });
    requireValue(envelope.provider?.kind === 'builtin_connector', 'CONNECTOR_REQUIRED', 'This node is not a connector');
    const control = args.control;
    requireValue(control && ['respond_permission','respond_input','cancel','disconnect','abandon','reconcile'].includes(control.action) && Buffer.byteLength(canonicalJSON(control)) <= 32000, 'CONNECTOR_CONTROL_SCHEMA', 'Select a bounded exact connector action');
    const record = await controllerAttempt(this.runtime, runId, args);
    if (['respond_permission','respond_input'].includes(control.action)) {
      await this.runtime.execution(runId, args);
      const config = await this.getConfig(); const provider = config.providers.find(item => item.id === envelope.provider.id);
      requireValue(config.global.enabled && !isEnvironmentDisabled(this.env) && provider?.enabled, 'PROVIDER_DISABLED', 'A disabled executor cannot receive new permission or input');
      requireValue(provider.capabilities.read && (envelope.access !== 'bounded_write' || provider.capabilities.write), 'PROVIDER_CAPABILITY', 'Provider capability was revoked before its permission/input response');
      requireValue(!provider.requires_user_approval || envelope.provider.requires_user_approval, 'PROVIDER_POLICY_CHANGED', 'Provider now requires approval absent from this Run');
    }
    const task = await this.registry.status(args.attempt_id, 0);
    const receipt = receiptIdentity(task);
    requireValue(task.task_id === args.attempt_id && task.provider_id === envelope.provider.id && task.stage_id === args.node_id && task.task_type_id === envelope.workflow_id && record.attempt.dispatch?.receipt && sameReceipt(receipt, record.attempt.dispatch.receipt), 'CONNECTOR_IDENTITY', 'Control target differs from the persisted exact connector');
    await this.runtime.runs.mutate(runId, 'connector_control', state => {
      requireValue(state.control_hash === record.state.control_hash, 'RUN_AUTHORITY', 'Controller changed before connector control');
      state.nodes[args.node_id].attempts.find(item => item.id === args.attempt_id).connector_control = { action: control.action, phase: 'intent', at: new Date().toISOString() };
    }, { expected_sequence: record.sequence });
    let result;
    try { result = await this.registry.control(args.attempt_id, control); }
    catch (error) {
      try { await this.runtime.runs.mutate(runId, 'connector_control', state => { state.nodes[args.node_id].attempts.find(item => item.id === args.attempt_id).connector_control = { action: control.action, phase: 'failed', code: error.code ?? 'CONNECTOR_CONTROL_FAILED' }; }); }
      catch (audit) { throw new AggregateError([error, audit], 'Connector control and audit persistence failed'); }
      throw error;
    }
    requireValue(sameReceipt(receiptIdentity(result), receipt), 'CONNECTOR_IDENTITY', 'Connector control returned another remote identity');
    await this.recordConnectorTerminalUsage(runId, args, record.attempt, result);
    await this.runtime.runs.mutate(runId, 'connector_control', state => {
      const attempt = state.nodes[args.node_id].attempts.find(item => item.id === args.attempt_id);
      attempt.connector_control = { action: control.action, phase: 'observed', state: result.state, at: new Date().toISOString() };
      if (result.state === 'cancelled') attempt.dispatch.cancellation_pending = false;
    });
    return { task: result, remote_cancel_confirmed: result.state === 'cancelled' };
  }
  async cancelPendingConnectors(runId, controlToken) {
    await this.runtime.authorizeController(runId, { control_token: controlToken });
    this.attemptAdmission.fenceRun(runId);
    const errors = [];
    try { await this.attemptAdmission.retryCleanup(runId, 'connector'); } catch (error) { errors.push(error); }
    try { await this.attemptAdmission.wait(runId, 'connector'); } catch (error) { errors.push(error); }
    const record = await this.runtime.runs.read(runId);
    for (const [nodeId, node] of Object.entries(record.state.nodes)) for (const attempt of node.attempts) if (attempt.dispatch?.cancellation_pending) {
      const definition = record.pins.root.workflow.nodes.find(item => item.id === nodeId);
      const provider = record.pins.providers.find(item => item.id === definition.executor?.provider_id);
      if (provider?.kind !== 'builtin_connector') continue;
      try {
        const task = await this.registry.status(attempt.id, 0); const receipt = receiptIdentity(task);
        requireValue(task.task_id === attempt.id && task.provider_id === provider.id && task.stage_id === nodeId && task.task_type_id === record.state.workflow_id, 'CONNECTOR_IDENTITY', 'Cancellation target differs from the pinned attempt');
        // Cancellation may win after the connector reserved its exact task but
        // before dispatch could journal the receipt. Adopt only that pinned
        // identity; never select a latest task or launch a replacement.
        if (!attempt.dispatch.receipt) await this.runtime.recordDispatchReceipt(runId, { run_id: runId, control_token: controlToken,
          node_id: nodeId, attempt_id: attempt.id, lease_token: leaseToken(controlToken, runId, nodeId, attempt.id, attempt.lease_generation ?? 0),
          request_id: attempt.dispatch.request_id, receipt });
        else requireValue(sameReceipt(receipt, attempt.dispatch.receipt), 'CONNECTOR_IDENTITY', 'Cancellation target differs from the recorded task');
        if (task.state === 'failed' && (task.startup_cleanup?.local_quiescent === true && task.startup_cleanup.prompt_submitted === false
          || Object.keys(task.remote_identity ?? {}).length === 0)) {
          await this.recordConnectorTerminalUsage(runId, { run_id: runId, control_token: controlToken, node_id: nodeId, attempt_id: attempt.id,
            lease_token: leaseToken(controlToken, runId, nodeId, attempt.id, attempt.lease_generation ?? 0) }, attempt, task);
          await this.runtime.runs.mutate(runId, 'connector_control', state => { const current = state.nodes[nodeId].attempts.find(item => item.id === attempt.id); current.dispatch.cancellation_pending = false; current.connector_control = { action: 'cancel', phase: 'observed', state: task.state, before_remote_submission: true }; });
          continue;
        }
        if (['completed','cancelled'].includes(task.state)) {
          await confirmConnectorExecutionQuiescent(this.registry, attempt.id);
          await this.recordConnectorTerminalUsage(runId, { run_id: runId, control_token: controlToken, node_id: nodeId, attempt_id: attempt.id,
            lease_token: leaseToken(controlToken, runId, nodeId, attempt.id, attempt.lease_generation ?? 0) }, attempt, task);
          await this.runtime.runs.mutate(runId, 'connector_control', state => { const current = state.nodes[nodeId].attempts.find(item => item.id === attempt.id); current.dispatch.cancellation_pending = false; current.connector_control = { action: 'cancel', phase: 'observed', state: task.state, already_terminal: true }; });
          continue;
        }
        const identity = task.remote_identity ?? {};
        const cancelled = await this.controlConnector(runId, { run_id: runId, control_token: controlToken, node_id: nodeId, attempt_id: attempt.id,
          lease_token: leaseToken(controlToken, runId, nodeId, attempt.id, attempt.lease_generation ?? 0), control: { action: 'cancel', confirm: true,
            ...(identity.agent_id ? { expected_agent_id: identity.agent_id } : {}),
            ...(identity.session_id ? { expected_session_id: identity.session_id } : {}), ...(identity.run_id ? { expected_run_id: identity.run_id } : {}) } });
        if (cancelled.remote_cancel_confirmed) await confirmConnectorExecutionQuiescent(this.registry, attempt.id);
        if (!cancelled.remote_cancel_confirmed) {
          const observed = await this.registry.status(attempt.id, 5_000);
          requireValue(sameReceipt(receiptIdentity(observed), receipt), 'CONNECTOR_IDENTITY', 'Exact remote cancellation changed identity');
          await confirmConnectorExecutionQuiescent(this.registry, attempt.id);
          await this.runtime.runs.mutate(runId, 'connector_control', state => {
            const current = state.nodes[nodeId].attempts.find(item => item.id === attempt.id);
            current.dispatch.cancellation_pending = false;
            current.connector_control = { action: 'cancel', phase: 'observed', state: observed.state, at: new Date().toISOString() };
          });
        }
      } catch (error) { errors.push(error); }
    }
    if (errors.length) throw Object.assign(new AggregateError(errors, 'Some exact remote tasks have unconfirmed cancellation'), { code: 'CONNECTOR_CANCEL_INCOMPLETE' });
  }
  async cancelPendingDirectApi(runId, controlToken) {
    await this.runtime.authorizeController(runId, { control_token: controlToken });
    this.attemptAdmission.fenceRun(runId);
    try { await this.attemptAdmission.wait(runId, 'direct_api'); }
    catch (error) { throw Object.assign(error, { code: 'DIRECT_API_CANCEL_INCOMPLETE' }); }
  }
  async reattachConnector(runId, args) {
    const record = await this.recoveryPreparation(runId, args);
    requireValue(record.provider?.kind === 'builtin_connector' && record.attempt.dispatch, 'CONNECTOR_REQUIRED', 'Reattachment requires an existing pinned connector dispatch');
    function verify(task) {
      requireValue(task.task_id === args.attempt_id && task.provider_id === record.provider.id && task.stage_id === args.node_id && task.task_type_id === record.state.workflow_id,
        'CONNECTOR_IDENTITY', 'Observed task belongs to another Run node or Provider');
      requireValue(task.remote_identity && Object.keys(task.remote_identity).length > 0, 'CONNECTOR_IDENTITY', 'Reattachment requires observed exact remote identity');
      const receipt = receiptIdentity(task);
      requireValue(!record.attempt.dispatch.receipt || sameReceipt(record.attempt.dispatch.receipt, receipt), 'DISPATCH_CONFLICT', 'Remote identity differs from the recorded dispatch');
      return record.attempt.dispatch.receipt ?? receipt;
    }
    let task = await this.registry.status(args.attempt_id, 0); let receipt = verify(task);
    if (['unknown_after_restart','needs_attention'].includes(task.state)) {
      await this.runtime.runs.mutate(runId, 'reattach', state => {
        requireValue(state.control_hash === record.state.control_hash && state.nodes[args.node_id].status === 'interrupted', 'RECOVERY_ATTEMPT_CHANGED', 'Run authority changed before transport reconciliation');
        state.nodes[args.node_id].attempts.find(item => item.id === args.attempt_id).reconciliation = { kind: 'connector_transport_intent', receipt, resubmitted: false, at: new Date().toISOString() };
      }, { expected_sequence: record.sequence });
      // This adapter operation attaches the saved remote ID; it never starts a task.
      task = await this.registry.control(args.attempt_id, { action: 'reconcile' }); receipt = verify(task);
    }
    await this.recordConnectorTerminalUsage(runId, args, record.attempt, task);
    requireValue(['running','completed','needs_permission','needs_input'].includes(task.state), 'CONNECTOR_RECOVERY_UNCONFIRMED', 'The exact connector task is not confirmed active or completed', { remote_state: task.state });
    const attached = await reattachAttempt(this.runtime, runId, args, { kind: 'connector_exact_identity', attempt_id: args.attempt_id, dispatch_request_id: record.attempt.dispatch.request_id, receipt, remote_state: task.state });
    return { ...attached, task };
  }
}
