import { delimiter, dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { readFile } from 'node:fs/promises';
import { createManagedNativeSession } from './managed-native-session.mjs';
import { createHostAuthBroker } from './codex-host-auth.mjs';
import { createWorkflowResourceBroker, loadNodeSkillSnapshots } from './workflow-resource-broker.mjs';
import {rejectWorkspaceScope} from './workspace-scope-evidence.mjs';
import {snapshotWorkspace, changedWorkspacePaths as changedPaths} from './workspace-snapshot.mjs';
import { qualifiedStrictSettings, codexQualification } from './strict-config.mjs';
import { managedNativeResultSchema, hostCompletionEnvelope, strictAgentOutputSchema, hostNodeTurnSchema, hostNodeTurnResult } from './host-main-automation.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { isEnvironmentDisabled } from '../config.mjs';
import { compactCodexResultEvidence, persistCodexCommandAudits } from './codex-result-evidence.mjs';
import { assertExecutionAttemptAdmission, executionAdmissionOpen } from './attempt-admission.mjs';
import { assignFanoutItems, assignedFanoutIndices, assignedFanoutWritePaths, projectFanoutInputs } from './fanout-input-projection.mjs';
import { nativeAgentResultSchema } from './native-agent-bridge.mjs';
import { materializeNodeInputs } from './node-input-materials.mjs';
import { pathBoundaries } from '../workflow-bindings.mjs';

const managers = new Map();
const entryKey = (runId, attemptId) => `${runId}/${attemptId}`;
const codeOf = error => typeof error?.code === 'string' && /^[A-Z0-9_]{1,100}$/.test(error.code) ? error.code : 'MANAGED_NATIVE_FAILED';
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

function within(path, boundary) { return boundary === '.' || path === boundary || path.startsWith(boundary.replaceAll('\\', '/').replace(/\/$/, '') + '/'); }
function augmentedEnvironment(env, runtimeEnvironment) {
  const directories = (runtimeEnvironment?.tools ?? []).filter(tool => tool.status === 'found' && typeof tool.path === 'string' && isAbsolute(tool.path)).map(tool => dirname(tool.path));
  const inherited = env.PATH ?? env.Path ?? '';
  return { ...env, PATH: [...new Set([...directories, ...inherited.split(delimiter).filter(Boolean)])].join(delimiter) };
}
function poolAssignments(subagents, accepted = {}) {
  if (!subagents?.fanout) return null;
  const { resolved_count: count, items, fanout } = subagents;
  const raw=assignFanoutItems(items,fanout,count),plan={count,items,assignments:raw};
  return raw.map((_assigned,index)=>{
    const item_indices=assignedFanoutIndices(plan,fanout,index).filter(itemIndex=>!accepted[itemIndex]);
    return {index,item_indices,items:item_indices.map(itemIndex=>items[itemIndex])};
  }).filter(assignment=>assignment.item_indices.length);
}
export async function runAssignedPool(assignments, maxConcurrency, run) {
  requireValue(Number.isSafeInteger(maxConcurrency) && maxConcurrency > 0, 'SUBAGENT_FANOUT_CONCURRENCY', 'Managed fan-out concurrency must be a positive integer');
  const results = new Array(assignments.length);
  const failures = [];
  let next = 0;
  const workers = Array.from({ length: Math.min(maxConcurrency, assignments.length) }, async () => {
    while (next < assignments.length) {
      const index = next++;
      try { results[index] = await run(assignments[index]); }
      catch (error) { failures.push(Object.assign(error,{assignment_index:index})); }
    }
  });
  await Promise.all(workers);
  if (failures.length) throw Object.assign(new AggregateError(failures, 'One or more managed fan-out sub-Agents failed'), { code: 'MANAGED_NATIVE_POOL_FAILED' });
  return results;
}
function aggregateUsage(results) {
  if (results.length === 0) return { unknown: false, cost_micros: 0 };
  const fields = ['input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens', 'visual_input_units', 'cost_micros'];
  const usage = { unknown: results.some(item => item.result.usage?.unknown !== false) };
  for (const field of fields) {
    const values = results.map(item => item.result.usage?.[field]).filter(Number.isSafeInteger);
    if (values.length) usage[field] = values.reduce((total, value) => total + value, 0);
  }
  return usage;
}
function fanoutResultSchema(definition, fanout) {
  const properties = definition.outputs_schema?.properties ?? {}, result = properties[fanout.result_output];
  requireValue(result?.type === 'array' && result.items, 'SUBAGENT_FANOUT_RESULT', 'Managed fan-out needs an item schema for its declared result list');
  return strictAgentOutputSchema({ type: 'object', properties: { result: structuredClone(result.items) }, required: ['result'], additionalProperties: false });
}

function perItemTurn(output) {
  let value;
  try { value=JSON.parse(output); }
  catch { return {category:'invalid',reason:'Managed native per-item final answer is not JSON'}; }
  if(value?.outcome==='blocked' && typeof value.block_reason==='string' && value.block_reason.trim())
    return {category:'blocked',reason:value.block_reason};
  if(value?.outcome==='completed' && Object.hasOwn(value,'result'))value=value.result;
  else if(value && typeof value==='object' && !Array.isArray(value) &&
    ['outcome','result','block_reason'].some(key=>Object.hasOwn(value,key)))
    return {category:'invalid',reason:'Managed native per-item final answer has no valid completion envelope'};
  return {value};
}

function perItemDiagnostic(issues) {
  const summary=issues.map(item=>({category:item.category,reason:item.reason}));
  const full=canonicalJSON(summary);
  if(full.length<=4096)return full;
  const first=canonicalJSON(summary[0]);
  return `First of ${issues.length} item issues: ${first.slice(0,3500)}`;
}

function combineTurnUsage(turns) {
  const fields=['input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens','visual_input_units','cost_micros'];
  const usage={unknown:turns.some(turn=>turn.usage?.unknown!==false)};
  for(const field of fields){const values=turns.map(turn=>turn.usage?.[field]).filter(Number.isSafeInteger);
    if(values.length)usage[field]=values.reduce((sum,value)=>sum+value,0);}
  return usage;
}
async function resourceItems(runtime, runId, envelope) {
  if (!envelope.resources.length) return [];
  const record = await runtime.runs.read(runId); const root = join(runtime.runs.directory(runId), 'objects');
  const resources = [];
  for (const path of envelope.resources) {
    const pin = record.pins.root.resources.find(item => item.path === path);
    requireValue(pin && pin.bytes <= 1024 * 1024, 'MANAGED_NATIVE_RESOURCE', `Pinned resource is unavailable or too large: ${path}`);
    resources.push({ path, sha256: pin.sha256, bytes: await readFile(join(root, pin.sha256)) });
  }
  return resources;
}

export function managedNativeManagerFor(options) {
  const id = resolve(options.configPath);
  if (!managers.has(id)) managers.set(id, new ManagedNativeManager(options));
  return managers.get(id);
}
export async function closeManagedNativeManagers() {
  const settled = await Promise.allSettled([...managers.entries()].map(async ([id,manager]) => { await manager.close(); managers.delete(id); }));
  const failures = settled.filter(item => item.status === 'rejected').map(item => item.reason);
  if (failures.length) throw new AggregateError(failures, 'Managed native shutdown requires attention');
}

const entryBrokers = entry => [...new Set([entry.broker,...(entry.brokers ?? [])].filter(Boolean))];
const entrySessions = entry => [...new Set([...(entry.sessions ?? []),entry.session].filter(Boolean))];
const entryNeedsRecovery = entry => entry.cleanupPending === true || entryBrokers(entry).some(broker => broker.isQuiescent?.() === false);
async function settleOwnedTask(promise) {
  if (!promise) return;
  let timer; try { await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Object.assign(new Error('Managed native task did not settle after confirmed stop'),{code:'MANAGED_NATIVE_STOP_PENDING'})),5000);})]); }
  finally { clearTimeout(timer); }
}
async function closeSessionForRecovery(session) {
  try { await session.close(); }
  catch (first) {
    try { await session.close(); }
    catch (second) { throw new AggregateError([first,second], 'Managed native session cleanup retry failed'); }
  }
}
async function interruptOwnedSessions(sessions) {
  const pending=sessions.map(session=>{
    try{return Promise.resolve(session.interrupt?.());}
    catch(error){return Promise.reject(error);}
  });
  return (await Promise.allSettled(pending)).filter(item=>item.status==='rejected').map(item=>item.reason);
}
async function quiesceBrokerForRecovery(broker) {
  const outcome = await broker.quiesce();
  requireValue(outcome?.quiescent !== false && broker.isQuiescent?.() !== false,
    'CODEX_BROKER_STOP_UNCONFIRMED','Managed bound execution still owns an unconfirmed Linux unit');
}

export class ManagedNativeManager {
  constructor({ configPath, getConfig, env = process.env, sessionFactory = createManagedNativeSession, qualify = qualifiedStrictSettings }) {
    this.configPath = resolve(configPath); this.getConfig = getConfig; this.env = env; this.sessionFactory = sessionFactory; this.qualify = qualify;
    this.parent = join(dirname(this.configPath), 'managed-native-profiles'); this.entries = new Map(); this.hostAuth = null; this.hostAuthBinary = null; this.accepting = executionAdmissionOpen(this.configPath);
  }
  async prepare(_runtime, _runId, _args, envelope) {
    requireValue(this.accepting && executionAdmissionOpen(this.configPath), 'MANAGED_NATIVE_STOPPED', 'Managed native manager is closed to new work');
    requireValue(envelope.skill_policy.mode === 'cooperative' && envelope.provider?.kind === 'native_agent', 'MANAGED_NATIVE_NODE', 'Managed native execution requires a cooperative native Provider node');
    const settings = await this.qualify(await this.getConfig(), this.env, { scope: 'managed_native' });
    requireValue(this.accepting && executionAdmissionOpen(this.configPath), 'MANAGED_NATIVE_STOPPED', 'Managed native manager is closed to new work');
    return { execution: 'managed_native_codex', model: envelope.provider.config.model, effort: envelope.provider.config.reasoning_effort,
      executable_sha256: settings.binary_sha256, settings, qualification: codexQualification(settings), final_acceptance_required: false };
  }
  async launch(runtime, runId, args, prepared) {
    requireValue(this.accepting && executionAdmissionOpen(this.configPath), 'MANAGED_NATIVE_STOPPED', 'Managed native manager is closed to new work');
    assertExecutionAttemptAdmission(this.configPath, runId, args.node_id, args.attempt_id);
    const id = entryKey(runId, args.attempt_id);
    requireValue(!this.entries.has(id), 'MANAGED_NATIVE_EXISTS', 'An exact managed child already owns this attempt');
    const current=await runtime.runs.read(runId);
    const currentAttempt=current.state.nodes?.[args.node_id]?.attempts?.find(item=>item.id===args.attempt_id);
    const assignments = poolAssignments(prepared.envelope.subagents,currentAttempt?.native_item_results);
    requireValue(assignments || !prepared.envelope.subagents || prepared.envelope.subagents.resolved_count === 1, 'SUBAGENT_POOL_JOIN', 'Managed multi-Agent execution requires an explicit runtime fan-out and join contract');
    const dispatchIds = new Map((assignments??[]).map(({index})=>[index,`managed-${args.attempt_id}-${String(index + 1).padStart(3, '0')}`]));
    const entry = { runtime, runId, args: { ...args }, prepared, assignments, dispatchIds, session: null, sessions: [], broker: null, brokers: [], authorize: null, assertActive: null, status: 'preparing', stopping: false, cleanupPending: false, error: null, job: null, writes: new Set() };
    const assertAdmission = () => { requireValue(this.accepting && !entry.stopping, 'MANAGED_NATIVE_STOPPED', 'Managed node permission was revoked'); assertExecutionAttemptAdmission(this.configPath, runId, args.node_id, args.attempt_id); };
    entry.assertActive = assertAdmission;
    this.entries.set(id, entry);
    const receipt = { invocation_id: `managed-${args.attempt_id}`, executor: 'codex-app-server-managed-native', model: prepared.adapter.model, effort: prepared.adapter.effort, executable_sha256: prepared.adapter.executable_sha256,
      ...(assignments ? { subagent_dispatch_ids: assignments.map(assignment=>dispatchIds.get(assignment.index)),
        subagent_plan:{resolved_count:assignments.length,input_sha256:digest(canonicalJSON(prepared.envelope.subagents.items)),
          assignments:assignments.map(assignment=>({...(prepared.envelope.subagents.fanout.result_mode==='per_item'?{assignment_index:assignment.index}:{}),
            dispatch_id:dispatchIds.get(assignment.index),items_sha256:digest(canonicalJSON(assignment.items))}))} } : {}) };
    const recorded = runtime.recordDispatchReceipt(runId, { ...args, request_id: `dispatch-${args.attempt_id}`, receipt });
    entry.job = recorded.then(() => { assertAdmission(); return this.execute(entry); }).catch(error => this.fail(entry, error));
    entry.done = entry.job;
    await recorded;
    assertAdmission();
    return { dispatched: true, receipt, completed: false, managed: true, execution_owner: 'managed_native_codex' };
  }
  async wait(runId, attemptId) {
    const entry = this.entries.get(entryKey(runId, attemptId));
    requireValue(entry?.done, 'MANAGED_NATIVE_UNAVAILABLE', 'The exact managed child lifecycle is unavailable');
    return entry.done;
  }
  async execute(entry) {
    const { runtime, runId, args, prepared } = entry; const { envelope, adapter } = prepared;
    const record = await runtime.runs.read(runId);
    const definition = record.pins.root.workflow.nodes.find(node => node.id === args.node_id);
    requireValue(definition, 'NODE_MISSING', 'Managed native node is absent from the pinned Workflow');
    const event = (kind, metadata) => runtime.recordExecutorEvent(runId, { ...args, event: { kind, metadata } });
    const assignmentWritePaths=new Map(entry.assignments?.map(assignment=>[assignment.index,assignedFanoutWritePaths({workspace:envelope.workspace,
      nodeAllowedPaths:envelope.effective_allowed_paths,assignedItems:assignment.items,fanout:definition.fanout})]) ?? [[0,envelope.effective_allowed_paths]]);
    const observedWritePaths=pathBoundaries([...assignmentWritePaths.values()].flat());
    const snapshot = (phase = 'completion') => snapshotWorkspace(envelope.workspace, {access: envelope.access, allowedPaths: observedWritePaths,
      requiredPaths: (definition.required_artifacts ?? []).map(item => item.path), codePrefix: 'MANAGED_NATIVE',
      onUnreadable: metadata => event('workspace_unreadable_authorized_path', {...metadata, phase})});
    entry.authorize = async () => {
      entry.assertActive();
      await runtime.execution(runId, args, { allowPaused: entry.status === 'running' });
      entry.assertActive();
      const config = await this.getConfig();
      entry.assertActive();
      requireValue(config.global.enabled && !isEnvironmentDisabled(this.env), 'CONTROL_DISABLED', 'Workflow execution was disabled');
      const current = config.providers.find(provider => provider.id === envelope.provider.id);
      requireValue(current?.enabled && current.capabilities.read && (envelope.access === 'read_only' || current.capabilities.write), 'PROVIDER_DISABLED', 'Provider permission was revoked');
      requireValue(!current.requires_user_approval || envelope.provider.requires_user_approval, 'PROVIDER_POLICY_CHANGED', 'Provider now requires a new approval');
      requireValue(canonicalJSON(current.config) === canonicalJSON(envelope.provider.config), 'PROVIDER_CONFIG_CHANGED', 'Managed Provider configuration changed during the attempt');
      entry.assertActive();
    };
    await entry.authorize();
    requireValue(/^[A-Za-z0-9-]{1,128}$/.test(runId)&&/^[A-Za-z0-9-]{1,128}$/.test(args.attempt_id),
      'MANAGED_NATIVE_INPUT_PATH','Managed input material identity is not a safe Run/attempt path');
    const inputRoot=join(envelope.workspace,'work','.workflow-runtime','managed-native',runId,args.attempt_id);
    const materialFor=async (index,scopedInputs,directory=join(inputRoot,`partition-${index}`))=>{
      entry.assertActive();
      const material=await materializeNodeInputs({directory,
        envelope:{...envelope,inputs:scopedInputs}});
      entry.assertActive();
      await event('node_input_materials',{index,inputs_path:material.inputs_path,
        prompt_sha256:material.prompt_sha256,input_count:material.manifest.length,
        manifest_sha256:digest(canonicalJSON(material.manifest))});
      return material;
    };
    const materials=new Map(entry.assignments
      ? await Promise.all(entry.assignments.map(async assignment=>[assignment.index,await materialFor(assignment.index,
        projectFanoutInputs(envelope.inputs,envelope.subagents.items,
          definition.fanout?.item_delivery==='incremental'?assignment.items.slice(0,1):assignment.items))]))
      : [[0,await materialFor(0,envelope.inputs)]]);
    const before = await snapshot('before');
    const resources = await resourceItems(runtime, runId, envelope);
    const allowedSkills = await loadNodeSkillSnapshots(runtime, runId, envelope);
    const brokerFor = async index => {
      const broker = await createWorkflowResourceBroker({
        workspace: envelope.workspace, access: envelope.access, allowedPaths: assignmentWritePaths.get(index),
        resources, authorize: entry.authorize,
        onOperation: async metadata => { const call_id = `${index + 1}:${String(metadata.call_id).slice(0, 240)}`; await event('tool_operation', { ...metadata, call_id }); },
      });
      entry.brokers.push(broker);
      await event('tool_capabilities', { access: envelope.access, tools: broker.tools().map(tool => tool.name).join(','),
        allowed_paths_count:assignmentWritePaths.get(index).length,allowed_paths_sha256:digest(canonicalJSON(assignmentWritePaths.get(index))) });
      return broker;
    };
    if (adapter.settings.authentication.mode === 'host_chatgpt' && this.hostAuthBinary !== adapter.settings.codex_binary) {
      this.hostAuth?.clear(); this.hostAuth = createHostAuthBroker({ binary: adapter.settings.codex_binary, cwd: this.parent, env: this.env }); this.hostAuthBinary = adapter.settings.codex_binary;
    }
    const env = augmentedEnvironment(this.env, record.state.runtime_environment ?? record.state.constraints?.runtime_environment);
    entry.status = 'running'; await event('session_state', { status: 'running' });
    const sessionFor = async (index, dispatchId) => {
      const broker = await brokerFor(index);
      const session = await this.sessionFactory({
        parent: this.parent, owner: { run_id: runId, node_id: args.node_id, attempt_id: dispatchId },
        hostAuth: adapter.settings.authentication.mode === 'host_chatgpt' ? this.hostAuth : undefined,
        binary: adapter.settings.codex_binary, expectedBinaryHash: adapter.settings.binary_sha256, expectedBinaryPath: adapter.qualification?.resolved_path,
        dynamicToolFormat: adapter.qualification?.dynamic_tool_format, authentication: adapter.settings.authentication,
        model: adapter.model, effort: adapter.effort, cwd: envelope.workspace, access: envelope.access, allowedPaths:assignmentWritePaths.get(index), env, toolBroker: broker, authorize: entry.authorize, assertActive: entry.assertActive,
        maxTurns: definition.fanout?.result_mode==='per_item'
          ? definition.retry.max_attempts+(definition.fanout.item_delivery==='incremental'
            ? entry.assignments.find(assignment=>assignment.index===index).item_indices.length-1 : 0) : 1,
        skillPolicy: envelope.skill_policy, allowedSkills,
        onSessionOwned: session => { if (!entry.sessions.includes(session)) entry.sessions.push(session); },
        onProfilePrepared: profile => event('profile_owned', { home: profile.home, ...(profile.receipt_home ? {receipt_home:profile.receipt_home} : {}), executable_sha256: profile.binary_sha256 }),
        onModelCatalog: metadata => event('model_catalog', metadata),
        onEvent: metadata => {
          if (!['thread/started', 'turn/started', 'turn/completed', 'thread/tokenUsage/updated', 'item/started', 'item/completed', 'error'].includes(metadata.method)) return;
          return event('codex_event', metadata);
        },
      });
      if (!entry.sessions.includes(session)) entry.sessions.push(session);
      await entry.authorize();
      entry.assertActive();
      return session;
    };
    let output, results;
    if (entry.assignments) {
      const semanticSchema = fanoutResultSchema(definition, envelope.subagents.fanout);
      const perItem=definition.fanout?.result_mode==='per_item';
      const plan={count:envelope.subagents.resolved_count,items:envelope.subagents.items,
        assignments:assignFanoutItems(envelope.subagents.items,envelope.subagents.fanout,envelope.subagents.resolved_count)};
      const runAssignment = async assignment => {
        const dispatch_id = entry.dispatchIds.get(assignment.index), session = await sessionFor(assignment.index, dispatch_id);
        const prompt = materials.get(assignment.index).prompt
          + `\n\nHost-assigned parallel sub-Agent identity: ${dispatch_id}. Process only the assigned ${envelope.subagents.fanout.item_name} partition in the declared node inputs. Other runtime items belong to other sub-Agents.`
          + (perItem?'':` Return one independent result matching the supplied schema as {"result":...}; do not return the aggregate list or Workflow protocol fields.`);
        if(perItem){
          const assigned=assignedFanoutIndices(plan,definition.fanout,assignment.index);
          const incremental=definition.fanout.item_delivery==='incremental';
          const schema=nativeAgentResultSchema(definition);
          let targetIndices=incremental?assignment.item_indices.slice(0,1):assignment.item_indices;
          const delegated=definition.fanout.shared_change_field
            ? ` or {"outcome":"delegated","result":<one semantic item>} when local work is complete and ${definition.fanout.shared_change_field} names downstream shared work`
            : '';
          let nextPrompt=prompt+`\nReturn exactly one entry per supplied item, in supplied order: {"items":[{"outcome":"completed","result":<one semantic item>}${delegated} or {"outcome":"blocked","block_reason":"specific obstacle"}]}. Do not copy positions, IDs, paths, hashes, tokens, receipts, or other Host-owned fields into the result. The Host binds each array entry to its item deterministically by order.\nResult schema:\n${canonicalJSON(schema)}`;
          const turns=[];
          const maxTurns=definition.retry.max_attempts+(incremental?assignment.item_indices.length-1:0);
          for(let turnNumber=0;turnNumber<maxTurns;turnNumber++){
            entry.assertActive();
            const expectedInputHash=digest(canonicalJSON([{type:'text',text:nextPrompt}]));
            const result=await (turnNumber===0?session.turn(nextPrompt,{timeout_ms:envelope.provider.config.inactivity_timeout_ms})
              :session.continueTurn(nextPrompt,{timeout_ms:envelope.provider.config.inactivity_timeout_ms}));
            entry.assertActive();
            requireValue(result.audit?.input_sha256===expectedInputHash,'MANAGED_NATIVE_INPUT_IDENTITY',
              `Managed native ${dispatch_id} turn ${result.turn_id} received an input differing from its Host-composed prompt`);
            turns.push(result);
            await event('native_prompt_delivery',{dispatch_id,index:assignment.index,thread_id:result.thread_id,turn_id:result.turn_id,
              prompt_sha256:digest(nextPrompt),prompt_chars:nextPrompt.length,input_sha256:expectedInputHash});
            const parsed=perItemTurn(result.output);
            let recorded,issues;
            if(parsed.category)issues=[{item_index:null,category:parsed.category,reason:parsed.reason}];
            else try{recorded=await runtime.recordNativeItemResults(runId,{...args,index:assignment.index,agent_id:dispatch_id,
              turn_id:result.turn_id,target_indices:targetIndices,result:parsed.value});
              issues=recorded.issues;}
            catch(error){if(error.code!=='NATIVE_ITEM_RESULT')throw error;
              issues=[{item_index:null,category:'invalid',reason:error.message}];}
            const fresh=await runtime.runs.read(runId);
            const attempt=fresh.state.nodes[definition.id].attempts.find(item=>item.id===args.attempt_id);
            const unresolved=assigned.filter(index=>!attempt.native_item_results?.[index]);
            if(recorded && !issues.length && !unresolved.length){
              await session.close();
              return {dispatch_id,value:recorded.result,result:{...result,usage:combineTurnUsage(turns),
                delivery_audits:turns.map(turn=>({thread_id:turn.thread_id,turn_id:turn.turn_id,input_sha256:turn.audit.input_sha256}))}};
            }
            const repair=issues.length>0;
            const diagnostic=repair?perItemDiagnostic(issues):null;
            if(repair){
              const rejection=await runtime.recordNativeRejectedTurn(runId,{...args,index:assignment.index,agent_id:dispatch_id,
                turn_id:result.turn_id,category:issues.some(item=>item.category==='blocked')?'blocked':'invalid',reason:diagnostic});
              if(rejection.count>=definition.retry.max_attempts)
                throw Object.assign(new Error(`Managed native ${dispatch_id} exhausted ${definition.retry.max_attempts} rejected turns; unresolved indices ${canonicalJSON(unresolved)}; ${diagnostic}`),
                  {code:'NATIVE_AGENT_REPAIR_EXHAUSTED'});
            }
            targetIndices=incremental?unresolved.slice(0,1):unresolved;
            const repairItems=targetIndices.map(itemIndex=>plan.items[itemIndex]);
            const repairMaterial=await materialFor(assignment.index,
              {...projectFanoutInputs(envelope.inputs,envelope.subagents.items,repairItems),...(repair?{repair_items:repairItems}:{})},
              join(inputRoot,`partition-${assignment.index}`,`${repair?'repair':'next'}-${turnNumber+1}`));
            nextPrompt=repairMaterial.prompt+(repair
              ? `\n\nRepair only the items supplied in repair_items in this existing thread. The Host already retained every accepted sibling result and file. Return exactly one entry per supplied repair item, in supplied order. Resolve these issues in the same order: ${diagnostic}. Return {"items":[...]} with the declared item schema. Do not include positions, IDs, paths, hashes, tokens, receipts, or other Host-owned fields; the Host binds entries by order.`
              : '\n\nContinue with the next supplied item in this same thread. Accepted items are already retained. Return {"items":[{"outcome":"completed","result":<one semantic item>}]} or one specific blocked outcome with the declared item schema.');
          }
          throw Object.assign(new Error(`Managed native ${dispatch_id} reached its pinned completion-turn limit`),{code:'NATIVE_AGENT_REPAIR_EXHAUSTED'});
        }
        const result = await session.turn(prompt + '\n\nReturn {"outcome":"completed","result":<your semantic result>,"block_reason":""}. If a required capability or input is missing, return {"outcome":"blocked","result":null,"block_reason":"specific obstacle"}; never hide a blocker inside a success field.',
          { output_schema: hostNodeTurnSchema(semanticSchema), timeout_ms: envelope.provider.config.inactivity_timeout_ms });
        await session.close();
        let value; try { value = JSON.parse(result.output); } catch { throw Object.assign(new Error(`Managed native sub-Agent ${dispatch_id} result is not JSON`), { code: 'MANAGED_NATIVE_OUTPUT_JSON' }); }
        value = hostNodeTurnResult(value, semanticSchema); return { dispatch_id, value: value.result, result };
      };
      results = await runAssignedPool(entry.assignments, envelope.subagents.fanout.scheduling==='serial'
        ? 1 : envelope.subagents.fanout.max_concurrency ?? Math.max(1,entry.assignments.length), runAssignment);
      if(perItem){const fresh=await runtime.runs.read(runId),accepted=fresh.state.nodes[definition.id].attempts.find(item=>item.id===args.attempt_id)?.native_item_results??{};
        output={ [envelope.subagents.fanout.result_output]:Array.from({length:plan.items.length},(_,itemIndex)=>accepted[itemIndex]?.result) };
        requireValue(output[envelope.subagents.fanout.result_output].every(item=>item!==undefined),'NATIVE_ITEM_RESULT','Per-item pool completion requires every inherited or newly accepted item');}
      else output = { [envelope.subagents.fanout.result_output]: results.map(item => item.value) };
      await runtime.recordManagedNativeResults(runId,{...args,results:results.map((item,index)=>({dispatch_id:item.dispatch_id,result_index:index,result_sha256:digest(canonicalJSON(item.value)),thread_id:item.result.thread_id,turn_id:item.result.turn_id}))});
    } else {
      const semanticSchema = managedNativeResultSchema(definition), session = await sessionFor(0, `managed-${args.attempt_id}`); entry.session = session;
      const prompt = materials.get(0).prompt + '\n\nReturn {"outcome":"completed","result":<your semantic result>,"block_reason":""}. If a required capability or input is missing, return {"outcome":"blocked","result":null,"block_reason":"specific obstacle"}; never hide a blocker inside a success field.';
      const result = await session.turn(prompt, { output_schema: hostNodeTurnSchema(semanticSchema), timeout_ms: envelope.provider.config.inactivity_timeout_ms });
      await session.close(); entry.session = null;
      try { output = JSON.parse(result.output); } catch { throw Object.assign(new Error('Managed native result is not JSON'), { code: 'MANAGED_NATIVE_OUTPUT_JSON' }); }
      output = hostNodeTurnResult(output, semanticSchema); results = [{ dispatch_id: `managed-${args.attempt_id}`, value: output, result }];
    }
    await event('session_state', { status: 'closed' });
    const after = await snapshot(); const changed = changedPaths(before, after);
    const internalBoundary=relative(envelope.workspace,inputRoot).replaceAll('\\','/');
    const semanticChanged=changed.filter(path=>!within(path,internalBoundary));
    const outside = envelope.access === 'read_only' ? semanticChanged : semanticChanged.filter(path => !observedWritePaths.some(boundary => within(path, boundary)));
    if(outside.length)await rejectWorkspaceScope({runtime:entry.runtime,runId:entry.runId,attemptId:args.attempt_id,code:'MANAGED_NATIVE_SCOPE_VIOLATION',changed:semanticChanged,outside,before,after,event});
    const commandAuditArtifact=await persistCodexCommandAudits(runtime,runId,`command-audit-${args.attempt_id}`,
      results.map(item=>({identity:{dispatch_id:item.dispatch_id,thread_id:item.result.thread_id,turn_id:item.result.turn_id},result:item.result})));
    const completion = hostCompletionEnvelope(definition, {
      output, summary: entry.assignments ? `Managed ${adapter.model} pool completed ${results.length} parallel sub-Agents for ${definition.id}` : `Managed ${adapter.model} child completed ${definition.id}`, artifacts: semanticChanged,
      changed_paths: semanticChanged, outside_paths: [],
      evidence: [...(entry.assignments ? [{ kind: 'subagent_pool', resolved_count: results.length, dispatch_ids: results.map(item => item.dispatch_id) }] : []),
        ...results.map((item,index) => ({ kind: 'managed_native_result', dispatch_id: item.dispatch_id, result_index:index,
          result_sha256:digest(canonicalJSON(item.value)),thread_id:item.result.thread_id,turn_id:item.result.turn_id,
          ...compactCodexResultEvidence(item.result) })),
        ...(commandAuditArtifact ? [{ kind:'command_audit_artifact', scope:'managed_native', ...commandAuditArtifact }] : [])],
    }, false);
    const request_id = `dispatch-${args.attempt_id}`;
    await runtime.recordUsage(runId, { ...args, request_id, usage: aggregateUsage(results) });
    const saved = await runtime.runs.saveExecutorResult(runId, args.attempt_id, completion);
    await event('result_proposed', { ...saved, final_acceptance_required: false });
    const settled = await runtime.completeNode(runId, { ...args, completion });
    entry.status = settled.nodes[args.node_id].status === 'failed' ? 'failed' : 'succeeded'; this.compact(entry);
    return { status: entry.status };
  }
  async fail(entry, cause) {
    entry.stopping = true; entry.broker?.revoke(); for (const broker of entry.brokers ?? []) broker.revoke(); const failures = [cause];
    if (cause?.usage) try { await entry.runtime.recordUsage(entry.runId, { ...entry.args, request_id: `dispatch-${entry.args.attempt_id}`, usage: cause.usage }); } catch (error) { failures.push(error); }
    const code = codeOf(cause);
    try {
      const diagnostic = diagnosticOf(cause);
      requireValue(typeof entry.runtime.failAttemptAfterQuiescence === 'function', 'EXECUTION_COORDINATOR_REQUIRED', 'Managed failure requires exact cleanup coordination');
      await entry.runtime.failAttemptAfterQuiescence(entry.runId, entry.args, { code, message: diagnostic }, { originEntry: entry, originManager: this });
      await entry.runtime.recordExecutorEvent(entry.runId, { ...entry.args, event: { kind: 'session_state', metadata: { status: 'failed', code, diagnostic } } });
    } catch (error) { failures.push(error); }
    entry.status = failures.length === 1 ? 'failed' : 'audit_or_cleanup_failed'; entry.error = { code, secondary_codes: failures.slice(1).map(codeOf) };
    this.compact(entry); return { status: entry.status, error: entry.error };
  }
  compact(entry) {
    if(entryNeedsRecovery(entry))return false;
    entry.session = null; entry.sessions = []; entry.broker = null; entry.brokers = []; entry.authorize = null; entry.assertActive = null; entry.prepared = null; entry.runtime = null; entry.job = null; entry.writes = new Set(); return true;
  }
  fenceRun(runId) {
    for (const entry of this.entries.values()) if (entry.runId === runId) {
      entry.stopping = true;
      for (const broker of entryBrokers(entry)) broker.revoke();
    }
  }
  fenceAttempt(runId, nodeId, attemptId) {
    const entry = this.entries.get(entryKey(runId, attemptId));
    if (entry?.args.node_id === nodeId) {
      entry.stopping = true;
      for (const broker of entryBrokers(entry)) broker.revoke();
    }
  }
  async stopAttempt(runId, nodeId, attemptId) {
    return this.stopRun(runId, entry => entry.args.node_id === nodeId && entry.args.attempt_id === attemptId);
  }
  async stopRun(runId, select = () => true) {
    const entries = [...this.entries.values()].filter(entry => entry.runId === runId
      && select(entry) && (!['succeeded', 'failed', 'audit_or_cleanup_failed', 'stopped'].includes(entry.status) || entryNeedsRecovery(entry)));
    const failures = [];
    // Revoke the whole Run synchronously before awaiting any one attempt's
    // interrupt or close. A slow first owner must not leave later attempts
    // authorized to submit new work after Run cancellation.
    for (const entry of entries) entry.stopping = true;
    for (const entry of entries) for (const broker of entryBrokers(entry)) broker.revoke();
    for (const entry of entries) {
      const interruptFailures=await interruptOwnedSessions(entrySessions(entry));
      if(interruptFailures.length)entry.interruptError={code:'MANAGED_NATIVE_INTERRUPT_FAILED',diagnostic:diagnosticOf(new AggregateError(interruptFailures))};
      for (const session of entrySessions(entry)) try { await session.close(); } catch { entry.cleanupPending = true; }
    }
    for (const entry of entries) {
      const recoveryFailures = [];
      for (const broker of entryBrokers(entry)) try { await quiesceBrokerForRecovery(broker); } catch (error) { recoveryFailures.push(error); }
      for (const session of entrySessions(entry)) try { await closeSessionForRecovery(session); } catch (error) { recoveryFailures.push(error); }
      const brokersBeforeSettle = entryBrokers(entry); const sessionsBeforeSettle = entrySessions(entry);
      let unconfirmed = entryBrokers(entry).some(broker => broker.isQuiescent?.() === false);
      let taskSettled = false;
      if (!recoveryFailures.length && !unconfirmed) try { await settleOwnedTask(entry.done); taskSettled = true; } catch (error) { recoveryFailures.push(error); }
      // A factory may publish its close owner while the bounded task-settlement
      // wait is in progress.  Revoke and close the current owner set after that
      // wait; pre-wait snapshots are not cleanup evidence for late owners.
      const currentBrokers = entryBrokers(entry); const currentSessions = entrySessions(entry);
      const ownersChanged = currentBrokers.length !== brokersBeforeSettle.length || currentSessions.length !== sessionsBeforeSettle.length
        || currentBrokers.some(owner => !brokersBeforeSettle.includes(owner)) || currentSessions.some(owner => !sessionsBeforeSettle.includes(owner));
      if (taskSettled && ownersChanged) {
        for (const broker of entryBrokers(entry)) broker.revoke();
        const interruptFailures=await interruptOwnedSessions(entrySessions(entry));
        if(interruptFailures.length)entry.interruptError={code:'MANAGED_NATIVE_INTERRUPT_FAILED',diagnostic:diagnosticOf(new AggregateError(interruptFailures))};
        for (const broker of entryBrokers(entry)) try { await quiesceBrokerForRecovery(broker); } catch (error) { recoveryFailures.push(error); }
        for (const session of entrySessions(entry)) try { await closeSessionForRecovery(session); } catch (error) { recoveryFailures.push(error); }
      }
      unconfirmed = entryBrokers(entry).some(broker => broker.isQuiescent?.() === false);
      entry.cleanupPending = recoveryFailures.length > 0 || unconfirmed;
      if (!entry.cleanupPending) this.compact(entry);
      else failures.push(Object.assign(new AggregateError(recoveryFailures, `Managed native Run ${entry.runId} retained cleanup ownership`), { code: 'CODEX_EXECUTION_STOP_UNCONFIRMED' }));
    }
    if (failures.length) throw new AggregateError(failures, 'Managed native shutdown retained one or more exact executions');
  }
  async close() {
    this.accepting = false;
    const settled = await Promise.allSettled([...new Set([...this.entries.values()].map(entry => entry.runId))].map(runId => this.stopRun(runId)));
    const failures = settled.filter(item => item.status === 'rejected').map(item => item.reason);
    if (failures.length) throw new AggregateError(failures, 'Managed native manager retained cleanup ownership');
    this.hostAuth?.clear();
  }
}
