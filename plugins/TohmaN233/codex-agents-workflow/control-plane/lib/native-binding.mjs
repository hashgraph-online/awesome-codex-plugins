import { NATIVE_BUILTINS_PROFILE_NAME, verifyInstalledNativeContextProfile } from '../../scripts/native-context-profile.mjs';

// This named platform profile controls tool/catalog exposure only. Workbench
// Roles still own reusable behavior; arbitrary platform roles remain rejected.
export const NATIVE_TOOL_CONTEXT_PROFILES = Object.freeze(['default', NATIVE_BUILTINS_PROFILE_NAME]);

export function nativeContextExecutionIssue(provider, { executor, skillPolicy, hostManagedNative = false } = {}) {
  if (provider?.kind !== 'native_agent' || provider.config?.agent_type !== NATIVE_BUILTINS_PROFILE_NAME) return null;
  if (executor?.kind === 'provider' && skillPolicy?.mode === 'cooperative' && !hostManagedNative) return null;
  return { code: 'NATIVE_CONTEXT_PROFILE_EXECUTION_UNSUPPORTED', provider_id: provider.id,
    message: 'The builtins tool context profile requires the Cooperative recorded-child spawn bridge; task threads, Strict and managed native sessions cannot apply it.' };
}

export function nativeBindingIssue(provider, { verifyProfile = verifyInstalledNativeContextProfile } = {}) {
  if (provider?.kind !== 'native_agent') return null;
  const config = provider.config ?? {};
  if (config.agent_type === undefined || config.agent_type === 'default') return null;
  if (config.agent_type === NATIVE_BUILTINS_PROFILE_NAME) {
    if (config.fresh_context === false) return { code: 'NATIVE_CONTEXT_PROFILE_HISTORY', provider_id: provider.id,
      message: 'The builtins tool context profile requires fresh context; inherited history can retain ambient catalogs.',
      expected: { fresh_context: true }, actual: { fresh_context: false } };
    try { verifyProfile(config.agent_type); }
    catch (error) {
      return { code: error.code ?? 'NATIVE_CONTEXT_PROFILE_UNAVAILABLE', provider_id: provider.id,
        message: error.message, expected: { agent_type: NATIVE_BUILTINS_PROFILE_NAME, installed_profile: true },
        actual: { installed_profile: false } };
    }
    return null;
  }
  return { code: 'NATIVE_PROVIDER_AGENT_TYPE', provider_id: provider.id,
    message: `Provider ${provider.id} must use a supported native tool context profile. Choose behavior through a Workbench Role, not a second Agent definition.`,
    expected: { agent_types: NATIVE_TOOL_CONTEXT_PROFILES }, actual: { agent_type: config.agent_type ?? null } };
}

export function nativeSpawnConfig(provider, options) {
  const issue = nativeBindingIssue(provider, options);
  if (issue) throw Object.assign(new Error(issue.message), issue);
  const config = provider.config;
  return { agent_type: config.agent_type ?? 'default',
    fork_turns: config.fresh_context === false ? 'all' : 'none',
    model: config.model, reasoning_effort: config.reasoning_effort };
}
