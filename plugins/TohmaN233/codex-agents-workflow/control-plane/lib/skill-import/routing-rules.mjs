import { requireValue } from '../workflow-paths.mjs';

export const TASK_TYPES = ['implementation', 'complex_implementation', 'review', 'planning'];
export function routingCatalog(providers = []) {
  return providers.filter(p => p.enabled && p.capabilities?.read).map(p => ({
    id:p.id, kind:p.kind, model:p.config?.model ?? 'client-managed', effort:p.config?.reasoning_effort ?? null,
    role:p.config?.role ?? 'advisor', description:p.description || 'No suitability description supplied; do not infer quality from the ID.',
    capabilities:{read:!!p.capabilities.read,write:!!p.capabilities.write},
  }));
}
export function defaultRoutingRules(providers = []) {
  const presets = { implementation: 'native-luna', complex_implementation: 'native-sol', review: 'native-sol', planning: 'native-astra' };
  const routes=Object.fromEntries(TASK_TYPES.map(type => [type, { provider_id: providers.some(p => p.id === presets[type] && p.enabled) ? presets[type] : '', role: type === 'review' ? 'reviewer' : 'implementer' }]));
  const eligible=providers.filter(provider=>provider.enabled && provider.capabilities?.read);
  const authoringPlanner=providers.some(provider=>provider.id==='native-astra'&&provider.enabled)?'native-astra':routes.planning.provider_id || eligible[0]?.id;
  const authoringReviewer=providers.some(provider=>provider.id==='native-sol'&&provider.enabled)?'native-sol'
    : eligible.find(provider=>provider.config?.role==='reviewer')?.id ?? authoringPlanner;
  return { version: 1, instructions: 'Classify each agent by its responsibility. Use GPT-6 Luna / Max for routine bounded implementation, GPT-6.1 Sol / High for complex implementation and independent review, and GPT-6 Astra / Medium for planning and focused problem solving. Preserve separate review boundaries. Use registered suitability descriptions for automatic selection; fixed mode follows the configured routes. Never grant permissions.',
    selection_mode: 'automatic', routes, generation:{...(authoringPlanner?{planner_provider_id:authoringPlanner}:{}),review_provider_id:authoringReviewer ?? 'native-sol',max_rounds:4} };
}
export function validateRoutingRules(rules) {
  requireValue(rules && rules.version === 1 && typeof rules.instructions === 'string' && rules.instructions.trim() && rules.instructions.length <= 16000 && rules.routes && Object.keys(rules).every(k => ['version','instructions','routes','generation','selection_mode'].includes(k)), 'ROUTING_RULES', 'Routing rules require version 1, instructions and routes');
  requireValue(rules.selection_mode === undefined || ['automatic','fixed'].includes(rules.selection_mode),'ROUTING_RULES','Unknown selection mode');
  requireValue(Object.keys(rules.routes).length === TASK_TYPES.length && TASK_TYPES.every(t => Object.hasOwn(rules.routes,t)), 'ROUTING_RULES', 'Provide one route for every supported task type');
  for (const [type,route] of Object.entries(rules.routes)) requireValue(route && Object.keys(route).every(k => ['provider_id','role'].includes(k)) && typeof route.provider_id === 'string' && route.provider_id.length <= 128 && typeof route.role === 'string' && route.role.trim() && route.role.length <= 64, 'ROUTING_RULES', `Each ${type} route requires a Provider ID and node responsibility`);
  if (rules.generation !== undefined) validateGenerationSettings(rules.generation);
  return structuredClone(rules);
}
export function routeAgent(node, rules, providers, catalog = routingCatalog(providers)) {
  requireValue(TASK_TYPES.includes(node.task_type) && typeof node.routing_reason === 'string' && node.routing_reason.trim() && node.routing_reason.length <= 2000, 'ROUTING_CLASSIFICATION', 'Every routed agent requires task_type and routing_reason');
  requireValue(node.main_mode === undefined || ['worker','orchestration'].includes(node.main_mode), 'MAIN_EXECUTION_MODE', 'Unknown Main context mode');
  if (node.main_mode !== undefined) {
    requireValue([undefined,'main'].includes(node.execution_target) && node.provider_choice === undefined && node.thread_lifecycle === undefined && node.thread_source_node === undefined, 'MAIN_EXECUTION_MODE', 'Explicit Main context modes cannot select a Provider or task lifecycle');
    return {executor:{kind:'main',mode:node.main_mode},role:'advisor'};
  }
  if (rules.selection_mode === 'automatic') {
    requireValue(['main','subagent','thread'].includes(node.execution_target),'ROUTING_CLASSIFICATION','Choose Main, a one-off Provider subagent, or a source-required durable Codex task');
    if (node.execution_target === 'main') {
      requireValue(node.provider_choice === undefined && node.thread_lifecycle === undefined && node.thread_source_node === undefined,'ROUTING_CLASSIFICATION','Main has no Provider/model or Codex task lifecycle selection');
      return {executor:{kind:'main'},role:'advisor'};
    }
    requireValue(catalog.some(p=>p.id===node.provider_choice),'ROUTING_CLASSIFICATION','Subagent must choose a Provider from the pinned candidate catalog');
    const selected=providers.find(p=>p.id===node.provider_choice);
    requireValue(selected?.enabled && selected.capabilities?.read,'ROUTING_PROVIDER_UNAVAILABLE','Choose an enabled registered read-capable Provider');
    if (node.execution_target === 'thread') {
      requireValue(selected.kind === 'native_agent','ROUTING_THREAD_PROVIDER','Codex task threads require a registered native Codex Provider');
      const lifecycle=node.thread_lifecycle ?? 'start';
      requireValue(['start','continue'].includes(lifecycle),'ROUTING_THREAD_LIFECYCLE','Codex task threads must start a task or continue one exact prior task');
      if (lifecycle === 'start') requireValue(node.thread_source_node === undefined,'ROUTING_THREAD_SOURCE','A new Codex task cannot name a source node');
      else requireValue(typeof node.thread_source_node === 'string' && node.thread_source_node.trim(),'ROUTING_THREAD_SOURCE','A continuing Codex task must name its exact source node');
      return {executor:{kind:'thread',provider_id:selected.id,lifecycle,...(lifecycle==='continue'?{source_node:node.thread_source_node}:{})},role:node.task_type==='review'?'reviewer':'implementer'};
    }
    requireValue(node.thread_lifecycle === undefined && node.thread_source_node === undefined,'ROUTING_CLASSIFICATION','Only Codex task threads accept a task lifecycle');
    return {executor:{kind:'provider',provider_id:selected.id},role:node.task_type==='review'?'reviewer':'implementer'};
  }
  requireValue(node.execution_target === undefined && node.provider_choice === undefined,'ROUTING_CLASSIFICATION','Fixed routes do not accept automatic execution choices');
  const rule = rules.routes[node.task_type];
  const provider = providers.find(p => p.id === rule.provider_id);
  requireValue(provider?.enabled && provider.capabilities?.read && (provider.kind !== 'native_agent' || ['advisor', rule.role].includes(provider.config?.role)), 'ROUTING_PROVIDER_UNAVAILABLE', `No eligible enabled Provider for ${node.task_type}; edit the routing rule`, { task_type: node.task_type, provider_id: rule.provider_id });
  return { executor: {kind:'provider',provider_id:provider.id}, role:rule.role };
}

export function validateGenerationSettings(value = {}) {
  requireValue(value && Object.keys(value).every(k=>['review_provider_id','planner_provider_id','max_rounds'].includes(k)), 'GENERATION_SETTINGS', 'Unknown generation setting');
  const result={review_provider_id:'native-sol',max_rounds:4,...value};
  requireValue(typeof result.review_provider_id==='string' && /^[A-Za-z0-9._-]{1,128}$/.test(result.review_provider_id) && Number.isInteger(result.max_rounds) && result.max_rounds>=1 && result.max_rounds<=4,'GENERATION_SETTINGS','Choose a registered reviewer Provider and one to four planner attempts (initial plan plus up to three semantic repairs)');
  requireValue(result.planner_provider_id === undefined || typeof result.planner_provider_id==='string' && /^[A-Za-z0-9._-]{1,128}$/.test(result.planner_provider_id),'GENERATION_SETTINGS','Choose a registered planning Provider');
  return result;
}
