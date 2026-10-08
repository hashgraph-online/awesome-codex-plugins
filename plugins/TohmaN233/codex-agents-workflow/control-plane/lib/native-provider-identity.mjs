export const BUILTIN_NATIVE_AGENT_PROFILES = Object.freeze({
  'native-luna': Object.freeze({ model: 'gpt-6-luna', reasoning_effort: 'max', role: 'advisor', agent_type: 'default' }),
  'native-sol': Object.freeze({ model: 'gpt-6.1-sol', reasoning_effort: 'high', role: 'advisor', agent_type: 'default' }),
  'native-astra': Object.freeze({ model: 'gpt-6-astra', reasoning_effort: 'medium', role: 'advisor', agent_type: 'default' }),
});

// A Provider represents one real execution connection. Role behaviour belongs
// to editable Roles and Workflow nodes, so one model/effort pair must not be
// duplicated under planning, implementation, or repair aliases.
export const BUILTIN_NATIVE_PROVIDER_METADATA = Object.freeze({
  'native-luna': Object.freeze({
    name: 'GPT-6 Luna / Max',
    description: 'Native Codex model connection for routine bounded implementation Roles.',
  }),
  'native-sol': Object.freeze({
    name: 'GPT-6.1 Sol / High',
    description: 'Native Codex model connection for complex implementation, repository analysis, and independent review Roles.',
  }),
  'native-astra': Object.freeze({
    name: 'GPT-6 Astra / Medium',
    description: 'Native Codex model connection for planning, brainstorming, and focused problem-solving Roles.',
  }),
});

export const RETIRED_NATIVE_PROVIDER_IDS = Object.freeze({
  'native-terra': 'native-sol',
  'native-luna-complex': 'native-sol',
  'native-luna-planner': 'native-astra',
  'native-luna-solver': 'native-astra',
  'native-reviewer': 'native-sol',
  'native-reviewer-low': 'native-sol',
  'native-generation-reviewer': 'native-sol',
  'native-authoring-astra-low': 'native-astra',
  'native-astra-solver': 'native-astra',
});

export function canonicalNativeProviderId(providerId) {
  return RETIRED_NATIVE_PROVIDER_IDS[providerId] ?? providerId;
}

export function canonicalizeRoutingProviderIds(rules) {
  const result = structuredClone(rules);
  for (const route of Object.values(result?.routes ?? {})) {
    if (typeof route?.provider_id === 'string') route.provider_id = canonicalNativeProviderId(route.provider_id);
    delete route?.role_id;
    delete route?.write_role_id;
  }
  if (typeof result?.generation?.planner_provider_id === 'string') {
    result.generation.planner_provider_id = canonicalNativeProviderId(result.generation.planner_provider_id);
  }
  if (typeof result?.generation?.review_provider_id === 'string') {
    result.generation.review_provider_id = canonicalNativeProviderId(result.generation.review_provider_id);
  }
  return result;
}
