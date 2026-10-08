import { isAbsolute, relative, resolve } from 'node:path';
import { createHmac } from 'node:crypto';
import { runtimeEnvironmentForWorker } from './runtime-environment-state.mjs';
import { requireValue } from './workflow-paths.mjs';
import { intersectBoundaries, pathBoundaries } from './workflow-bindings.mjs';
import { digest, canonicalJSON } from './workflow-revisions.mjs';
import { skillPathKey } from './execution/codex-skill-policy.mjs';
import { effectiveSkillPolicy } from './workflow-reference-schema.mjs';
import { nodeWorkspace } from './parallel/workspace.mjs';
import { isThreadExecutor, threadContext } from './thread-handoff.mjs';
import { projectNodeContext } from './workflow-context-projection.mjs';
import { WORKSPACE_SOURCE_LOCATIONS, WORKSPACE_SOURCE_LOCATION_RULES } from './workspace-source-locations.mjs';

export function runPermissions({ workspace, access, allowed_paths = [] }) {
  requireValue(typeof workspace === 'string' && isAbsolute(workspace), 'RUN_WORKSPACE', 'Run workspace must be absolute');
  requireValue(['read_only', 'bounded_write'].includes(access), 'RUN_ACCESS', 'Run access must be explicitly read-only or bounded-write');
  requireValue(Array.isArray(allowed_paths), 'PATH_SCOPE', 'Path scope must be an array');
  const paths = pathBoundaries(allowed_paths.map(value => {
    if (typeof value !== 'string' || !isAbsolute(value.trim())) return value;
    const target = value.trim();
    requireValue(!/[*?\[\]{}!\x00-\x1f]/.test(target), 'PATH_SCOPE', 'Path boundaries cannot contain globs or control characters');
    const path = relative(resolve(workspace), resolve(target));
    requireValue(!isAbsolute(path) && path !== '..' && !path.startsWith('../') && !path.startsWith('..\\'), 'PATH_SCOPE', 'Write target is outside the current Run workspace', {workspace, target});
    return path || '.';
  }));
  requireValue(access !== 'bounded_write' || paths.length, 'RUN_PATHS', 'Write access needs concrete current-Run path boundaries');
  return { workspace, access, allowed_paths: paths };
}

export function nodePermissions(node, state) {
  const access = typeof node.access === 'object' ? state.permissions.access : node.access;
  requireValue(['read_only', 'bounded_write'].includes(access), 'NODE_ACCESS', 'Node has no resolved access mode');
  if (access === 'read_only') return { access, allowed_paths: [] };
  requireValue(state.permissions.access === 'bounded_write', 'NODE_WRITE_UNAUTHORIZED', 'Node requests write access outside this Run authorization');
  const requested = Array.isArray(node.path_scope) ? node.path_scope : state.permissions.allowed_paths;
  const paths = intersectBoundaries(state.permissions.allowed_paths, requested);
  requireValue(paths.length, 'NODE_PATHS_EMPTY', 'Node path scope has no intersection with Run permissions');
  return { access, allowed_paths: paths };
}

export function bindingContext(state) {
  const loops = Object.fromEntries(Object.entries(state.loops ?? {}).map(([id, loop]) => [id,
    Object.fromEntries(['round','status','feedback','all_accepted','review_items','repair_items'].filter(key => Object.hasOwn(loop, key)).map(key => [key, loop[key]]))]));
  return { inputs: state.inputs, loops, nodes: Object.fromEntries(Object.entries(state.nodes).map(([id, node]) => [id, { output: node.output }])) };
}

export function approvalBinding(node, state, pins, attemptNumber = state.nodes[node.id].attempts.length + 1) {
  const provider = ['provider', 'thread'].includes(node.executor?.kind) ? pins.providers.find(item => item.id === node.executor.provider_id) : node.executor?.kind === 'main' ? pins.authoring_reviewer ?? pins.generation?.reviewer ?? null : null;
  const permissions = nodePermissions(node, state);
  return {
    required: Boolean(node.approval.required || provider?.requires_user_approval || state.require_approval),
    hash: digest(canonicalJSON({ revision: state.workflow_revision, node_id: node.id, attempt: attemptNumber, provider, permissions, skill_policy: effectiveSkillPolicy(pins.inherited_policy ?? pins.root.workflow.skill_policy, node.skill_policy), subworkflow: node.subworkflow ?? null })),
  };
}

export function leaseToken(controlToken, runId, nodeId, attemptId, generation = 0) {
  return createHmac('sha256', controlToken).update([runId, nodeId, attemptId, ...(generation ? ['generation', String(generation)] : [])].join('\0')).digest('hex');
}

export function executionEnvelope(node, state, pins, attempt, token) {
  const permissions = nodePermissions(node, state);
  const constraints=structuredClone(state.constraints);
  delete constraints.native_parent_thread_id;
  delete constraints.runtime_requirements;
  const runtimeEnvironment = runtimeEnvironmentForWorker(state);
  if (runtimeEnvironment) constraints.runtime_environment = runtimeEnvironment;
  const context = projectNodeContext(node, pins.root.workflow, bindingContext(state));
  const skillPolicy = effectiveSkillPolicy(pins.inherited_policy ?? pins.root.workflow.skill_policy, node.skill_policy);
  const skillPaths = [...skillPolicy.ambient_allow, ...(node.skill_ref ? [node.skill_ref.path, ...node.skill_ref.allowed_nested_skills.map(item => item.path)] : [])];
  const allowedSkills = [...new Set(skillPaths.map(skillPathKey))].map(path => {
    requireValue(!skillPolicy.shadowed_skill_paths.some(shadow => skillPathKey(shadow) === path), 'SKILL_POLICY_CONFLICT', 'Explicit or ambient Skill allowance conflicts with a shadowed source');
    const pin = (pins.skills ?? []).find(skill => skillPathKey(skill.path) === path);
    requireValue(pin, 'SKILL_ALLOW_UNPINNED', 'Node allowance has no immutable Run snapshot'); return structuredClone(pin);
  });
  const threadExecutor = isThreadExecutor(node.executor);
  let subagents=null;
  if(node.subagent_count!==undefined){
    requireValue(node.executor?.kind!=='main','SUBAGENT_COUNT','Main Agent nodes cannot configure sub-Agent quantity');
    let resolved_count=node.subagent_count==='auto'?1:node.subagent_count,items=null;
    if(node.fanout){
      items=context.inputs[node.fanout.input];
      requireValue(Array.isArray(items)&&items.length>0,'SUBAGENT_FANOUT_INPUT','Fan-out input must resolve to a nonempty list');
      if(node.subagent_count==='auto')resolved_count=node.fanout.batch_size?Math.ceil(items.length/node.fanout.batch_size):items.length;
      else requireValue(resolved_count<=items.length,'SUBAGENT_FANOUT_INPUT','Fixed fan-out cannot allocate more sub-Agents than runtime items');
    }
    requireValue(Number.isSafeInteger(resolved_count)&&resolved_count>=1&&(node.fanout?.scheduling==='serial'||node.fanout?.max_concurrency||resolved_count<=32),'SUBAGENT_COUNT','Unbounded parallel fan-out may dispatch at most 32 concurrent sub-Agents');
    subagents={configured_count:node.subagent_count,resolved_count,...(node.fanout?{fanout:structuredClone(node.fanout),items:structuredClone(items)}:{})};
  }
  const thread = threadExecutor ? { ...threadContext(state, node.executor), protocol_version: pins.thread_protocol_version ?? 1 } : null;
  const resourceInstruction = node.resources?.length
    ? threadExecutor
      ? 'Resources listed below are logical identifiers, not filesystem paths. Use the supplied immutable UTF-8 snapshots; cite resource IDs.'
      : 'Resources listed below are logical identifiers, not filesystem paths. Use read_workflow_resource; cite resource IDs.'
    : '';
  const locationOutputs=Object.entries(node.output_validators??{}).filter(([,kind])=>kind===WORKSPACE_SOURCE_LOCATIONS).map(([name])=>name);
  return {
    run_id: state.run_id, workflow_id: state.workflow_id, workflow_name: pins.root.workflow.name, workflow_revision: state.workflow_revision,
    node_id: node.id, node_name: node.name ?? node.id, attempt_id: attempt.id, lease_token: token, executor: structuredClone(node.executor),
    provider: ['provider', 'thread'].includes(node.executor.kind) ? structuredClone(pins.providers.find(item => item.id === node.executor.provider_id)) : null,
    role: node.role ?? null, access: permissions.access, workspace: nodeWorkspace(node.id, state, pins),
    inputs: context.inputs, context_projection: context.projection,
    constraints: {...constraints,...(state.constraints.task_workspace?{task_workspace:nodeWorkspace(node.id,state,pins)}:{})},
    prompt_template: ((pins.root.workflow.requirements?.executables?.length || pins.root.workflow.requirements?.environment?.length)
        ? `Dependencies: ${JSON.stringify({executables:pins.root.workflow.requirements?.executables ?? [],environment:pins.root.workflow.requirements?.environment ?? []})}. Report unresolved dependencies with command/error evidence.\n` : '')
      + (constraints.runtime_environment?.tools?.length
        ? `Run executables: ${JSON.stringify(constraints.runtime_environment.tools)}. Use these locations and a process-local PATH for helpers.\n` : '')
      + resourceInstruction + (resourceInstruction ? '\n' : '')
      + (locationOutputs.length ? `Marked output ${locationOutputs.join(', ')}: ${WORKSPACE_SOURCE_LOCATION_RULES}\n` : '')
      + (node.prompt_template ?? (node.type === 'skill_ref' ? 'Apply the pinned Skill to {{task}} using its mapped resources.' : '')),
    resources: context.references, outputs_schema: structuredClone(node.outputs_schema ?? {}), completion_contract:structuredClone(node.completion_contract ?? null),
    subagents,
    skill_policy: skillPolicy, skill_ref: structuredClone(node.skill_ref ?? null),
    subworkflow: structuredClone(node.subworkflow ?? null),
    thread,
    allowed_skills: allowedSkills,
    effective_allowed_paths: permissions.allowed_paths,
    resource_access: { reader: threadExecutor ? 'thread_snapshot' : 'read_workflow_resource', paths: structuredClone(node.resources ?? []) },
    ...(skillPolicy.mode === 'cooperative' ? {path_scope_applies_to:'writes_only',tool_access:'host_permissions',read_access:'host_permissions'} : {}),
  };
}
