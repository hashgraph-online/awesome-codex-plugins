import { workflowInvocationDescription } from './workflow-call-policy.mjs';

const string = { type: 'string' }; const object = { type: 'object' };
const properties = {
  environment_directories: {type:'array',items:string,description:'Optional discovered installation directories outside PATH; applies only to this Run.'},
  folder: string, discovery: { type: 'string', enum: ['folders','host'] }, routing_rules: object,
  workflow_id: string, revision_hash: string, run_id: string, node_id: string, attempt_id: string, task: string,
  context:string,verification:string,
  user_approved:{type:'boolean',description:'Explicit current-task approval when the configured Provider requires it.'},
  control_token: { type: 'string', description: 'Main-controller capability returned by workflow_start. Never include it in worker prompts.' },
  lease_token: { type: 'string', description: 'Exact attempt lease returned by workflow_claim_node.' },
  request_id: string, owner: string, expected_sequence: { type: 'integer', minimum: 1 },
  request_prefix: string, usage: object,
  agent_id: string, index: { type: 'integer', minimum: 0 }, result: {},
  batch_id:{type:'string',pattern:'^[a-f0-9]+$',minLength:64,maxLength:64,
    description:'Exact Host-generated native spawn batch identity embedded in its fixed invocation adapter. Never author or transcribe this field.'},
  agent_ids: { type: 'array', items: string }, results: { type: 'array', items: object },
  native_spawns: {type:'array',minItems:1,maxItems:32,items:{type:'object',properties:{
    index:{type:'integer',minimum:0},agent_id:string},required:['index','agent_id'],additionalProperties:false}},
  expected_revision: string, workflow: object, resources: object, inputs: {},
  inputs_path: {type:'string',description:'Optional JSON file inside the Run workspace containing the exact Workflow inputs. Relative and absolute in-workspace paths are supported. Do not also send inputs.'},
  startup_reference:{type:'string',pattern:'^[0-9a-f-]+$',minLength:36,maxLength:36,description:'Opaque Host-created preparation UUID embedded in the startup contract adapter. Reuse the exact reference and semantic result to rejoin the same invocation.'},
  initial_output:{description:'New semantic decision for an eligible initial current-Main node. Use the Host startup contract adapter: it fixes revision_hash and startup_inputs_sha256 while the caller fills only this semantic result. Original node checks remain required. Ordinary startup may omit this field and return the real initial Main handoff.'},
  startup_inputs_sha256:{type:'string',pattern:'^[a-f0-9]+$',minLength:64,maxLength:64,description:'Host-generated exact original-input pin in the startup adapter; required with initial_output. Do not author or transcribe this field.'},
  launch_key:{type:'string',pattern:'^[0-9a-f-]+$',minLength:36,maxLength:36,description:'Host-generated invocation identity embedded in a startup adapter. Reusing that exact adapter rejoins the same launch, including terminal outcomes; a newly generated adapter starts a new invocation. Never author or transcribe this field.'},
  workspace: string,
  access: { type: 'string', enum: ['read_only', 'bounded_write'] }, allowed_paths: { type: 'array', items: string, description: 'Current Run write targets: workspace-relative paths or absolute paths inside workspace. Use a task-derived scope; . means the entire workspace. Absolute targets are normalized and pinned as relative paths.' },
  constraints: {}, main_actor: string, require_approval: { type: 'boolean' }, completion: object, output: object,
  native_parent_thread_id:{type:'string',description:'Host-authenticated controller Codex thread UUID. This field is unavailable to model-facing Workflow start calls.'},
  summary: string, artifacts: { type: 'array' }, evidence: { type: 'array' }, changed_paths: { type: 'array', items: string }, outside_paths: { type: 'array', items: string },
  accepted: { type: 'boolean' }, error: object,
  reconciliation: object, after_restart: { type: 'boolean' }, reason: string, approval_id: string, decision: { type: 'boolean' },
  authorization: { type: 'object', description: 'Optional record of existing user authorization. Task authorization persists across recovery and continuation; a fresh per-Run confirmation is not required.', properties: { confirmed: { type: 'boolean', enum: [true] }, source: { type: 'string', enum: ['user_message'] }, statement: { type: 'string', minLength: 1, maxLength: 2000 } }, required: ['confirmed', 'source', 'statement'], additionalProperties: false },
  after_sequence: { type: 'integer', minimum: 0 }, receipt: object,
  timeout_ms:{type:'integer',minimum:1,maximum:3600000,description:'Host-side wait ceiling. Default 3600000 ms (one hour); actionable events return immediately.'},
  skill_id: string, provider_id: string, name: string, brief: string, proposal: object, accepted: { type: 'boolean' },
  region_id: string, patch_sha256: string, package_version:string, package:object, package_path:string, source_url:string, expected_sha256:string,
  resource_path: string, text: string, remove: { type: 'boolean' },
  template_kind: {type:'string',enum:['role','workflow'],description:'role is a reusable single-agent behavior; workflow is a complete task graph. Omit for workflow.'},
  completion_policy: {type:'string',enum:['automatic','manual'],description:'New authoring Runs default to automatic launch-ready completion. Select manual only to retain a reviewed Draft for explicit acceptance.'},
  control: object,
  limit: {type:'integer',minimum:1,maximum:20},
  include_legacy: {type:'boolean',description:'Include retired task-graph Drafts only for explicit historical inspection.'},
};
const lease = ['run_id', 'node_id', 'attempt_id', 'lease_token'];
const main = ['run_id', 'control_token'];
const recovery = [...main, 'node_id', 'attempt_id'];
// These operations are application-host APIs. The console/runtime call the
// service boundary directly. They are absent from both the model catalog and
// the model-facing MCP dispatch boundary, so guessing a tool name cannot expose
// controller capabilities, leases or completion-envelope fields.
const hostOnlySpecs = [
  ['begin_main', 'Host-only main-session launch.', ['workflow_id', 'workspace', 'access', 'main_actor'], ['native_parent_thread_id','revision_hash', 'run_id', 'inputs', 'inputs_path', 'allowed_paths', 'constraints', 'require_approval','environment_directories']],
  ['run_main', 'Host-only background launch through isolated logical Main nodes.', ['workflow_id', 'workspace', 'access', 'main_actor'], ['native_parent_thread_id','revision_hash', 'run_id', 'inputs', 'inputs_path', 'allowed_paths', 'constraints', 'require_approval','environment_directories']],
  ['main_status', 'Host-only isolated Main status and final proposal lookup.', ['run_id'], []],
  ['accept_main', 'Host-only human acceptance of one isolated final Main proposal.', ['run_id','control_token','accepted'], []],
  ['continue_main', 'Host-only continuation after a human control decision.', ['run_id','control_token','owner'], ['request_prefix']],
  ['create_authoring_run', 'Host-only materialization of one stored authoring Workflow against an exact private source Draft, with a pinned completion policy.', ['workflow_id', 'revision_hash', 'run_id', 'workspace', 'main_actor'], ['provider_id','routing_rules','completion_policy']],
  ['apply_authoring_result', 'Host-only source-free deployment of one exact human-accepted authoring result.', [...main, 'workflow_id', 'expected_revision'], []],
  ['purge_authoring_artifacts', 'Host-only retry for exact private authoring cleanup after a source-free deployment committed.', [...main,'workflow_id'], []],
];
const specs = [
  ['routing_defaults', 'Read editable default Skill expansion routing rules for the configured Providers.', [], []],
  ['role_templates', 'List enabled and disabled Workbench Roles for automatic helper selection in ordinary tasks; does not read instructions or start a Workflow Run.', [], []],
  ['role_template', 'Compile one selected Workbench Role and its exact Provider adapter for an ordinary helper assignment; never use this inside a Workflow Run.', ['workflow_id','task'], ['revision_hash','context','constraints','verification']],
  ['start_role_connector', 'Execute one enabled Workbench Role through its pinned built-in connector without a Workflow Run or legacy Task Type. The Host compiles and delivers the Role instructions; use the returned task_id with connector status/control.', ['workflow_id','revision_hash','task','workspace'], ['context','constraints','verification','allowed_paths','user_approved']],
  ['route', 'Return only compact valid Ready Workflow candidates for one concrete task; excludes authoring Workflows and prompt bodies.', ['task'], ['limit']],
  ['startup_contract','Prepare an eligible Ready Workflow initial current-Main semantic contract without a Run or model invocation. The Host retains a sealed preparation and returns an adapter embedding only its opaque startup_reference. Typed initial_output validates the actual node schema and leaves no source slot; otherwise fill only fresh semantic JSON. Exact launch arguments, revision and original inputs remain Host-owned; startup retains the original lifecycle, checks, approvals and final acceptance.',['workflow_id','workspace','access'],['inputs','inputs_path','allowed_paths','constraints','require_approval','environment_directories','completion_policy','initial_output']],
  ['start_prepared','Call the supplied startup adapter directly; Host reads the retained inputs and checks/registers dependencies. Submit the exact Host-created startup_reference from startup_contract. For an untyped preparation supply only fresh semantic initial_output; a typed preparation already owns its validated output and accepts no replacement. The Host resolves original business arguments and exact revision/input pins, authenticates the current conversation and reuses normal startup authorization, one-Run retries, original checks and final acceptance.',['startup_reference'],['initial_output']],
  ['authoring_workflows', 'List the built-in Skill conversion and from-scratch Workflow authoring pipelines, their shared semantic contract, and retry boundary.', [], []],
  ['capabilities', 'Read current Strict qualification and declared host capabilities without starting a session or exposing credentials.', [], []],
  ['skill_inventory', 'Discover importable Skills in default Codex folders or a user folder without executing models; explicit host mode reads qualified host metadata.', [], ['workspace', 'folder', 'discovery']],
  ['import_skill', 'Coarse-import a user-selected current Skill inventory entry into an immutable Cooperative Draft with explicit dependency observations. Executes no scripts or model calls.', ['skill_id', 'workflow_id'], ['workspace', 'folder', 'discovery', 'name', 'provider_id']],
  ['build_workflow', 'Build a role or complete Workflow from a brief. A role is a direct agent instruction profile; a Workflow enters the shared semantic compiler and review path. Choose template_kind from the user intent; omit for workflow.', ['workflow_id','name','brief'], ['provider_id','template_kind','access']],
  ['install_workflow_package', 'Install one integrity-checked Workflow package. For a local file, pass package_path so the Host reads it directly; package JSON is intentionally not accepted at the model boundary. Relative package_path values require an absolute workspace. HTTPS sources may be pinned with expected_sha256.', [], ['package_path','workspace','source_url','expected_sha256']],
  ['export_workflow_package', 'Export one immutable Workflow revision as a content-addressed portable package suitable for local or cloud distribution.', ['workflow_id'], ['revision_hash','package_version']],
  ['delete', 'Move one explicitly selected Workflow or Role to recoverable storage. Read it first and pass its exact current revision hash.', ['workflow_id','expected_revision'], []],
  ['verify_relocation', 'Verify pinned imported resource availability without reading the original Skill. Does not prove functional execution.', ['workflow_id', 'revision_hash'], []],
  ['import_review', 'Read unresolved import observations and exact inferred nodes/edges for human review. This does not confirm or publish them.', ['workflow_id'], ['revision_hash']],
  ['inline_skill', 'Convert one exact SkillRef and its explicitly pinned nested Skills to editable resource-backed instructions. Always creates a Draft and never runs source scripts.', ['workflow_id', 'node_id', 'expected_revision'], []],
  ['prepare_expansion', 'Prepare a read-only expansion packet for the user-selected Provider. This does not invoke that Provider or grant approval.', ['workflow_id', 'revision_hash', 'provider_id'], ['routing_rules']],
  ['list', 'List current Workflow metadata and readiness, without prompt bodies. Retired Role graphs require include_legacy for explicit historical inspection.', [], ['include_legacy']],
  ['read', 'Read one explicit immutable Workflow revision for inspection or editing.', ['workflow_id'], ['revision_hash']],
  ['source_status', 'Compare the complete imported Skill source inventory, plus explicit linked Skill sources, against pinned hashes and report update_available or read diagnostics. Never changes Workflow resources or an existing Run.', ['workflow_id'], ['revision_hash']],
  ['revisions', 'Read immutable revision history metadata. Opening a revision verifies its resource content separately.', ['workflow_id'], []],
  ['read_resource', 'Read an exact pinned Pack resource for inspection. Binary or large content is not editable as text.', ['workflow_id', 'resource_path'], ['revision_hash']],
  ['write_resource', 'Save one user-requested bounded resource edit as a Draft under revision CAS. Imported resource changes require review and never touch the original source.', ['workflow_id', 'expected_revision', 'resource_path'], ['text', 'remove']],
  ['validate', 'Validate a graph, pinned bindings and current launch blockers.', ['workflow'], []],
  ['create', 'Create a user-requested Workflow Pack. Skill imports declare their own Strict or Cooperative execution policy.', ['workflow'], ['resources']],
  ['save', 'Save one complete definition using the previously read revision hash; use write_resource for resource changes.', ['workflow_id', 'workflow', 'expected_revision'], []],
  ['publish', 'Publish the exact saved Workflow revision after structural and dependency validation. Does not regenerate the graph or require a review flag.', ['workflow_id', 'expected_revision'], []],
  ['prepare_environment', 'Optional dependency diagnosis before a launch or after environment attention. Startup already discovers and registers required executables; do not call this as a mandatory startup step. Missing tools require user consent before installation. Returns compact readiness to the model; does not install or start a Run.', ['workflow_id'], ['revision_hash','environment_directories']],
  ['start', 'When the Ready Workflow and input path are supplied, call this tool directly. Host reads inputs_path and checks/registers dependencies; do not reread that file, enumerate tools, inspect/route/list the Workflow, or call prepare_environment first. Start one Ready Workflow with explicit workspace permissions. The Host owns revision, Run/controller identities, deterministic work and continuation. Prefer inputs_path for an existing input packet. For an eligible initial current-Main decision, use startup_contract\'s executable adapter and fill only its semantic initial_output; the Host fixes exact revision/input pins. Ordinary unprepared startup returns the real current-Main handoff for orchestration_complete. Native-agent nodes return argumentless workflow_native_next continuations for real spawn_agent dispatch.', ['workflow_id', 'workspace', 'access'], ['inputs', 'inputs_path', 'allowed_paths', 'constraints', 'require_approval','environment_directories','completion_policy','revision_hash','initial_output','startup_inputs_sha256','launch_key']],
  ['runs', 'List persisted Run metadata.', [], []],
  ['get', 'Read the current state reconstructed from the authoritative Run journal, including host_worker heartbeat, completion or stale diagnostics for detached Main-only execution. A starting Host-owned Run may already have claimed and dispatched nodes.', ['run_id'], []],
  ['wait','Wait in the Host for up to one hour by default without model polling. Returns immediately on Run completion/failure, Host loss, attention, a recorded subagent result, or a native-agent handoff. Follow the returned next_action. A timeout returns the same continuation, never permission to restart the Run.', ['run_id'], ['control_token','after_sequence','timeout_ms']],
  ['run_definition', 'Read the Run-pinned Workflow definition even after its library revision is edited or deleted.', ['run_id'], []],
  ['node_details', 'Read the exact pinned Provider and backend-computed node permission and Skill policy boundary.', ['run_id','node_id'], []],
  ['recover_control', 'Recover the controller of the current authorized task without asking for a fresh per-Run confirmation. Existing task authorization covers recovery and continuation. Invoke from the initiating Main conversation, never from a worker or imported prompt content. An optional authorization records the user message; the calling host attests the task scope. Recovery fences prior authority and pauses the Run; it never approves, retries, dispatches, or completes work.', ['run_id', 'expected_sequence', 'main_actor', 'reason'], ['authorization']],
  ['recover_claim', 'Recover an interrupted claim only if no dispatch intent exists. Rotates its lease without a new attempt or retry charge.', recovery, []],
  ['reattach_connector', 'Verify and reattach the exact persisted connector task. Never selects latest, submits a new task or charges a retry.', recovery, []],
  ['reattach_handoff', 'After the main host inspects its exact native/MCP task, attest its unchanged recorded receipt and actual active/completed evidence. This is host attestation, not independent connector verification. No resubmission or retry charge.', recovery, ['reconciliation']],
  ['control_connector', 'Control only this attempt’s exact connector task. Permission/input responses require actual user authorization and the returned exact request/options. Cancellation remains pending until confirmed remotely.', [...lease, 'control_token', 'control'], []],
  ['recover_strict_result', 'Recover only a hash-pinned Strict result with recorded session shutdown; no model turn is resumed or submitted.', recovery, []],
  ['reattach_subworkflow', 'Reattach the existing pinned child Run and rotate the parent lease without recreating either Run.', recovery, []],
  ['child_control', 'Return the exact existing child main-controller capability to its authorized parent controller. Never put it in worker prompts.', recovery, []],
  ['next', 'Read ready node IDs and pending approvals. This does not claim or dispatch work.', ['run_id'], []],
  ['native_next', 'Continue the model session’s current Workflow Run. The Host owns Run authority and every receipt field. Execute each Host-generated spawn_calls tool with its exact arguments, then execute the fixed native spawn batch invocation adapter.', [], []],
  ['native_spawned_batch', 'Acknowledge that every spawn_agent call in the exact Host-released batch succeeded. Execute the returned fixed invocation adapter; it embeds the Host batch identity and retries only that receipt. Empty arguments are accepted only for one unambiguous durable batch.', [], ['batch_id']],
  ['orchestration_complete', 'Complete the current conversation orchestration node with newly authored semantic output only. The Host resolves the Run, node, receipt, paths and completion, then advances the Workflow.', ['output'], []],
  ['native_followed_up', 'Acknowledge one successful collaboration.followup_task call for the Host-persisted follow-up intent; pass no arguments.', [], []],
  ['drive', 'Advance one bounded Host-controlled step for an ordinary Run without logical Main nodes. Built-in authoring Runs use their pinned planner/reviewer controller and may incur model usage. A Main-only Run is owned by its detached Host worker: workflow_drive rejects model calls with HOST_MAIN_BRIDGE_REQUIRED and does not report whether that worker has already dispatched nodes. Semantic nodes, approvals, missing input, ambiguity and failures return an exact stop reason.', [...main], ['owner', 'request_prefix']],
  ['claim_node', 'Atomically claim one ready node and return its narrow execution lease. Main nodes require the exact main actor.', [...main, 'node_id', 'owner', 'request_id'], ['expected_sequence']],
  ['complete_node', 'Commit successful node output plus artifacts, evidence, changed_paths and outside_paths. Authoring finalization is reserved for verified Host automatic completion or the authenticated human Workbench action.', [...lease, 'completion'], []],
  ['fail_node', 'Commit an explicit node failure diagnostic under its active lease.', [...lease, 'error'], []],
  ['retry_node', 'Explicitly retry a failed/interrupted node within its pinned budget. Uncertain external dispatch requires reconciliation evidence.', [...main, 'node_id'], ['reconciliation']],
  ['pause', 'Pause new node release and dispatch; active completions remain recorded.', main, ['reason']],
  ['resume', 'Resume a paused Run, or fence and reconstruct it after_restart. Never silently resubmits an interrupted task.', main, ['after_restart']],
  ['cancel', 'Fence local Run leases and mark external cancellation pending. Remote termination must be confirmed separately.', main, []],
  ['approve', 'Record an authorized current-node approval bound to the pinned scope. Set decision only from actual user authorization.', [...main, 'approval_id', 'decision'], []],
  ['events', 'Read sequenced event metadata without prompts or controller secrets.', main, ['after_sequence']],
  ['dispatch', 'Persist intent, then invoke the pinned built-in/API Provider or return a main/native/Codex-thread/MCP handoff. Codex-thread handoffs carry an exact create-or-continue task contract, bounded pinned text snapshots when needed, and exact collection instructions. Repeated uncertain dispatch never resubmits.', [...lease, 'control_token'], []],
  ['dispatch_receipt', 'Persist exact task identity from the external tool result for one existing dispatch intent.', [...lease, 'control_token', 'request_id', 'receipt'], []],
  ['record_usage', 'Journal actual request usage, cached/visual usage when reported, or explicit unknown metering. Budgeted semantic work cannot complete without it.', [...lease, 'control_token', 'request_id', 'usage'], []],
  ['reconcile_connector', 'Inspect only the preallocated exact connector task after an uncertain dispatch. Does not retry it.', [...lease, 'control_token'], []],
  ['collect_connector', 'Collect an active exact connector task. Commit completion only with observed terminal and workspace-scope evidence.', [...lease, 'control_token'], []],
  ['collect_subworkflow', 'Collect the exact child Run after its main-agent acceptance. Output stays in the parent node namespace; collection never invokes another executor.', [...lease, 'control_token'], []],
  ['prepare_integration', 'Verify isolated branch changes and create an immutable merge proposal after Join. Conflicts or failed branches stop integration.', [...main, 'region_id'], []],
  ['review_integration', 'Read the exact saved merge patch and branch evidence before main-controlled integration.', [...main, 'region_id'], []],
  ['integrate_parallel', 'Apply a main-reviewed exact merge patch only if its target still matches the recorded base. Leaves the user branch and index unchanged.', [...main, 'region_id', 'accepted', 'patch_sha256'], []],
  ['cleanup_parallel', 'Remove exact owned worktrees only after terminal execution and accepted unchanged branch snapshots. Unmerged or changed worktrees remain for inspection.', main, []],
  ['strict_status', 'Read one exact isolated session status. Login URLs are restricted to the human console.', [...lease, 'control_token'], []],
  ['collect_strict', 'Read or reconcile a durable isolated result without another model submission. Authoring acceptance cannot be submitted by a model; the Host applies the Run-pinned completion policy.', [...lease, 'control_token'], ['accepted']],
  ['cleanup_strict_orphans', 'After fencing an interrupted attempt, stop and remove only its verified orphan profile. Never resubmits work or terminates an active owner.', [...lease, 'control_token'], []],
];
export const WORKFLOW_TOOL_OPERATIONS = new Set(specs.map(([name]) => name));
export const HOST_ONLY_WORKFLOW_OPERATIONS = new Set(hostOnlySpecs.map(([name]) => name));
// MCP annotations describe effects; they do not grant authority or add gates.
// Keep every operation classified so additions cannot inherit misleading hints.
const effectGroups = [
  [true, false, false, 'routing_defaults role_templates role_template route authoring_workflows import_review prepare_expansion list read revisions read_resource runs get wait run_definition node_details next events review_integration child_control'],
  [true, false, true, 'capabilities skill_inventory verify_relocation source_status validate strict_status'],
  [false, false, false, 'startup_contract build_workflow inline_skill create publish claim_node complete_node fail_node dispatch_receipt record_usage prepare_integration'],
  [false, true, false, 'delete write_resource save recover_control recover_claim reattach_handoff recover_strict_result reattach_subworkflow pause resume approve'],
  [false, false, true, 'import_skill export_workflow_package prepare_environment reattach_connector reconcile_connector collect_connector collect_subworkflow collect_strict'],
  [false, true, true, 'start_role_connector install_workflow_package start start_prepared control_connector native_next native_spawned_batch native_followed_up orchestration_complete drive retry_node cancel dispatch integrate_parallel cleanup_parallel cleanup_strict_orphans'],
];
const effects = new Map(effectGroups.flatMap(([readOnlyHint, destructiveHint, openWorldHint, names]) =>
  names.split(' ').map(name => [name, { readOnlyHint, destructiveHint, openWorldHint }])));
export function workflowToolDefinitions(transport = 'code_mode') {
  return specs.map(([name, description, required, optional]) => {
    const annotations = effects.get(name);
    if (!annotations) throw new Error('MCP_TOOL_EFFECTS_MISSING: ' + name);
    return { name: 'workflow_' + name, description: workflowInvocationDescription('workflow_' + name, description, transport), annotations: { ...annotations },
      inputSchema: { type: 'object', properties: Object.fromEntries([...required, ...optional].map(key => [key, properties[key]])), required, additionalProperties: false },
    };
  });
}
