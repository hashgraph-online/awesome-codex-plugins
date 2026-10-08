import { join, dirname, resolve } from 'node:path';
import { readFile, lstat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { createCodexSession } from './codex-session.mjs';
import { codexStructuredSchema, restoreOptionalOmissions } from './codex-structured-output.mjs';
import { createHostAuthBroker } from './codex-host-auth.mjs';
import { createWorkflowResourceBroker } from './workflow-resource-broker.mjs';
import { waitForManagedLogin } from './codex-managed-login.mjs';
import { qualifiedStrictSettings, validateStrictConfig, codexQualification } from './strict-config.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { validateData } from '../workflow-data-schema.mjs';
import { isEnvironmentDisabled } from '../config.mjs';
import { inspectOrphanProfiles, stopVerifiedOrphan } from './codex-process-ownership.mjs';
import { cleanupCodexProfile } from './codex-profile-builder.mjs';
import { skillPathKey } from './codex-skill-policy.mjs';
import { leaseToken } from '../workflow-execution-envelope.mjs';
import { GENERATED_PROPOSAL_ENVELOPE_SCHEMA, GENERATED_PROPOSAL_ENVELOPE_SCHEMA_V21, GENERATED_REPAIR_ENVELOPE_SCHEMA } from '../skill-import/expansion-run.mjs';
import { targetedSemanticRepairSchema } from '../authoring/blueprint-contract.mjs';
import { AUTHORING_REPAIR_PROMPT, AUTHORING_REPAIR_RESOURCE, AUTHORING_REVIEW_RESOURCE, AUTHORING_REVIEW_INPUTS_RESOURCE, MAX_AUTHORING_REVIEW_RESOURCE_BYTES, authoringReviewIdentity, isAuthoringRunProvenance, authoringDependencyAssessmentRequired } from '../authoring/authoring-workflows.mjs';
import { assertExecutionAdmission, assertExecutionAttemptAdmission, executionAdmissionOpen } from './attempt-admission.mjs';
import { EXECUTOR_RESULT_MAX_BYTES } from '../workflow-run-store.mjs';
import { resolveMainModelSelection } from './main-model-selection.mjs';

const managers = new Map();
async function settleOwnedTask(promise) {
  if (!promise) return;
  let timer; try { await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Object.assign(new Error('Strict task did not settle after confirmed stop'),{code:'STRICT_TASK_STOP_PENDING'})),5000);})]); }
  finally { clearTimeout(timer); }
}
const key = (runId, attemptId) => runId + '/' + attemptId;
const trackedEvents = new Set(['thread/started', 'turn/started', 'turn/completed', 'item/started', 'item/completed', 'error', 'thread/tokenUsage/updated', 'account/login/completed', 'account/updated']);
export function strictOutputByteBudget(repairState=null) {
  if(!repairState?.previous_proposal)return EXECUTOR_RESULT_MAX_BYTES;
  // A targeted patch can replace existing entities and add new ones, but should
  // not stream many multiples of the entire plan it is patching.
  const planBytes=Buffer.byteLength(canonicalJSON(repairState.previous_proposal));
  return Math.min(EXECUTOR_RESULT_MAX_BYTES,Math.max(16*1024,2*planBytes+8*1024));
}
const codeOf = error => typeof error?.code === 'string' && /^[A-Z0-9_]{1,100}$/.test(error.code) ? error.code : 'STRICT_EXECUTOR_FAILED';
const diagnosticOf = error => {
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
};

export function strictManagerFor(options) {
  const id = resolve(options.configPath);
  if (!managers.has(id)) managers.set(id, new StrictSessionManager(options));
  return managers.get(id);
}
export async function closeStrictManagers() {
  const results = await Promise.allSettled([...managers.values()].map(manager => manager.close()));
  const failures = results.filter(result => result.status === 'rejected').map(result => result.reason);
  if (failures.length) throw new AggregateError(failures, 'Strict executor shutdown requires attention');
  managers.clear();
}

// Injected factories are trusted in-process test seams, never JSON/MCP options.
export class StrictSessionManager {
  constructor({ configPath, getConfig, env = process.env, sessionFactory = createCodexSession, qualify = qualifiedStrictSettings, mainModelSelection = resolveMainModelSelection }) {
    this.configPath = resolve(configPath); this.getConfig = getConfig; this.env = env;
    this.sessionFactory = sessionFactory; this.qualify = qualify; this.mainModelSelection = mainModelSelection; this.entries = new Map();
    this.parent = join(dirname(this.configPath), 'strict-profiles');
    this.hostAuth = null; this.hostAuthBinary = null; this.accepting = executionAdmissionOpen(this.configPath);
  }
  async capability(pack, providers, skills = []) {
    const settings = await this.qualify(await this.getConfig(), this.env);
    const pinned = new Set(skills.map(skill => skillPathKey(skill.path)));
    requireValue(pack.workflow.skill_policy.mode === 'strict' && pack.workflow.skill_policy.ambient_allow.every(path => pinned.has(skillPathKey(path))), 'STRICT_SKILL_PIN_UNAVAILABLE', 'Ambient Skill allowances need immutable executor pins');
    for (const node of pack.workflow.nodes) {
      requireValue(!node.fanout, 'STRICT_FANOUT_UNSUPPORTED', `Strict execution cannot run native fan-out for node ${node.id}; use a Cooperative native Provider`);
      if (!['start', 'end', 'condition', 'parallel', 'join', 'human_gate', 'subworkflow'].includes(node.type)) {
        const nativeModel=['agent','skill_ref'].includes(node.type) && (node.executor?.kind === 'main' || node.executor?.kind === 'provider' && providers.find(provider => provider.id === node.executor.provider_id)?.kind === 'native_agent');
        const pinnedHostTool=node.type==='tool' && node.executor?.kind==='tool';
        requireValue(nativeModel || pinnedHostTool, 'STRICT_NODE_UNSUPPORTED', 'Strict execution requires native model nodes, main finalization or pinned Host tool nodes');
      }
      if (node.type === 'skill_ref') requireValue([node.skill_ref.path, ...node.skill_ref.allowed_nested_skills.map(item => item.path)].every(path => pinned.has(skillPathKey(path))), 'STRICT_SKILL_PIN_UNAVAILABLE', 'SkillRef allowance is missing from immutable Run pins');
      requireValue((node.resources ?? []).every(path => pack.resources.some(resource => resource.path === path && resource.bytes <= 1024 * 1024)), 'STRICT_RESOURCE_UNAVAILABLE', 'Node resource is missing or exceeds the qualified text broker limit');
    }
    return settings;
  }
  async prepare(runtime, runId, _args, envelope) {
    requireValue(this.accepting && executionAdmissionOpen(this.configPath), 'STRICT_SESSION_STOPPED', 'Strict manager is closed to new work');
    assertExecutionAdmission(this.configPath, runId);
    const record = await runtime.runs.read(runId), { pins } = record;
    const settings = await this.capability(pins.root, pins.providers, pins.skills);
    requireValue(this.accepting && executionAdmissionOpen(this.configPath), 'STRICT_SESSION_STOPPED', 'Strict manager is closed to new work');
    const main = envelope.executor.kind === 'main';
    const generationReviewer = pins.authoring_reviewer ?? pins.generation?.reviewer ?? null;
    if(generationReviewer) {const current=(await this.getConfig()).providers.find(p=>p.id===generationReviewer.id);requireValue(current?.enabled && current.kind==='native_agent' && current.capabilities.read && canonicalJSON(current.config)===canonicalJSON(generationReviewer.config),'GENERATION_REVIEW_PROVIDER','Review binding must match the registered Provider');}
    requireValue(this.accepting && executionAdmissionOpen(this.configPath), 'STRICT_SESSION_STOPPED', 'Strict manager is closed to new work');
    const selection = main
      ? generationReviewer ? { model: generationReviewer.config.model, effort: generationReviewer.config.reasoning_effort }
        : await this.mainModelSelection(record, settings, { env: this.env })
      : { model: envelope.provider.config.model, effort: envelope.provider.config.reasoning_effort };
    return { execution: 'strict_codex', model: selection.model, effort: selection.effort,
      executable_sha256: settings.binary_sha256, settings_sha256: digest(canonicalJSON(settings)),
      final_acceptance_required: main && envelope.role === 'finalizer', qualification: codexQualification(settings) };
  }
  async launch(runtime, runId, args, { envelope, adapter, prompt }) {
    requireValue(this.accepting && executionAdmissionOpen(this.configPath), 'STRICT_SESSION_STOPPED', 'Strict manager is closed to new work');
    assertExecutionAttemptAdmission(this.configPath, runId, args.node_id, args.attempt_id);
    const id = key(runId, args.attempt_id);
    requireValue(!this.entries.has(id), 'STRICT_SESSION_EXISTS', 'An exact local execution already owns this attempt');
    const entry = { runtime, runId, args: { ...args }, envelope, adapter, prompt, status: 'preparing', session: null, error: null, job: null,
      writes: new Set(), stopping: false, cleanupPending: false, journal: Promise.resolve(), timer: null, assertActive: null };
    entry.preview = { text: '', characters: 0, truncated: false, verified: false, durable: false }; entry.progressAt = 0; entry.outputBytes=0; entry.outputByteBudget=EXECUTOR_RESULT_MAX_BYTES;
    entry.outputHead=''; entry.outputHash=createHash('sha256'); entry.deltaHashes=[];
    let preparationSettled; entry.preparation = new Promise(resolve => { preparationSettled = resolve; });
    this.entries.set(id, entry);
    const event = (kind, metadata) => {
      const next = entry.journal.then(() => runtime.recordExecutorEvent(runId, { ...entry.args, event: { kind, metadata } }));
      entry.journal = next; return next;
    };
    entry.event = event;
    entry.assertActive = () => { requireValue(this.accepting && !entry.stopping, 'STRICT_SESSION_STOPPED', 'Local executor permission was revoked'); assertExecutionAttemptAdmission(this.configPath, runId, args.node_id, args.attempt_id); };
    entry.authorize = async () => {
      entry.assertActive();
      await runtime.execution(runId, args, { allowPaused: entry.status === 'running' });
      entry.assertActive();
      const config = await this.getConfig();
      entry.assertActive();
      const reviewerRecord=await runtime.runs.read(runId),reviewer=reviewerRecord.pins.authoring_reviewer ?? reviewerRecord.pins.generation?.reviewer;
      entry.assertActive();
      if(reviewer && envelope.executor.kind==='main') {const registered=config.providers.find(p=>p.id===reviewer.id);requireValue(registered?.enabled && registered.capabilities.read && (!registered.requires_user_approval || reviewer.requires_user_approval),'GENERATION_REVIEW_PROVIDER','Pinned reviewer permission was revoked');}
      requireValue(config.global.enabled && !isEnvironmentDisabled(this.env), 'CONTROL_DISABLED', 'Workflow execution was disabled');
      requireValue(digest(canonicalJSON(validateStrictConfig(config.strict_executor))) === adapter.settings_sha256, 'STRICT_CONFIG_CHANGED', 'Strict executor settings changed during the attempt');
      if (envelope.provider) {
        const current = config.providers.find(provider => provider.id === envelope.provider.id);
        requireValue(current?.enabled && current.capabilities.read && (envelope.access === 'read_only' || current.capabilities.write), 'PROVIDER_DISABLED', 'Provider permission was revoked');
        requireValue(!current.requires_user_approval || envelope.provider.requires_user_approval, 'PROVIDER_POLICY_CHANGED', 'Provider now requires a new approval');
      }
      entry.assertActive();
    };
    try {
      await entry.authorize();
      const settings = validateStrictConfig((await this.getConfig()).strict_executor);
      entry.settings = settings;
      entry.authenticationMode = settings.authentication.mode;
      const { pins,state } = await runtime.runs.read(runId);
      const resourceObjectRoot = join(runtime.runs.directory(runId), 'objects');
      const resources = await Promise.all(envelope.resources.map(async path => {
        const pin = pins.root.resources.find(item => item.path === path);
        requireValue(pin, 'STRICT_RESOURCE_UNAVAILABLE', 'Node resource is not pinned');
        return { path, sha256: pin.sha256, bytes: await readFile(join(resourceObjectRoot, pin.sha256)) };
      }));
      const allowedSkills = []; const skillResources = [];
      for (const pin of envelope.allowed_skills ?? []) {
        const files = Object.create(null); const prefix = '__skill_pins__/' + digest(pin.path) + '/';
        for (const resource of pin.resources) {
          const bytes = await readFile(join(resourceObjectRoot, resource.sha256)); files[resource.path] = bytes;
          resources.push({ path: prefix + resource.path, sha256: resource.sha256, bytes });
        }
        allowedSkills.push({ source_path: pin.path, source_hash: pin.source_hash, name: pin.name, files });
        skillResources.push({ skill: pin.name, source_path: pin.path, resource_prefix: prefix });
      }
      const generationState=isAuthoringRunProvenance(pins.root.provenance) && args.node_id==='expand' ? state.generation_repair : null;
      entry.outputByteBudget=strictOutputByteBudget(generationState);
      if(generationState){
        requireValue(generationState.previous_proposal && generationState.feedback,'AUTHORING_REPAIR_STATE','Targeted repair needs an exact prior semantic plan and current findings');
        const bytes=Buffer.from(canonicalJSON({contract:'workflow-semantic-repair-context/v1',round:generationState.round,semantic_repair_index:generationState.semantic_repair_index ?? null,feedback:generationState.feedback,user_guidance:generationState.user_guidance ?? null,previous_proposal:generationState.previous_proposal}));
        requireValue(bytes.length<=1024*1024,'AUTHORING_REPAIR_STATE','Targeted repair context exceeds the bounded resource limit');
        entry.repairContext={path:AUTHORING_REPAIR_RESOURCE,sha256:digest(bytes),bytes:bytes.length};
        resources.push({path:AUTHORING_REPAIR_RESOURCE,sha256:entry.repairContext.sha256,bytes});
        await event('repair_context_prepared',entry.repairContext);
      }
      if(isAuthoringRunProvenance(pins.root.provenance) && args.node_id==='final'){
        const proposal=state.nodes.expand?.output?.proposal;
        requireValue(proposal && state.nodes.deterministic_validation?.status==='succeeded','AUTHORING_REVIEW_STATE','Independent review needs the exact validated canonical proposal');
        const inputsSchema=state.generation_projection?.review_inputs_schema;
        requireValue(inputsSchema&&typeof inputsSchema==='object'&&!Array.isArray(inputsSchema),'AUTHORING_REVIEW_STATE','Independent review needs the Host-projected future-Run input schema');
        const bytes=Buffer.from(canonicalJSON(proposal));
        requireValue(bytes.length>0 && bytes.length<=MAX_AUTHORING_REVIEW_RESOURCE_BYTES,'AUTHORING_REVIEW_RESOURCE_LIMIT','Canonical proposal exceeds the bounded independent-review resource limit');
        entry.reviewContext={path:AUTHORING_REVIEW_RESOURCE,sha256:digest(bytes),bytes:bytes.length,...authoringReviewIdentity({state,pins})};
        resources.push({path:AUTHORING_REVIEW_RESOURCE,sha256:entry.reviewContext.sha256,bytes});
        const inputBytes=Buffer.from(canonicalJSON(inputsSchema));
        resources.push({path:AUTHORING_REVIEW_INPUTS_RESOURCE,sha256:digest(inputBytes),bytes:inputBytes});
        await event('review_context_prepared',entry.reviewContext);
      }
      entry.skillResources = skillResources;
      entry.broker = await createWorkflowResourceBroker({ workspace: envelope.workspace, access: envelope.access, allowedPaths: envelope.effective_allowed_paths,
        resources, authorize: entry.authorize,
        onOperation: async metadata => { await event('tool_operation', metadata); },
      });
        if (settings.authentication.mode === 'host_chatgpt' && this.hostAuthBinary !== settings.codex_binary) {
          this.hostAuth?.clear();
          this.hostAuth = createHostAuthBroker({ binary: settings.codex_binary, cwd: this.parent, env: this.env });
          this.hostAuthBinary = settings.codex_binary;
        }
        entry.session = await this.sessionFactory({ parent: this.parent, owner: { run_id: runId, node_id: args.node_id, attempt_id: args.attempt_id },
        hostAuth: settings.authentication.mode === 'host_chatgpt' ? this.hostAuth : undefined,
        binary: settings.codex_binary, expectedBinaryHash: settings.binary_sha256, expectedBinaryPath: adapter.qualification?.resolved_path,
        dynamicToolFormat: adapter.qualification?.dynamic_tool_format, authentication: settings.authentication, model: adapter.model, effort: adapter.effort,
        cwd: envelope.workspace, access: envelope.access, allowedPaths:envelope.effective_allowed_paths, env: this.env, skillPolicy: envelope.skill_policy, allowedSkills, toolBroker: entry.broker, authorize: entry.authorize, assertActive: entry.assertActive,
        onSessionOwned: session => { entry.session = session; },
        onProfilePrepared: profile => event('profile_owned', { home: profile.home, ...(profile.receipt_home ? {receipt_home:profile.receipt_home} : {}), executable_sha256: profile.binary_sha256 }),
        onEvent: metadata => trackedEvents.has(metadata.method) ? event('codex_event', metadata) : undefined,
        onModelCatalog: metadata => event('model_catalog', metadata),
        onOutput: async ({ delta }) => {
          entry.outputBytes+=Buffer.byteLength(delta);
          entry.outputHash.update(delta);
          entry.outputHead=(entry.outputHead+delta).slice(0,2048);
          entry.deltaHashes.push(digest(Buffer.from(delta)));
          if(entry.deltaHashes.length>16)entry.deltaHashes.shift();
          if(entry.outputBytes>entry.outputByteBudget){
            const sample=Buffer.from(canonicalJSON({contract:'strict-output-anomaly/v1',streamed_bytes:entry.outputBytes,budget_bytes:entry.outputByteBudget,stream_sha256:entry.outputHash.copy().digest('hex'),first_characters:entry.outputHead,last_characters:(entry.preview.text+delta).slice(-4096),last_delta_sha256:entry.deltaHashes}));
            const saved=await entry.runtime.runs.saveArtifact(entry.runId,`output-anomaly-${entry.args.attempt_id}`,sample);
            await event('output_anomaly',{...saved,streamed_bytes:entry.outputBytes,budget_bytes:entry.outputByteBudget});
            throw Object.assign(new Error(`Node output exceeded its ${entry.outputByteBudget}-byte budget while streaming; private diagnostic ${saved.artifact} retained`),{code:'STRICT_OUTPUT_BUDGET'});
          }
          entry.preview.characters += delta.length; entry.preview.text = (entry.preview.text + delta).slice(-32768);
          entry.preview.truncated = entry.preview.characters > entry.preview.text.length;
          if (Date.now() - entry.progressAt >= 2000) {
            await event('output_progress', { characters: entry.preview.characters, retained_characters: entry.preview.text.length, truncated: entry.preview.truncated }); entry.progressAt = Date.now();
          }
        },
        onToolRead: metadata => event('skill_read', metadata),
      });
      await entry.authorize();
      entry.assertActive();
      const receipt = { invocation_id: `strict-${args.attempt_id}`, executor: 'codex-app-server', executable_sha256: settings.binary_sha256,
        ...(entry.reviewContext?{authoring_review_context:{proposal_hash:entry.reviewContext.proposal_hash,source_revision:entry.reviewContext.source_revision,expand_attempt_id:entry.reviewContext.expand_attempt_id}}:{}) };
      const record=await runtime.runs.read(runId),definition=record.pins.root.workflow.nodes.find(item=>item.id===args.node_id);
      if(definition?.executor?.kind==='main')await runtime.recordHostMainDispatchReceipt(runId, { ...args, request_id: `dispatch-${args.attempt_id}`, receipt });
      else await runtime.recordDispatchReceipt(runId, { ...args, request_id: `dispatch-${args.attempt_id}`, receipt });
      if (settings.authentication.mode === 'environment_api_key') await entry.session.login({ apiKeyEnv: settings.authentication.api_key_env });
      const authenticated = (await entry.session.authentication()).authenticated;
      requireValue(authenticated || settings.authentication.mode === 'managed_chatgpt', 'HOST_AUTH_UNAVAILABLE', 'Configured authentication is unavailable; no browser login was started');
      entry.status = authenticated ? 'ready' : 'auth_required';
      await event('session_state', { status: entry.status });
      if (authenticated) this.start(entry);
      else {
        entry.timer = setTimeout(() => { entry.job = this.fail(entry, Object.assign(new Error('Managed login deadline expired'), { code: 'CODEX_LOGIN_TIMEOUT' })); }, 600000);
        entry.timer.unref?.();
      }
      return { dispatched: true, receipt, execution_owner: 'strict_codex', session: this.view(entry) };
    } catch (error) {
      await this.fail(entry, error); throw entry.failure;
    } finally { preparationSettled(); }
  }
  view(entry) { return { status: entry.status, error: entry.error, run_id: entry.runId, node_id: entry.args.node_id, attempt_id: entry.args.attempt_id, final_acceptance_required: entry.adapter.final_acceptance_required, output_preview: structuredClone(entry.preview) }; }
  async wait(runId, attemptId) {
    const entry = this.entries.get(key(runId, attemptId));
    requireValue(entry?.runId === runId && entry.args.attempt_id === attemptId,
      'STRICT_SESSION_UNAVAILABLE', 'This exact Strict attempt has no local execution owner');
    const pending = entry.job;
    if (pending) await pending;
    return this.view(entry);
  }
  async find(runtime, runId, args) {
    await runtime.execution(runId, args, { allowInactive: true });
    const entry = this.entries.get(key(runId, args.attempt_id));
    requireValue(entry && entry.args.node_id === args.node_id, 'STRICT_SESSION_UNAVAILABLE', 'Exact local session is absent; inspect its durable receipt/result and reconcile ownership before retry');
    return entry;
  }
  start(entry) {
    entry.assertActive();
    requireValue(!entry.job && !entry.stopping, 'STRICT_SESSION_BUSY', 'A node model turn cannot be submitted twice');
    clearTimeout(entry.timer); entry.status = 'running';
    entry.job = this.execute(entry).then(() => this.view(entry), error => this.fail(entry, error));
  }
  async execute(entry) {
    await entry.authorize(); await entry.event('session_state', { status: 'running' });
    const record=await entry.runtime.runs.read(entry.runId);
    const authoring=isAuthoringRunProvenance(record.pins.root.provenance);
    const generationState=authoring?record.state.generation_repair:null;
    const authoringExpand=authoring && entry.args.node_id==='expand';
    const initialAuthoringSchema=authoringDependencyAssessmentRequired(record.pins.root.workflow.authoring?.contract)?GENERATED_PROPOSAL_ENVELOPE_SCHEMA_V21:GENERATED_PROPOSAL_ENVELOPE_SCHEMA;
    const schema = authoringExpand ? (generationState ? {...GENERATED_REPAIR_ENVELOPE_SCHEMA,properties:{proposal:targetedSemanticRepairSchema(generationState.previous_proposal,generationState.feedback)}} : initialAuthoringSchema) : entry.envelope.outputs_schema;
    const structured = Object.keys(schema).length > 0;
    const constrainedAuthoring=authoringExpand && structured;
    const apiSchema=constrainedAuthoring?codexStructuredSchema(schema):null;
    const prompt = (generationState && authoringExpand ? AUTHORING_REPAIR_PROMPT : entry.prompt) + (entry.skillResources.length ? '\nPinned Skill reference files are available with read_workflow_resource using these exact prefixes (never the original source paths):\n' + canonicalJSON(entry.skillResources) : '') +
      (constrainedAuthoring ? '\nReturn only the JSON value constrained by the API-provided output schema. Use null for inapplicable optional fields; the Host removes those placeholders.' : structured ? '\nReturn only a JSON value matching this success output schema: ' + canonicalJSON(schema) : '') +
      (constrainedAuthoring ? '\nConversion/planning analyzes the pinned source data and does not require executing that source.' : '\nIf this node cannot produce its required result because a prerequisite, capability, answer or verification is missing, return exactly {"$workflow_blocked":"specific reason, up to 2000 characters"}. This reserved failure response overrides the success schema and fails the node; never return a normal successful report of a blocker. Conversion/planning analyzes source data and does not require executing that source.');
    const maxPrompt=(await this.getConfig()).global.max_prompt_chars;
    requireValue(prompt.length<=maxPrompt,'PROMPT_LIMIT','Final node prompt exceeds the configured prompt limit after strict output and Skill contracts are attached');
    const result = await entry.session.turn(prompt, { timeout_ms: entry.settings.inactivity_timeout_ms, explicit_sources: entry.envelope.skill_ref ? [entry.envelope.skill_ref.path] : [], ...(constrainedAuthoring?{output_schema:apiSchema}:{}) });
    requireValue(Buffer.byteLength(result.output)<=entry.outputByteBudget,'STRICT_OUTPUT_BUDGET',`Node result exceeded its ${entry.outputByteBudget}-byte budget`);
    let candidate;
    try { candidate=JSON.parse(result.output); }
    catch { if(structured) throw Object.assign(new Error('Model result is not the required JSON value'),{code:'STRICT_OUTPUT_JSON'}); /* Ordinary unstructured text is valid. */ }
    if(candidate && typeof candidate==='object' && Object.hasOwn(candidate,'$workflow_blocked')) {
      requireValue(!Array.isArray(candidate)&&Object.keys(candidate).length===1&&typeof candidate.$workflow_blocked==='string'&&candidate.$workflow_blocked.trim()&&candidate.$workflow_blocked.length<=2000,'STRICT_BLOCKER_SCHEMA','A blocked response must contain only a nonempty bounded $workflow_blocked reason');
      throw Object.assign(new Error(candidate.$workflow_blocked),{code:'WORKFLOW_NODE_BLOCKED'});
    }
    const output=structured?(constrainedAuthoring?restoreOptionalOmissions(candidate,schema):candidate):{text:result.output};
    validateData(output, schema);
    await entry.session.close(); await entry.event('session_state', { status: 'closed' });
    await entry.authorize();
    const completion = { status: 'succeeded', summary: 'Node result recorded', structured_output: output,
      artifacts: [], evidence: [{ kind: 'strict_codex_result', thread_id: result.thread_id, turn_id: result.turn_id, audit: result.audit }],
      changed_paths: [...entry.writes].sort(), outside_paths: [] };
    const saved = await entry.runtime.runs.saveExecutorResult(entry.runId, entry.args.attempt_id, completion);
    await entry.event('result_proposed', { ...saved, final_acceptance_required: entry.adapter.final_acceptance_required,
      ...(entry.reviewContext?{proposal_hash:entry.reviewContext.proposal_hash,source_revision:entry.reviewContext.source_revision,expand_attempt_id:entry.reviewContext.expand_attempt_id}:{}) });
    entry.resultSaved = true;
    entry.status = entry.adapter.final_acceptance_required ? 'awaiting_main_acceptance' : 'result_ready';
    if (!entry.adapter.final_acceptance_required) {
      await entry.runtime.completeNode(entry.runId, { ...entry.args, completion }); entry.status = 'succeeded';
    }
    this.#compactSettledEntry(entry);
  }
  async fail(entry, cause) {
    entry.stopping = true; clearTimeout(entry.timer); entry.broker?.revoke();
    const failures = [cause];
    const code = codeOf(cause);
    try {
      const diagnostic = diagnosticOf(cause);
      requireValue(typeof entry.runtime.failAttemptAfterQuiescence === 'function', 'EXECUTION_COORDINATOR_REQUIRED', 'Strict failure requires exact cleanup coordination');
      await entry.runtime.failAttemptAfterQuiescence(entry.runId, entry.args,
        { code, message: code === 'WORKFLOW_NODE_BLOCKED' ? cause.message : diagnostic },
        { originEntry: entry, originManager: this, commitFailure: !entry.resultSaved });
      await entry.event('session_state', { status: 'failed', code, diagnostic });
    } catch (error) { failures.push(error); }
    entry.status = failures.length === 1 ? entry.resultSaved ? 'result_commit_failed' : 'failed' : 'audit_or_cleanup_failed';
    entry.error = { code, secondary_codes: failures.slice(1).map(codeOf) };
    entry.failure = failures.length === 1 ? cause : Object.assign(new AggregateError(failures, 'Strict execution and audit/cleanup failed'), { code: 'STRICT_FAILURE_INCOMPLETE' });
    this.#compactSettledEntry(entry);
    // Background failures become an explicit observable outcome, never a dropped rejection.
    return this.view(entry);
  }
  async login(runtime, runId, args) {
    const entry = await this.find(runtime, runId, args); await entry.authorize();
    requireValue(entry.authenticationMode === 'managed_chatgpt', 'STRICT_LOGIN_MODE', 'Browser login is available only in explicit managed_chatgpt mode');
    requireValue(entry.status === 'auth_required' && !entry.job, 'STRICT_LOGIN_STATE', 'This exact session is not awaiting managed login');
    clearTimeout(entry.timer); entry.status = 'auth_pending'; const after = entry.session.client.events.length;
    let login;
    try { login = await entry.session.login(); await entry.event('session_state', { status: entry.status }); }
    catch (error) { await this.fail(entry, error); throw entry.failure; }
    entry.job = waitForManagedLogin(entry.session.client, login.login_id, { after }).then(async () => {
      await entry.authorize(); entry.status = 'ready'; entry.job = null; this.start(entry); return this.view(entry);
    }).catch(error => this.fail(entry, error));
    // Human-authenticated console only. Never return this through a worker MCP tool.
    return { ...this.view(entry), auth_url: login.auth_url };
  }
  async status(runtime, runId, args) { return this.view(await this.find(runtime, runId, args)); }
  async cleanupOrphans(runtime, runId, args) {
    await runtime.execution(runId, args, { allowInactive: true });
    const state = await runtime.get(runId);
    requireValue(!['claimed', 'running'].includes(state.nodes[args.node_id].status), 'STRICT_RECOVERY_ACTIVE', 'Fence the interrupted attempt before orphan cleanup');
    const cleaned = []; const blocked = [];
    let records;
    try { records = await inspectOrphanProfiles(this.parent); }
    catch (error) { if (error.code !== 'ENOENT') throw error; return { cleaned, blocked }; }
    for (const record of records) {
      if (record.status === 'blocked') { blocked.push({ home: record.home, code: record.code }); continue; }
      const ownerPath = join(record.home, 'owner.json'); const stat = await lstat(ownerPath);
      requireValue(stat.isFile() && stat.size <= 64000, 'PROFILE_OWNER', 'Profile ownership record must be bounded');
      const owner = JSON.parse(await readFile(ownerPath, 'utf8'));
      if (owner.owner?.run_id !== runId || owner.owner?.node_id !== args.node_id || owner.owner?.attempt_id !== args.attempt_id) continue;
      if (record.status === 'active') { blocked.push({ home: record.home, code: 'PROFILE_OWNER_ACTIVE' }); continue; }
      await stopVerifiedOrphan(record);
      await cleanupCodexProfile({ parent: this.parent, home: record.home, owner_token: record.token });
      await runtime.recordExecutorEvent(runId, { ...args, event: { kind: 'session_state', metadata: { status: 'closed' } } });
      cleaned.push(record.home);
    }
    return { cleaned, blocked, resubmitted: false };
  }
  async collect(runtime, runId, args) {
    const envelope = await runtime.execution(runId, args, { allowInactive: true });
    const state = await runtime.get(runId); const attempt = state.nodes[args.node_id].attempts.find(item => item.id === args.attempt_id);
    requireValue(!['failed','interrupted','cancelled'].includes(attempt.status), attempt.error?.code ?? 'STRICT_EXECUTOR_FAILED', attempt.error?.message ?? 'Strict execution terminated; do not keep polling for a result', {node_status:state.nodes[args.node_id].status,attempt_status:attempt.status,error:attempt.error});
    requireValue(attempt.result_proposal, 'STRICT_RESULT_PENDING', 'No durable result proposal exists for this attempt');
    const completion = await runtime.runs.readExecutorResult(runId, args.attempt_id, attempt.result_proposal.sha256);
    const record=await runtime.runs.read(runId),authoringFinal=isAuthoringRunProvenance(record.pins.root.provenance)&&args.node_id===record.pins.root.workflow.finalization.node_id;
    if(authoringFinal){
      const expected=authoringReviewIdentity(record),proposed={proposal_hash:attempt.result_proposal.proposal_hash,source_revision:attempt.result_proposal.source_revision,expand_attempt_id:attempt.result_proposal.expand_attempt_id};
      requireValue(canonicalJSON(proposed)===canonicalJSON(expected)&&canonicalJSON(attempt.dispatch?.receipt?.authoring_review_context)===canonicalJSON(expected),'AUTHORING_REVIEW_IDENTITY','Collected reviewer result is not bound to the current canonical proposal');
    }
    if (envelope.role === 'finalizer') {
      if (args.accepted !== true) return { final_acceptance_required: true, completion };
      completion.acceptance = { accepted: true };
      if(authoringFinal){
        requireValue(false,'AUTHORING_HUMAN_ACCEPTANCE_REQUIRED','Authoring finalization must use the checklist-gated accept_authoring action');
      }
    }
    if(envelope.executor?.kind==='main')return runtime.completeHostMainResult(runId,args,{accepted:args.accepted});
    return runtime.completeNode(runId, { ...args, completion });
  }
  async acceptAuthoring(runtime,runId,args){
    const envelope=await runtime.execution(runId,args,{allowInactive:true});
    requireValue(envelope.role==='finalizer','AUTHORING_HUMAN_ACCEPTANCE_REQUIRED','Authoring acceptance requires the final reviewer attempt');
    const record=await runtime.runs.read(runId),attempt=record.state.nodes[args.node_id]?.attempts.find(item=>item.id===args.attempt_id);
    requireValue(isAuthoringRunProvenance(record.pins.root.provenance)&&args.node_id===record.pins.root.workflow.finalization.node_id,'AUTHORING_HUMAN_ACCEPTANCE_REQUIRED','This attempt is not an authoring final review');
    requireValue(attempt?.result_proposal,'STRICT_RESULT_PENDING','No durable reviewer result exists for this attempt');
    const expected=authoringReviewIdentity(record),proposed={proposal_hash:attempt.result_proposal.proposal_hash,source_revision:attempt.result_proposal.source_revision,expand_attempt_id:attempt.result_proposal.expand_attempt_id};
    requireValue(canonicalJSON(proposed)===canonicalJSON(expected)&&canonicalJSON(attempt.dispatch?.receipt?.authoring_review_context)===canonicalJSON(expected),'AUTHORING_REVIEW_IDENTITY','Accepted reviewer result is not bound to the current canonical proposal');
    return runtime.acceptAuthoringFinal(runId,{...args,control_token:args.control_token});
  }
  fenceRun(runId) {
    for (const entry of this.entries.values()) if (entry.runId === runId) {
      entry.stopping = true; entry.broker?.revoke();
    }
  }

  fenceAttempt(runId, nodeId, attemptId) {
    const entry = this.entries.get(key(runId, attemptId));
    if (entry?.args.node_id === nodeId) { entry.stopping = true; entry.broker?.revoke(); }
  }

  async stopAttempt(runId, nodeId, attemptId) {
    const entry = this.entries.get(key(runId, attemptId));
    if (entry?.args.node_id === nodeId) await this.stop(entry);
  }

  async stopRun(runId) {
    const results = await Promise.allSettled([...this.entries.values()].filter(entry => entry.runId === runId).map(entry => this.stop(entry)));
    const failures = results.filter(result => result.status === 'rejected').map(result => result.reason);
    if (failures.length) throw new AggregateError(failures, 'Some Strict sessions did not shut down cleanly');
  }
  async stopRecovered(runId, authority) {
    for (const entry of this.entries.values()) if (entry.runId === runId) {
      entry.stopping = true; entry.broker?.revoke();
      const attempt = authority.state.nodes[entry.args.node_id]?.attempts.find(item => item.id === entry.args.attempt_id);
      requireValue(attempt, 'STRICT_RECOVERY_IDENTITY', 'Owned session does not match a recovered attempt');
      entry.args = { ...entry.args, control_token: authority.control_token,
        lease_token: leaseToken(authority.control_token, runId, entry.args.node_id, attempt.id, attempt.lease_generation ?? 0) };
    }
    await this.stopRun(runId);
  }
  async stop(entry) {
    if (entry.status === 'stopped') return;
    entry.stopping = true; clearTimeout(entry.timer); entry.broker?.revoke();
    let timer;
    try {
      await Promise.race([entry.preparation, new Promise((_, reject) => { timer = setTimeout(() => reject(Object.assign(new Error('Strict setup is still stopping; cancellation remains pending'), { code: 'STRICT_SETUP_STOP_PENDING' })), 5000); })]);
    } finally { clearTimeout(timer); }
    if (entry.session) { await entry.session.close(); entry.cleanupPending = false; await entry.event('session_state', { status: 'closed' }); }
    if (entry.job) try { await settleOwnedTask(entry.job); } catch (error) { entry.cleanupPending = true; throw error; }
    if (!['failed', 'result_commit_failed', 'audit_or_cleanup_failed'].includes(entry.status)) entry.status = 'stopped';
    this.#compactSettledEntry(entry);
  }

  #compactSettledEntry(entry) {
    if (entry.compacted) return;
    if (entry.cleanupPending || entry.broker?.isQuiescent?.() === false) return;
    // Status, exact attempt identity and final-acceptance policy remain local;
    // heavyweight session, broker, prompt and pinned envelope references do not.
    // Durable Run artifacts are the source of truth for later collection.
    if (!['succeeded', 'result_ready', 'awaiting_main_acceptance', 'failed', 'result_commit_failed', 'audit_or_cleanup_failed', 'stopped'].includes(entry.status)) return;
    const finalAcceptanceRequired = Boolean(entry.adapter?.final_acceptance_required);
    entry.session = null;
    entry.broker = null;
    entry.prompt = null;
    entry.envelope = null;
    entry.authorize = null;
    entry.assertActive = null;
    entry.event = null;
    entry.runtime = null;
    entry.writes = new Set();
    entry.job = null;
    entry.skillResources = null;
    entry.adapter = { final_acceptance_required: finalAcceptanceRequired };
    entry.journal = Promise.resolve();
    entry.compacted = true;
  }
  async close() {
    this.accepting = false;
    const entries = [...this.entries.values()];
    for (const entry of entries) { entry.stopping = true; clearTimeout(entry.timer); entry.broker?.revoke(); }
    try {
      const settled = await Promise.allSettled(entries.map(entry => this.stop(entry)));
      const failures = settled.filter(item => item.status === 'rejected').map(item => item.reason);
      if (failures.length) throw new AggregateError(failures, 'Strict manager retained one or more exact executions');
    } finally { this.hostAuth?.clear(); }
  }
}
