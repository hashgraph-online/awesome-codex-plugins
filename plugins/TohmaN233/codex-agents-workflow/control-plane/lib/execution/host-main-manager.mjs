import { delimiter, dirname, isAbsolute, join, resolve } from 'node:path';
import { readFile } from 'node:fs/promises';
import { createCodexSession } from './codex-session.mjs';
import { preflightSemanticOutput, correctableCompletionError, boundedCompletionDiagnostic } from './completion-preflight.mjs';
import { semanticTurnsConsumed } from './completion-turn-budget.mjs';
import { createHostAuthBroker } from './codex-host-auth.mjs';
import { createWorkflowResourceBroker, loadNodeSkillSnapshots } from './workflow-resource-broker.mjs';
import {rejectWorkspaceScope} from './workspace-scope-evidence.mjs';
import {snapshotWorkspace, changedWorkspacePaths as changedPaths} from './workspace-snapshot.mjs';
import { qualifiedStrictSettings, validateStrictConfig, codexQualification } from './strict-config.mjs';
import { hostResultProposalEnvelope, semanticResultSchema, strictAgentOutputSchema } from './host-main-automation.mjs';
import { authoringReviewIdentity, isAuthoringRunProvenance } from '../authoring/authoring-workflows.mjs';
import { leaseToken } from '../workflow-execution-envelope.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import {materializeNodeInputs} from './node-input-materials.mjs';
import { validateData } from '../workflow-data-schema.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { isEnvironmentDisabled } from '../config.mjs';
import { compactCodexResultEvidence, persistCodexCommandAudits } from './codex-result-evidence.mjs';
import { assertExecutionAdmission, assertExecutionAttemptAdmission, executionAdmissionOpen } from './attempt-admission.mjs';
import { resolveMainModelSelection } from './main-model-selection.mjs';

const managers = new Map();
const terminal = new Set(['succeeded', 'failed', 'cancelled', 'stopped']);
const entryKey = runId => runId;

const codeOf = error => typeof error?.code === 'string' && /^[A-Z0-9_]{1,100}$/.test(error.code)
  ? error.code : 'HOST_MAIN_FAILED';

function hostMainUsage(usage) {
  requireValue(usage && typeof usage.available === 'boolean', 'CODEX_USAGE_SCHEMA', 'Host Main requires a metering availability signal');
  const result = { unknown: true }; // Codex reports tokens, not a billable micro-unit cost.
  for (const key of ['input_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'output_tokens', 'reasoning_output_tokens']) {
    if (usage[key] !== undefined) result[key] = usage[key];
  }
  return result;
}

function combinedTurnUsage(turns) {
  const total = { available: turns.every(turn => turn?.available === true) };
  for (const key of ['input_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'output_tokens', 'reasoning_output_tokens']) {
    const values = turns.map(turn => turn?.[key]);
    if (values.every(value => Number.isSafeInteger(value) && value >= 0)) total[key] = values.reduce((sum, value) => sum + value, 0);
  }
  return total;
}

function diagnosticOf(error) {
  const messages = [];
  const visit = value => {
    if (!value || messages.length >= 8) return;
    messages.push(`${codeOf(value)}: ${String(value.message ?? value)}`);
    if (value instanceof AggregateError) for (const child of value.errors) visit(child);
    else if (value.cause) visit(value.cause);
  };
  visit(error);
  return messages.join(' | ')
    .replace(/\bBearer\s+\S+/ig, 'Bearer [redacted]')
    .replace(/((?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|cookie|secret)\s*[:=]\s*)\S+/ig, '$1[redacted]')
    .slice(0, 2000);
}

function within(path, boundary) {
  return boundary === '.' || path === boundary || path.startsWith(boundary.replaceAll('\\', '/').replace(/\/$/, '') + '/');
}
function augmentedEnvironment(env, runtimeEnvironment) {
  const directories = (runtimeEnvironment?.tools ?? [])
    .filter(tool => tool.status === 'found' && typeof tool.path === 'string' && isAbsolute(tool.path))
    .map(tool => dirname(tool.path));
  const inherited = env.PATH ?? env.Path ?? '';
  return { ...env, PATH: [...new Set([...directories, ...inherited.split(delimiter).filter(Boolean)])].join(delimiter) };
}
async function resourceItems(runtime, runId, envelope) {
  if (!envelope.resources.length) return [];
  const record = await runtime.runs.read(runId); const root = join(runtime.runs.directory(runId), 'objects');
  const resources = [];
  for (const path of envelope.resources) {
    const pin = record.pins.root.resources.find(item => item.path === path);
    requireValue(pin && pin.bytes <= 1024 * 1024, 'HOST_MAIN_RESOURCE', `Pinned resource is unavailable or too large: ${path}`);
    resources.push({ path, sha256: pin.sha256, bytes: await readFile(join(root, pin.sha256)) });
  }
  return resources;
}

function publicView(entry) {
  return {
    run_id: entry.runId,
    status: entry.status,
    ...(entry.nodeId ? { node_id: entry.nodeId } : {}),
    ...(entry.outcome ? { outcome: structuredClone(entry.outcome) } : {}),
    ...(entry.error ? { error: structuredClone(entry.error) } : {}),
  };
}

export function hostMainManagerFor(options) {
  const id = resolve(options.configPath);
  if (!managers.has(id)) managers.set(id, new HostMainManager(options));
  return managers.get(id);
}

export async function closeHostMainManagers() {
  const settled = await Promise.allSettled([...managers.entries()].map(async ([id,manager]) => { await manager.close(); managers.delete(id); }));
  const failures = settled.filter(item => item.status === 'rejected').map(item => item.reason);
  if (failures.length) throw new AggregateError(failures, 'Host Main shutdown requires attention');
}

const entryHasUnconfirmedExecution = entry => entry.broker?.isQuiescent?.() === false;
const entryNeedsRecovery = entry => entry.cleanupPending === true || entryHasUnconfirmedExecution(entry) || Boolean(entry.session);
async function settleOwnedTask(promise) {
  if (!promise) return;
  let timer; try { await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Object.assign(new Error('Host Main task did not settle after confirmed stop'),{code:'HOST_MAIN_STOP_PENDING'})),5000);})]); }
  finally { clearTimeout(timer); }
}
async function closeSessionForRecovery(session) {
  try { await session.close(); }
  catch (first) {
    try { await session.close(); }
    catch (second) { throw new AggregateError([first,second], 'Host Main session cleanup retry failed'); }
  }
}

/**
 * Executes logical Main nodes in fresh, host-owned Codex threads. The logical
 * actor remains stable for Run authorization, while every node receives only
 * its projected inputs, pinned resources and scoped capability broker.
 */
export class HostMainManager {
  constructor({ configPath, getConfig, env = process.env, sessionFactory = createCodexSession, qualify = qualifiedStrictSettings, mainModelSelection = resolveMainModelSelection }) {
    this.configPath = resolve(configPath); this.getConfig = getConfig; this.env = env;
    this.sessionFactory = sessionFactory; this.qualify = qualify; this.mainModelSelection = mainModelSelection;
    this.parent = join(dirname(this.configPath), 'host-main-profiles');
    this.entries = new Map(); this.hostAuth = null; this.hostAuthBinary = null; this.accepting = executionAdmissionOpen(this.configPath);
  }

  async launchRun({ runtime, drive, runId, controlToken, owner }) {
    requireValue(this.accepting && executionAdmissionOpen(this.configPath), 'HOST_MAIN_STOPPED', 'Host Main manager is closed to new work');
    assertExecutionAdmission(this.configPath, runId);
    requireValue(!this.entries.has(entryKey(runId)), 'HOST_MAIN_RECOVERY_PENDING', 'This Run already has a Host Main execution owner');
    const entry = { runId, runtime, drive, controlToken, owner, handoff: null, nodeId: null, status: 'starting', outcome: null,
      error: null, session: null, broker: null, stopping: false, cleanupPending: false, job: null, assertActive: null };
    this.entries.set(entryKey(runId), entry);
    entry.job = Promise.resolve().then(() => this.executeLoop(entry)).catch(error => this.fail(entry, error));
    return publicView(entry);
  }

  async launch({ runtime, drive, handoff }) {
    if (handoff?.stop_reason !== 'main_node') return handoff;
    requireValue(this.accepting && executionAdmissionOpen(this.configPath), 'HOST_MAIN_STOPPED', 'Host Main manager is closed to new work');
    const runId = handoff.host_binding.run_id; const prior = this.entries.get(entryKey(runId));
    assertExecutionAttemptAdmission(this.configPath, runId, handoff.host_binding.node_id, handoff.host_binding.attempt_id);
    if (prior && ['starting', 'running', 'awaiting_human_acceptance'].includes(prior.status)) return publicView(prior);
    requireValue(!prior || !entryNeedsRecovery(prior), 'HOST_MAIN_RECOVERY_PENDING', 'The prior Host Main execution still owns recovery state');
    const entry = { runId, runtime, drive, handoff, nodeId: handoff.host_binding.node_id, status: 'starting', outcome: null,
      error: null, session: null, broker: null, stopping: false, cleanupPending: false, job: null, assertActive: null };
    this.entries.set(entryKey(runId), entry);
    entry.job = this.executeLoop(entry).catch(error => this.fail(entry, error));
    return publicView(entry);
  }

  async wait(runId) {
    const entry = this.entries.get(entryKey(runId));
    requireValue(entry?.job, 'HOST_MAIN_UNAVAILABLE', 'This Run has no live Host Main execution');
    await entry.job; return publicView(entry);
  }

  async executeLoop(entry) {
    const assertActive = () => { requireValue(this.accepting && !entry.stopping, 'HOST_MAIN_STOPPED', 'Host Main permission was revoked'); const binding = entry.handoff?.host_binding; if (binding) assertExecutionAttemptAdmission(this.configPath, entry.runId, binding.node_id, binding.attempt_id); else assertExecutionAdmission(this.configPath, entry.runId); };
    let handoff = entry.handoff;
    if (!handoff) {
      entry.status = 'running';
      handoff = await entry.drive.advanceToMain(entry.runId, {
        control_token: entry.controlToken, owner: entry.owner, request_prefix: `host-main-${entry.runId}`, assertActive,
      });
      assertActive();
    }
    while (handoff?.stop_reason === 'main_node') {
      assertActive();
      entry.handoff = handoff; entry.nodeId = handoff.host_binding.node_id; entry.status = 'running';
      const result = await this.executeNode(entry, handoff);
      if (result.final_acceptance_required) {
        entry.status = 'awaiting_human_acceptance'; entry.outcome = result; this.compact(entry); return publicView(entry);
      }
      const state = await entry.runtime.get(entry.runId);
      if (terminal.has(state.status)) {
        entry.status = state.status; entry.outcome = { status: state.status, stop_reason: 'terminal' }; this.compact(entry); return publicView(entry);
      }
      assertActive();
      handoff = await entry.drive.advanceToMain(entry.runId, {
        control_token: handoff.host_binding.control_token,
        owner: handoff.host_binding.owner,
        request_prefix: `host-main-${entry.runId}`,
        assertActive,
      });
      assertActive();
    }
    entry.outcome = handoff; entry.status = terminal.has(handoff?.status) ? handoff.status : 'attention'; this.compact(entry);
    return publicView(entry);
  }

  async executeNode(entry, handoff) {
    const binding = handoff.host_binding; const { runtime, runId } = entry;
    const record = await runtime.runs.read(runId);
    const definition = record.pins.root.workflow.nodes.find(node => node.id === binding.node_id);
    requireValue(definition?.executor?.kind === 'main' && definition.executor.mode !== 'orchestration', 'HOST_MAIN_NODE', 'Host Main may execute only a logical Main node');
    const consumed = semanticTurnsConsumed(record.state.nodes[binding.node_id]);
    const remainingTurns = (definition.retry?.max_attempts ?? 3) - consumed;
    requireValue(Number.isSafeInteger(remainingTurns) && remainingTurns > 0, 'RETRY_LIMIT', 'Main node exhausted its pinned semantic attempt limit');
    const envelope = await runtime.execution(runId, binding);
    const settings = await this.qualify(await this.getConfig(), this.env);
    const reviewer = record.pins.authoring_reviewer ?? record.pins.generation?.reviewer ?? null;
    if (reviewer) {
      const current = (await this.getConfig()).providers.find(provider => provider.id === reviewer.id);
      requireValue(current?.enabled && current.kind === 'native_agent' && current.capabilities.read && canonicalJSON(current.config) === canonicalJSON(reviewer.config),
        'GENERATION_REVIEW_PROVIDER', 'Review binding must match the registered Provider');
    }
    const { model, effort } = reviewer
      ? { model: reviewer.config.model, effort: reviewer.config.reasoning_effort }
      : await this.mainModelSelection(record, settings, { env: this.env });
    const finalAcceptance = record.pins.root.workflow.finalization?.node_id === definition.id
      && isAuthoringRunProvenance(record.pins.root.provenance);
    const event = (kind, metadata) => runtime.recordExecutorEvent(runId, { ...binding, event: { kind, metadata } });
    const snapshot = (phase = 'completion') => snapshotWorkspace(envelope.workspace, {access: envelope.access, allowedPaths: envelope.effective_allowed_paths,
      requiredPaths: (definition.required_artifacts ?? []).map(item => item.path), codePrefix: 'HOST_MAIN',
      onUnreadable: metadata => event('workspace_unreadable_authorized_path', {...metadata, phase})});
    const assertActive = entry.assertActive = () => { requireValue(this.accepting && !entry.stopping, 'HOST_MAIN_STOPPED', 'Host Main permission was revoked'); assertExecutionAttemptAdmission(this.configPath, entry.runId, binding.node_id, binding.attempt_id); };
    const authorize = async () => {
      assertActive();
      await runtime.execution(runId, binding, { allowPaused: entry.status === 'running' });
      assertActive();
      const current = await this.getConfig(); const currentSettings = validateStrictConfig(current.strict_executor);
      assertActive();
      requireValue(current.global.enabled && !isEnvironmentDisabled(this.env), 'CONTROL_DISABLED', 'Workflow execution was disabled');
      requireValue(canonicalJSON(currentSettings) === canonicalJSON(settings), 'STRICT_CONFIG_CHANGED', 'Host Main executor settings changed during the attempt');
      if (reviewer) {
        const provider = current.providers.find(item => item.id === reviewer.id);
        requireValue(provider?.enabled && canonicalJSON(provider.config) === canonicalJSON(reviewer.config), 'GENERATION_REVIEW_PROVIDER', 'Review Provider changed during the attempt');
      }
      assertActive();
    };
    await authorize();
    const material=await materializeNodeInputs({directory:join(envelope.workspace,'work','.workflow-runtime','host-main',runId,binding.attempt_id),
      envelope:{...envelope,prompt_template:envelope.prompt_template??handoff.agent_packet.prompt}});
    await event('node_input_materials',{index:0,inputs_path:material.inputs_path,prompt_sha256:material.prompt_sha256,input_count:material.manifest.length});
    const before = await snapshot('before');
    const resources = await resourceItems(runtime, runId, envelope);
    const allowedSkills = await loadNodeSkillSnapshots(runtime, runId, envelope);
    entry.broker = await createWorkflowResourceBroker({
      workspace: envelope.workspace, access: envelope.access, allowedPaths: envelope.effective_allowed_paths,
      resources, authorize,
      onOperation: metadata => event('tool_operation', metadata),
    });
    await event('tool_capabilities', { access: envelope.access, tools: entry.broker.tools().map(tool => tool.name).join(',') });
    if (settings.authentication.mode === 'host_chatgpt' && this.hostAuthBinary !== settings.codex_binary) {
      this.hostAuth?.clear();
      this.hostAuth = createHostAuthBroker({ binary: settings.codex_binary, cwd: this.parent, env: this.env });
      this.hostAuthBinary = settings.codex_binary;
    }
    const environment = augmentedEnvironment(this.env, record.state.runtime_environment ?? record.state.constraints?.runtime_environment);
    entry.session = await this.sessionFactory({
      parent: this.parent, owner: { run_id: runId, node_id: binding.node_id, attempt_id: binding.attempt_id },
      hostAuth: settings.authentication.mode === 'host_chatgpt' ? this.hostAuth : undefined,
      binary: settings.codex_binary, expectedBinaryHash: settings.binary_sha256, expectedBinaryPath: codexQualification(settings)?.resolved_path,
      dynamicToolFormat: codexQualification(settings)?.dynamic_tool_format, authentication: settings.authentication, model, effort,
      cwd: envelope.workspace, access: envelope.access, allowedPaths:envelope.effective_allowed_paths, env: environment, toolBroker: entry.broker, authorize, assertActive,
      skillPolicy: envelope.skill_policy ?? {mode:"cooperative",implicit:"deny",ambient_allow:[],shadowed_skill_paths:[]}, allowedSkills,
      maxTurns: remainingTurns,
      onSessionOwned: session => { entry.session = session; },
      onProfilePrepared: profile => event('profile_owned', { home: profile.home, ...(profile.receipt_home ? {receipt_home:profile.receipt_home} : {}), executable_sha256: profile.binary_sha256 }),
      onModelCatalog: metadata => event('model_catalog', metadata),
      onEvent: metadata => {
        if (!['thread/started', 'turn/started', 'turn/completed', 'thread/tokenUsage/updated', 'item/started', 'item/completed', 'error'].includes(metadata.method)) return;
        return event('codex_event', metadata);
      },
    });
    assertActive();
    const authoring = isAuthoringRunProvenance(record.pins.root.provenance) && binding.node_id === record.pins.root.workflow.finalization.node_id
      ? authoringReviewIdentity(record) : null;
    const receipt = {
      invocation_id: `host-main-${binding.attempt_id}`, executor: 'codex-app-server-host-main', executable_sha256: settings.binary_sha256,
      model, effort, main_actor: record.state.main_actor, session_id: `logical-main-${runId}`, call_chain_id: `workflow-run-${runId}`,
      ...(authoring ? { authoring_review_context: authoring } : {}),
    };
    await runtime.recordHostMainDispatchReceipt(runId, { ...binding, request_id: `dispatch-${binding.attempt_id}`, receipt });
    await event('session_state', { status: 'running' });
    const canBlock = definition.decision?.options?.includes('blocked') === true;
    const modelSchema = semanticResultSchema(definition, { finalAcceptance });
    if (canBlock) {
      modelSchema.properties.block_reason = { type: 'string', maxLength: 600 };
      modelSchema.required = [...new Set([...(modelSchema.required ?? []), 'block_reason'])];
    }
    const schema = strictAgentOutputSchema(modelSchema);
    const instruction = `\n\nTask file-change scope: ${envelope.access === 'read_only' ? 'read-only' : JSON.stringify(envelope.effective_allowed_paths)}.`
      + '\nReturn only a JSON value matching the requested semantic result schema. Do not return Workflow lifecycle fields, identifiers, receipts or human-acceptance records.'
      + (!finalAcceptance && record.pins.root.workflow.finalization?.node_id === definition.id ? ' Report your evidence-based completion assessment; the Host handles any separately declared approval.' : '')
      + (canBlock ? ' Set block_reason to an empty string on success. A failed Python/tool call is recoverable: inspect its output, correct the invocation or code, and retry. Use decision=blocked only for a concrete unrecoverable obstacle, with its reason in block_reason.' : '');
    const prompt = material.prompt + instruction;
    let result; let output; let blockReason = ''; let missingArtifacts = []; const usages = [];
    let correctionPrompt = '';
    try {
      for (let correction = 0; correction < remainingTurns; correction++) {
        await authorize();
        await runtime.reserveHostMainTurn(runId, binding);
        result = await (correction === 0 ? entry.session.turn(prompt, { output_schema: schema, timeout_ms: settings.inactivity_timeout_ms })
          : entry.session.continueTurn(correctionPrompt, { output_schema: schema, timeout_ms: settings.inactivity_timeout_ms }));
        usages.push(result.usage);
        const expectedInput = digest(canonicalJSON([{type: 'text', text: correction === 0 ? prompt : correctionPrompt}]));
        requireValue(result.audit?.input_sha256 === expectedInput, 'HOST_MAIN_INPUT_MISMATCH', 'Main session input differs from the exact Host task');
        let validationError; let rawBlockReason = '';
        try {
          output = JSON.parse(result.output);
          validateData(output, modelSchema);
          if (canBlock) { rawBlockReason = output?.block_reason; delete output.block_reason; }
          await preflightSemanticOutput(definition, output, envelope.workspace, { ...record, finalAcceptance });
        } catch (error) {
          validationError = error instanceof SyntaxError
            ? Object.assign(new Error('Host Main result is not the required JSON value'), { code: 'HOST_MAIN_OUTPUT_JSON' }) : error;
        }
        if (validationError) {
          if (!correctableCompletionError(validationError)) throw validationError;
          const diagnostic = JSON.stringify(boundedCompletionDiagnostic(validationError));
          await event('completion_invalid', { correction, diagnostic, thread_id: result.thread_id, turn_id: result.turn_id });
          if (correction + 1 === remainingTurns) throw validationError;
          correctionPrompt = `The prior result failed Host completion validation: ${diagnostic}. Correct that exact error in the current node and return the complete declared JSON result. The Host will validate it again.`;
          continue;
        }
        if (canBlock) {
          blockReason = diagnosticOf(new Error(rawBlockReason || 'no concrete reason supplied')).slice(0, 700);
        }
        if (canBlock && output.decision === 'blocked') {
          await event('semantic_blocked', { correction, reason: blockReason, thread_id: result.thread_id, turn_id: result.turn_id });
          if (correction + 1 === remainingTurns) break;
          correctionPrompt = `The prior result reported blocked: ${JSON.stringify(blockReason)}. In this same node thread, correct a recoverable command or code error if possible and return the complete declared JSON result. Report blocked only for a concrete unrecoverable obstacle.`;
          continue;
        }
        if (definition.required_artifacts?.length) {
          const current = await snapshot();
          const observed = changedPaths(before, current);
          const key = path => process.platform === 'win32' ? path.toLowerCase() : path;
          const present = new Set([...current.keys()].map(key));
          missingArtifacts = definition.required_artifacts.filter(required => !observed.some(path => key(path) === key(required.path) && present.has(key(path))));
          if (missingArtifacts.length) {
            await event('required_artifacts_missing', { correction, paths: missingArtifacts.map(item => item.path).join(', ').slice(0, 4096), thread_id: result.thread_id, turn_id: result.turn_id });
            if (correction + 1 === remainingTurns) break;
            correctionPrompt = `The Host did not observe these required output paths as newly written: ${JSON.stringify(missingArtifacts.map(item => item.path))}. Produce and verify them in the current node workspace, then return the complete declared JSON result.`;
            continue;
          }
        }
        break;
      }
    } catch (error) {
      if (usages.length) await runtime.recordHostMainUsage(runId, { ...binding, request_id: `dispatch-${binding.attempt_id}`, usage: hostMainUsage(combinedTurnUsage(usages)) });
      throw error;
    }
    await entry.session.close(); entry.session = null;
    await event('session_state', { status: 'closed' });
    const after = await snapshot(); const changed = changedPaths(before, after);
    const outside = envelope.access === 'read_only' ? changed : changed.filter(path => !envelope.effective_allowed_paths.some(boundary => within(path, boundary)));
    if(outside.length)await rejectWorkspaceScope({runtime,runId,attemptId:binding.attempt_id,code:'HOST_MAIN_SCOPE_VIOLATION',changed,outside,before,after,event});
    const commandAuditArtifact=await persistCodexCommandAudits(runtime,runId,`command-audit-${binding.attempt_id}`,
      [{identity:{thread_id:result.thread_id,turn_id:result.turn_id},result}]);
    const completion = hostResultProposalEnvelope(definition, {
      output, summary: `Main completed ${definition.id}`, artifacts: changed, changed_paths: changed, outside_paths: [],
      evidence: [{ kind: 'host_main_result', thread_id: result.thread_id, turn_id: result.turn_id,
        ...compactCodexResultEvidence(result),
        ...(commandAuditArtifact ? { command_audit_artifact: commandAuditArtifact } : {}) }],
    }, { finalAcceptance });
    await runtime.recordHostMainUsage(runId, { ...binding, request_id: `dispatch-${binding.attempt_id}`, usage: hostMainUsage(combinedTurnUsage(usages)) });
    if (missingArtifacts.length && completion.structured_output.decision !== 'blocked') {
      await runtime.failNode(runId, { ...binding, error: { code: 'REQUIRED_ARTIFACT_MISSING', message: `Host Main did not produce the declared output paths after correction: ${missingArtifacts.map(item => item.path).join(', ')}` } });
      return { final_acceptance_required: false };
    }
    if (definition.decision && completion.structured_output.decision === 'blocked') {
      await runtime.failNode(runId, { ...binding, error: { code: 'WORKFLOW_NODE_BLOCKED', message: blockReason } });
      return { final_acceptance_required: false };
    }
    const saved = await runtime.runs.saveExecutorResult(runId, binding.attempt_id, completion);
    await event('result_proposed', { ...saved, final_acceptance_required: finalAcceptance, ...(authoring ?? {}) });
    if (finalAcceptance) return { final_acceptance_required: true, proposal: saved, node_id: binding.node_id };
    // Ordinary finalizers that declare an `accepted` semantic field make their
    // own decision. Other valid final outputs are themselves the Main decision;
    // only authoring Runs enter the separate human-acceptance path above.
    const ordinaryFinal = record.pins.root.workflow.finalization?.node_id === definition.id;
    const implicitMainAcceptance = ordinaryFinal && !Object.hasOwn(definition.outputs_schema?.properties ?? {}, 'accepted');
    await runtime.completeHostMainResult(runId, binding, implicitMainAcceptance ? { accepted: true } : {});
    return { final_acceptance_required: false };
  }

  async pending(runtime, runId) {
    const record = await runtime.runs.read(runId); const entry = this.entries.get(entryKey(runId));
    const finalId = record.pins.root.workflow.finalization?.node_id; const node = finalId ? record.state.nodes[finalId] : null;
    const attempt = node?.attempts.find(item => item.id === node.active_attempt_id) ?? node?.attempts.at(-1);
    if (attempt?.result_proposal?.final_acceptance_required) {
      const proposal = await runtime.runs.readExecutorResult(runId, attempt.id, attempt.result_proposal.sha256);
      return { kind: 'final_acceptance', run_id: runId, node_id: finalId, proposal };
    }
    if (entry && (!terminal.has(entry.status) || entry.error)) return { kind: 'host_main', ...publicView(entry) };
    const next = await runtime.next(runId);
    if (next.approvals.length || next.parent_block || record.state.status === 'blocked') {
      return { kind: 'control_wait', outcome: { status: record.state.status, stop_reason: next.approvals.length ? 'approval' : 'input_or_ambiguity', approvals: next.approvals, details: next.parent_block } };
    }
    return null;
  }

  async accept({ runtime, drive, runId, controlToken, accepted }) {
    requireValue(this.accepting && executionAdmissionOpen(this.configPath), 'HOST_MAIN_STOPPED', 'Host Main manager is closed to new work');
    assertExecutionAdmission(this.configPath, runId);
    requireValue(typeof accepted === 'boolean', 'FINAL_ACCEPTANCE_REQUIRED', 'Final acceptance requires an explicit human boolean');
    await runtime.authorizeController(runId, { control_token: controlToken });
    const record = await runtime.runs.read(runId); const finalId = record.pins.root.workflow.finalization?.node_id;
    const definition = record.pins.root.workflow.nodes.find(node => node.id === finalId);
    const node = record.state.nodes[finalId]; const attempt = node?.attempts.find(item => item.id === node.active_attempt_id) ?? node?.attempts.at(-1);
    requireValue(definition?.executor?.kind === 'main' && attempt?.result_proposal?.final_acceptance_required,
      'HOST_MAIN_ACCEPTANCE_MISSING', 'No isolated Main proposal is awaiting human acceptance');
    const args = { run_id: runId, control_token: controlToken, node_id: finalId, attempt_id: attempt.id,
      lease_token: leaseToken(controlToken, runId, finalId, attempt.id, attempt.lease_generation ?? 0) };
    const prior = this.entries.get(entryKey(runId));
    requireValue(!prior || !entryNeedsRecovery(prior), 'HOST_MAIN_RECOVERY_PENDING', 'Host Main cleanup must complete before final acceptance');
    if (!accepted) {
      await runtime.failNode(runId, { ...args, error: { code: 'FINAL_ACCEPTANCE_REJECTED', message: `Main node ${finalId} was rejected` } });
    } else if (isAuthoringRunProvenance(record.pins.root.provenance)) {
      await runtime.acceptAuthoringFinal(runId, args);
    } else {
      await runtime.completeHostMainResult(runId,args,{accepted:true});
    }
    if (prior) prior.status = accepted ? 'accepted' : 'failed';
    this.entries.delete(entryKey(runId));
    const assertActive = () => { requireValue(this.accepting, 'HOST_MAIN_STOPPED', 'Host Main manager is closed to new work'); assertExecutionAdmission(this.configPath, runId); };
    assertActive();
    const next = await drive.advanceToMain(runId, { control_token: controlToken, owner: record.state.main_actor, request_prefix: `host-main-accept-${runId}`, assertActive });
    assertActive();
    return this.launch({ runtime, drive, handoff: next });
  }

  async fail(entry, cause) {
    const unexpected = !entry.stopping;
    entry.stopping = true; entry.broker?.revoke(); const failures = [cause];
    try {
      const binding = entry.handoff?.host_binding;
      if (binding) {
        requireValue(typeof entry.runtime.failAttemptAfterQuiescence === 'function', 'EXECUTION_COORDINATOR_REQUIRED', 'Host Main failure requires exact cleanup coordination');
        await entry.runtime.failAttemptAfterQuiescence(entry.runId, binding,
          { code: codeOf(cause), message: diagnosticOf(cause) }, { originEntry: entry, originManager: this });
      } else {
        requireValue(typeof entry.runtime.quiesceFailedOrigin === 'function', 'EXECUTION_COORDINATOR_REQUIRED', 'Host Main failure requires local cleanup coordination');
        await entry.runtime.quiesceFailedOrigin(entry);
        if (unexpected && entry.controlToken) await entry.runtime.runs.mutate(entry.runId, 'host_main_advance_failed', state => {
          if (state.status === 'running') {
            state.status = 'failed';
            state.error = { code: 'HOST_MAIN_ADVANCE_FAILED', message: diagnosticOf(cause) };
            state.updated_at = new Date().toISOString();
          }
        });
      }
      if (binding) await entry.runtime.recordExecutorEvent(entry.runId, { ...binding, event: { kind: 'session_state', metadata: { status: 'failed', code: codeOf(cause), diagnostic: diagnosticOf(cause) } } });
    } catch (error) { failures.push(error); }
    entry.status = failures.length === 1 ? 'failed' : 'audit_or_cleanup_failed';
    entry.error = { code: codeOf(cause), diagnostic: diagnosticOf(cause), secondary_codes: failures.slice(1).map(codeOf) };
    this.compact(entry); return publicView(entry);
  }

  compact(entry) {
    if(entry.cleanupPending||entryHasUnconfirmedExecution(entry))return false;
    entry.session = null; entry.broker = null; entry.handoff = null; entry.runtime = null; entry.drive = null; entry.assertActive = null;
    entry.controlToken = null; entry.owner = null; return true;
  }

  fenceRun(runId) {
    const entry = this.entries.get(entryKey(runId));
    if (entry) { entry.stopping = true; entry.broker?.revoke(); }
  }

  fenceAttempt(runId, nodeId, attemptId) {
    const entry = this.entries.get(entryKey(runId));
    if (entry?.handoff?.host_binding?.node_id === nodeId && entry.handoff.host_binding.attempt_id === attemptId) {
      entry.stopping = true; entry.broker?.revoke();
    }
  }

  async stopAttempt(runId, nodeId, attemptId) {
    const entry = this.entries.get(entryKey(runId));
    if (entry?.handoff?.host_binding?.node_id === nodeId && entry.handoff.host_binding.attempt_id === attemptId) await this.stopRun(runId);
  }

  async stopRun(runId) {
    const entry = this.entries.get(entryKey(runId));
    if (!entry || (terminal.has(entry.status) && !entryNeedsRecovery(entry))) return;
    entry.stopping = true; entry.broker?.revoke();
    if (entry.session) try { await entry.session.interrupt?.(); } catch (error) {
      entry.interruptError = { code: codeOf(error), diagnostic: diagnosticOf(error) };
    }
    if (entry.session) try { await entry.session.close(); } catch { entry.cleanupPending = true; }
    const failures = [];
    if (entry.broker) try {
      const outcome = await entry.broker.quiesce();
      requireValue(outcome?.quiescent !== false && entry.broker.isQuiescent?.() !== false,
        'CODEX_BROKER_STOP_UNCONFIRMED','Host Main still owns an unconfirmed Linux execution unit');
    } catch (error) { failures.push(error); }
    if (entry.session) try { await closeSessionForRecovery(entry.session); } catch (error) { failures.push(error); }
    const brokerBeforeSettle = entry.broker; const sessionBeforeSettle = entry.session;
    let taskSettled = false;
    if (!failures.length && !entryHasUnconfirmedExecution(entry)) try { await settleOwnedTask(entry.job); taskSettled = true; } catch (error) { failures.push(error); }
    // executeNode may hand off a session while the bounded job-settlement wait
    // is active.  Re-read the current owner and clean it before deciding that
    // cancellation completed; never overwrite a late cleanup failure.
    if (taskSettled && (entry.broker !== brokerBeforeSettle || entry.session !== sessionBeforeSettle)) {
      entry.broker?.revoke();
      if (entry.session) try { await entry.session.interrupt?.(); } catch (error) {
        entry.interruptError = { code: codeOf(error), diagnostic: diagnosticOf(error) };
      }
      if (entry.broker) try {
        const outcome = await entry.broker.quiesce();
        requireValue(outcome?.quiescent !== false && entry.broker.isQuiescent?.() !== false,
          'CODEX_BROKER_STOP_UNCONFIRMED','Host Main still owns an unconfirmed Linux execution unit');
      } catch (error) { failures.push(error); }
      if (entry.session) try { await closeSessionForRecovery(entry.session); } catch (error) { failures.push(error); }
    }
    entry.cleanupPending = failures.length > 0 || entryHasUnconfirmedExecution(entry);
    if (!entry.cleanupPending) this.compact(entry);
    else throw Object.assign(new AggregateError(failures, `Host Main Run ${runId} retained cleanup ownership`), { code: 'CODEX_EXECUTION_STOP_UNCONFIRMED' });
  }

  async close() {
    this.accepting = false;
    const settled = await Promise.allSettled([...this.entries.keys()].map(runId => this.stopRun(runId)));
    const failures = settled.filter(item => item.status === 'rejected').map(item => item.reason);
    if (failures.length) throw new AggregateError(failures, 'Host Main manager retained cleanup ownership');
    this.hostAuth?.clear();
  }
}
