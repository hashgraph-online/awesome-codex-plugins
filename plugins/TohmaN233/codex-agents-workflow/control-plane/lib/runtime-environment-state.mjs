import { canonicalJSON, digest } from './workflow-revisions.mjs';
import { requireValue } from './workflow-paths.mjs';
import { isAbsolute, join } from 'node:path';

export const workspaceRuntimeDirectories = workspace => typeof workspace==='string'&&isAbsolute(workspace)
  ? ['.venv','venv','env'].flatMap(name=>['Scripts','bin'].map(bin=>join(workspace,name,bin))) : [];

export const runtimeEnvironmentForState = state => state.runtime_environment ?? state.constraints?.runtime_environment ?? null;
export const runtimeRequirementsForState = state => state.constraints?.runtime_requirements ?? {
  executables: (runtimeEnvironmentForState(state)?.tools ?? []).map(tool => tool.name),
};

// Host evidence stays in the Run journal. Workers need only usable locations.
export function runtimeEnvironmentForWorker(state) {
  const environment = runtimeEnvironmentForState(state);
  return environment ? { status: environment.status, tools: environment.tools.map(({name,status,path}) => ({name,status,path})) } : null;
}

export async function ensureRunRuntimeEnvironment(runtime, runId, { control_token, expected_sequence, extraDirectories = [] }) {
  const record = await runtime.runs.read(runId);
  await runtime.authorizeController(runId, {control_token});
  requireValue(expected_sequence === undefined || expected_sequence === record.sequence, 'RUN_SEQUENCE_CONFLICT', 'Run changed before dependency verification');
  const requirements = runtimeRequirementsForState(record.state);
  const pinned = runtimeEnvironmentForState(record.state);
  if (!requirements.executables.length) return { environment: pinned, sequence: record.sequence };
  await runtime.assertAncestors(record.pins);
  requireValue(record.state.status === 'running', 'RUN_NOT_RUNNING', 'Runtime dependencies can only be rebound for a running Run');
  let stale;
  try {
    await runtime.environmentVerifier(requirements, pinned);
    if (!record.state.environment_attention) return { environment: pinned, sequence: record.sequence };
  } catch (error) {
    if (error.code !== 'ENVIRONMENT_BINDING_STALE') throw error;
    stale = { code: error.code, dependency: error.dependency ?? error.details?.dependency ?? null,
      reason: error.reason ?? error.details?.reason ?? error.message, cause_code: error.cause_code ?? error.details?.cause_code ?? null };
  }
  const environment = await runtime.environmentResolver(requirements, {extraDirectories,knownDirectories:workspaceRuntimeDirectories(record.state.permissions.workspace)});
  const attention = environment.status !== 'ready';
  // Keep the initial constraints and immutable pins intact. Each re-registration
  // is an explicit journal transition, not a rewrite of previous evidence.
  const result = await runtime.transition(runId, attention ? 'runtime_environment_attention' : 'runtime_environment_rebound', state => {
    requireValue(state.status === 'running', 'RUN_NOT_RUNNING', 'Run stopped during dependency verification');
    if (attention) {
      state.environment_attention = { ...environment, ...(stale ? {cause:stale} : {}) };
    } else {
      state.runtime_environment = environment;
      state.environment_generation = (state.environment_generation ?? 0) + 1;
      state.environment_rebinding = { generation: state.environment_generation, previous_sha256: digest(canonicalJSON(pinned)),
        current_sha256: digest(canonicalJSON(environment)), verified_at: new Date().toISOString(), ...(stale ? {cause:stale} : {}) };
      state.environment_attention = null;
    }
    state.updated_at = new Date().toISOString();
  }, {expected_sequence: record.sequence});
  requireValue(!attention, 'ENVIRONMENT_SETUP_REQUIRED', '运行依赖需要重新注册；已搜索本机，安装前需要用户同意。', {environment});
  return { environment, sequence: result.sequence };
}
