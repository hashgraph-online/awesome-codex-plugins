import { canonicalJSON, digest } from './workflow-revisions.mjs';
import { requireValue } from './workflow-paths.mjs';
import { isAbsolute, join, dirname, basename, delimiter } from 'node:path';
import { statSync, realpathSync, accessSync, constants } from 'node:fs';
import { normalizeNodeRuntimeRequirements, normalizeExecutableRequirements } from './runtime-requirements.mjs';
import {assertOutsideHostRunTransaction,withRunStorePurpose} from './workflow-run-store.mjs';

export const workspaceRuntimeDirectories = workspace => typeof workspace==='string'&&isAbsolute(workspace)
  ? ['.venv','venv','env'].flatMap(name=>['Scripts','bin'].map(bin=>join(workspace,name,bin))) : [];

export const runtimeEnvironmentForState = state => state.runtime_environment ?? state.constraints?.runtime_environment ?? null;
export const runtimeRequirementsForState = state => state.constraints?.runtime_requirements ?? {
  executables: (runtimeEnvironmentForState(state)?.tools ?? []).map(tool => tool.name),
};

export function augmentedRuntimeEnvironment(env,environment,{workspace}={}){
  const windows=process.platform==='win32',key=value=>windows?value.toLowerCase():value;
  const tools=(environment?.tools??[]).filter(tool=>tool.status==='found'&&typeof tool.path==='string'&&isAbsolute(tool.path));
  const directories=[...new Set(tools.map(tool=>dirname(tool.path)))];
  const result={...env},pathKey=Object.keys(result).find(name=>name.toUpperCase()==='PATH'),inherited=pathKey?result[pathKey]:'';
  const canonical=path=>key(realpathSync.native(path));
  // Match libuv native Windows lookup: only a nonempty final extension is
  // literal-first, and a trailing dot already separates the appended extension.
  const candidateNames=name=>{
    if(!windows)return [name];
    const dot=name.lastIndexOf('.'),stem=name.endsWith('.')?name:`${name}.`;
    return [...(dot>=0&&dot<name.length-1?[name]:[]),`${stem}com`,`${stem}exe`];
  };
  const candidate=(directory,name)=>{
    const names=candidateNames(name);
    for(const filename of names){const path=join(directory,filename);let info;
      try{info=statSync(path);}catch(error){if(['ENOENT','ENOTDIR'].includes(error.code))continue;throw error;}
      if(!info.isFile())continue;
      if(!windows)accessSync(path,constants.X_OK);
      return {path,canonical:canonical(path)};
    }
    return null;
  };
  const edges=new Map(directories.map(directory=>[directory,new Set()]));
  const bindings=[];
  for(const tool of tools){
    const expected=canonical(tool.path),target=dirname(tool.path),filename=key(basename(tool.path)),name=key(tool.name);
    // Physical aliases keep their absolute binding; PATH cannot invent a logical alias.
    const matches=candidateNames(name);
    // An apparent logical stem (alpha. -> alpha..exe) is not a physical alias:
    // reject it when the actual native candidate resolves a different pin.
    const logicalStem=windows&&filename.replace(/\.(com|exe)$/,'')===name;
    if(!matches.includes(filename)&&!logicalStem)continue;
    bindings.push({tool,expected});
    const own=candidate(target,tool.name);
    requireValue(own?.canonical===expected,'ENVIRONMENT_BINDING_STALE','Bound executable is shadowed within its own directory',{dependency:tool.name,expected_path:tool.path,observed_path:own?.path??null});
    if(windows&&workspace){const local=candidate(workspace,tool.name);
      requireValue(!local||local.canonical===expected,'ENVIRONMENT_BINDING_STALE','Working directory shadows a bound executable',{dependency:tool.name,expected_path:tool.path,observed_path:local?.path??null});}
    for(const directory of directories){if(directory===target)continue;const found=candidate(directory,tool.name);if(found&&found.canonical!==expected)edges.get(target).add(directory);}
  }
  const ordered=[],remaining=new Set(directories);
  while(remaining.size){const next=directories.find(directory=>remaining.has(directory)&&![...remaining].some(other=>edges.get(other).has(directory)));
    requireValue(next,'ENVIRONMENT_BINDING_STALE','Executable directory precedence cannot satisfy all bound paths',{dependencies:bindings.map(({tool})=>tool.name),directories});
    ordered.push(next);remaining.delete(next);
  }
  for(const {tool,expected} of bindings){const found=ordered.map(directory=>candidate(directory,tool.name)).find(Boolean);
    requireValue(found?.canonical===expected,'ENVIRONMENT_BINDING_STALE','PATH resolution differs from the bound executable',{dependency:tool.name,expected_path:tool.path,observed_path:found?.path??null});}
  for(const name of Object.keys(result))if(name.toUpperCase()==='PATH')delete result[name];
  result.PATH=[...new Set([...ordered,...inherited.split(delimiter).filter(Boolean)])].join(delimiter);
  return result;
}

// Host evidence stays in the Run journal. Workers need only usable locations.
export function nodeRuntimeScope(state,pins,nodeId){
  const node=pins.root.workflow.nodes.find(item=>item.id===nodeId);
  requireValue(node,'NODE_MISSING','Workflow node does not exist',{node_id:nodeId});
  if(node.runtime_requirements===undefined)return null;
  const declared=normalizeNodeRuntimeRequirements(node.runtime_requirements);
  const requirements={executables:normalizeExecutableRequirements([...runtimeRequirementsForState(state).executables,...declared.executables])};
  return {node_id:nodeId,requirements,source_requirement_ids:declared.source_requirement_ids,
    scope_sha256:digest(canonicalJSON({pins_hash:state.pins_hash,node_id:nodeId,requirements,source_requirement_ids:declared.source_requirement_ids}))};
}
export const runtimeEnvironmentPathsHash=environment=>digest(canonicalJSON((environment?.tools??[]).map(({name,status,path})=>({name,status,path})).sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0)));
function dependencyVerificationBinding(record,nodeId,attemptId){
  const node=record.state.nodes[nodeId],attempt=node?.attempts.find(item=>item.id===attemptId);
  return canonicalJSON({pins_hash:record.state.pins_hash,permissions:record.state.permissions,
    scope_sha256:nodeRuntimeScope(record.state,record.pins,nodeId)?.scope_sha256,
    ...(attemptId===undefined?{}:{active_attempt_id:node?.active_attempt_id,attempt:{id:attempt?.id,
      lease_hash:attempt?.lease_hash,lease_generation:attempt?.lease_generation??0,runtime_environment_scope:attempt?.runtime_environment_scope}})});
}
export function runtimeEnvironmentForWorker(state,node,pins) {
  const scope=node?.runtime_requirements!==undefined&&pins?nodeRuntimeScope(state,pins,node.id):null;
  const binding=scope?state.nodes[node.id]?.runtime_environment_binding:null;
  if(scope)requireValue(binding?.scope_sha256===scope.scope_sha256&&binding.environment?.status==='ready','ENVIRONMENT_BINDING_STALE','Node executable environment has no exact verified scope',{node_id:node.id,scope_sha256:scope.scope_sha256});
  const environment = scope?binding.environment:runtimeEnvironmentForState(state);
  return environment ? { status: environment.status, tools: environment.tools.map(({name,status,path}) => ({name,status,path})),...(scope?{scope_sha256:scope.scope_sha256}:{}) } : null;
}

export async function ensureRunRuntimeEnvironment(runtime, runId, { control_token, expected_sequence, extraDirectories = [],node_id,attempt_id,lease_token },auditedRecord=null,commit=null) {
  // Internal immediate-call reuse only. This fourth argument is never model
  // input, never persisted and never crosses execution/environment effects.
  const record = auditedRecord??await withRunStorePurpose('dependency_pre',()=>runtime.authorizedRun(runId, {control_token}));
  requireValue(record.state.run_id===runId&&digest(control_token)===record.state.control_hash,
    'RUN_AUTHORITY','Environment preparation requires its exact audited controller');
  requireValue(expected_sequence === undefined || expected_sequence === record.sequence, 'RUN_SEQUENCE_CONFLICT', 'Run changed before dependency verification');
  const scope=node_id?nodeRuntimeScope(record.state,record.pins,node_id):null;
  const admission=state=>{
    requireValue(state.status==='running','RUN_NOT_RUNNING','Run stopped during dependency preparation');
    if(attempt_id!==undefined){const node=state.nodes[node_id],attempt=node?.attempts.find(item=>item.id===attempt_id);
      requireValue(attempt&&typeof lease_token==='string'&&digest(lease_token)===attempt.lease_hash,'LEASE_INVALID','Dependency preparation needs the exact lease');
      requireValue(node.active_attempt_id===attempt_id&&['claimed','running'].includes(attempt.status),'STALE_LEASE','Dependency preparation lease is inactive');}
    if(!scope)return;
    const node=state.nodes[node_id];
    requireValue(node&&['ready','claimed','running'].includes(node.status),'NODE_NOT_READY','Scoped dependency preparation requires a selected executable node',{node_id});
    if(attempt_id!==undefined){const attempt=node.attempts.find(item=>item.id===attempt_id);
      requireValue(attempt&&typeof lease_token==='string'&&digest(lease_token)===attempt.lease_hash,'LEASE_INVALID','Scoped dependency verification needs the exact lease');
      requireValue(node.active_attempt_id===attempt_id&&['claimed','running'].includes(attempt.status),'STALE_LEASE','Scoped dependency verification lease is inactive');
      const binding=node.runtime_environment_binding;
      requireValue(attempt.runtime_environment_scope?.scope_sha256===scope.scope_sha256&&binding?.scope_sha256===scope.scope_sha256
        &&attempt.runtime_environment_scope.paths_sha256===runtimeEnvironmentPathsHash(binding.environment),
        'ENVIRONMENT_BINDING_STALE','Claimed node executable paths differ from its exact admission binding',{node_id,scope_sha256:scope.scope_sha256});
    }
  };
  admission(record.state);
  const requirements = scope?.requirements??runtimeRequirementsForState(record.state);
  const prior=scope?record.state.nodes[node_id].runtime_environment_binding:null;
  const pinned = scope?(prior?.scope_sha256===scope.scope_sha256?prior.environment:null):runtimeEnvironmentForState(record.state);
  const attentionApplies=scope?record.state.environment_attention?.node_id===node_id:record.state.environment_attention&&!record.state.environment_attention.node_id;
  // Only fixed Host call sites supply this synchronous commit phase. The
  // verifier/resolver has settled before a new writer/transaction is acquired.
  const finish=async(environment,observed=record)=>{
    const complete=async()=>{
      const current=await withRunStorePurpose('dependency_post',()=>runtime.authorizedRun(runId,{control_token}));
      // Explicit caller CAS remains strict. Implicit verification follows its
      // actual dependencies: sibling progress/receipts do not change executable
      // authority, while pins, scopes, permissions or lease changes still fail.
      if(scope&&expected_sequence!==undefined)requireValue(current.sequence===observed.sequence,'RUN_SEQUENCE_CONFLICT','Run changed during scoped dependency verification');
      admission(current.state);
      if(scope)requireValue(dependencyVerificationBinding(current,node_id,attempt_id)===dependencyVerificationBinding(observed,node_id,attempt_id),
        'ENVIRONMENT_BINDING_STALE','Execution binding changed during scoped dependency verification');
      const currentScope=node_id?nodeRuntimeScope(current.state,current.pins,node_id):null;
      requireValue(canonicalJSON(currentScope?.requirements??runtimeRequirementsForState(current.state))===canonicalJSON(requirements),
        'ENVIRONMENT_BINDING_STALE','Dependency requirements changed during verification');
      const bound=currentScope?current.state.nodes[node_id].runtime_environment_binding?.environment:runtimeEnvironmentForState(current.state);
      requireValue(canonicalJSON(bound)===canonicalJSON(environment),'ENVIRONMENT_BINDING_STALE','Dependency paths changed during verification');
      const prepared={environment,sequence:current.sequence,record:current,...(scope?{scope_sha256:scope.scope_sha256}:{})};
      return commit?commit.action(prepared):prepared;
    };
    return commit?runtime.runs.withHostTransaction(runId,commit.phase,complete):complete();
  };
  if (!requirements.executables.length) {
    const prepared={environment:pinned,sequence:record.sequence,record};
    return commit?runtime.runs.withHostTransaction(runId,commit.phase,async()=>commit.action({...prepared,record:await runtime.authorizedRun(runId,{control_token})})):prepared;
  }
  await runtime.assertAncestors(record.pins);
  requireValue(record.state.status === 'running', 'RUN_NOT_RUNNING', 'Runtime dependencies can only be rebound for a running Run');
  let stale;
  try {
    assertOutsideHostRunTransaction();
    await runtime.environmentVerifier(requirements, pinned);
    if (!attentionApplies) {
      return finish(pinned);
    }
  } catch (error) {
    if (error.code !== 'ENVIRONMENT_BINDING_STALE') throw error;
    stale = { code: error.code, dependency: error.dependency ?? error.details?.dependency ?? null,
      reason: error.reason ?? error.details?.reason ?? error.message, cause_code: error.cause_code ?? error.details?.cause_code ?? null };
  }
  assertOutsideHostRunTransaction();
  const resolved = await runtime.environmentResolver(requirements, {extraDirectories,knownDirectories:workspaceRuntimeDirectories(record.state.permissions.workspace)});
  const environment=scope?{...resolved,scope_sha256:scope.scope_sha256}:resolved;
  if(scope&&attempt_id!==undefined&&environment.status==='ready'){
    const attempt=record.state.nodes[node_id].attempts.find(item=>item.id===attempt_id);
    requireValue(attempt.runtime_environment_scope.paths_sha256===runtimeEnvironmentPathsHash(environment),'ENVIRONMENT_BINDING_STALE',
      'Scoped executable re-registration changed the paths of an admitted attempt',{node_id,scope_sha256:scope.scope_sha256,
        expected_paths_sha256:attempt.runtime_environment_scope.paths_sha256,observed_paths_sha256:runtimeEnvironmentPathsHash(environment)});
  }
  const attention = environment.status !== 'ready';
  // Keep the initial constraints and immutable pins intact. Each re-registration
  // is an explicit journal transition, not a rewrite of previous evidence.
  const result = await runtime.transition(runId, attention ? 'runtime_environment_attention' : 'runtime_environment_rebound', state => {
    requireValue(state.status === 'running', 'RUN_NOT_RUNNING', 'Run stopped during dependency verification');
    admission(state);
    if (attention) {
      state.environment_attention = { ...environment, ...(scope?scope:{}), ...(stale ? {cause:stale} : {}) };
    } else {
      if(scope){
        const generation=(state.nodes[node_id].runtime_environment_binding?.generation??0)+1;
        state.nodes[node_id].runtime_environment_binding={...scope,environment,generation,verified_at:new Date().toISOString(),
          previous_sha256:digest(canonicalJSON(pinned)),current_sha256:digest(canonicalJSON(environment)),...(stale?{cause:stale}:{})};
      }else{
      state.runtime_environment = environment;
      state.environment_generation = (state.environment_generation ?? 0) + 1;
      state.environment_rebinding = { generation: state.environment_generation, previous_sha256: digest(canonicalJSON(pinned)),
        current_sha256: digest(canonicalJSON(environment)), verified_at: new Date().toISOString(), ...(stale ? {cause:stale} : {}) };
      }
      if(attentionApplies||!state.environment_attention)state.environment_attention = null;
    }
    state.updated_at = new Date().toISOString();
  }, {expected_sequence: record.sequence});
  requireValue(!attention, 'ENVIRONMENT_SETUP_REQUIRED', '运行依赖需要重新注册；已搜索本机，安装前需要用户同意。', {environment:attention?{...environment,...(scope?scope:{})}:environment});
  return finish(environment,result);
}
