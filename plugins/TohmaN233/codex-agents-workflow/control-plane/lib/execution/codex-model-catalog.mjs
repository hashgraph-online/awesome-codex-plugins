import { requireValue } from '../workflow-paths.mjs';

// Account-specific inventory must be observed after login. Anonymous built-in
// metadata cannot decide whether an authenticated account has a newer model.
export async function authenticatedModel(client, model, effort, onCatalog = async () => {}) {
  const account = await client.call('account/read', { refreshToken: false });
  requireValue(account && typeof account.requiresOpenaiAuth === 'boolean', 'CODEX_AUTH_SCHEMA', 'Unsupported account metadata response');
  requireValue(account.account || account.requiresOpenaiAuth === false, 'CODEX_AUTH_REQUIRED', 'Authenticate before resolving the pinned model');
  const models = []; const cursors = new Set(); let cursor;
  do {
    requireValue(cursors.size < 20, 'CODEX_MODEL_SCHEMA', 'Model pagination exceeded its bounded page count');
    const page = await client.call('model/list', { includeHidden: true, limit: 100, ...(cursor ? { cursor } : {}) });
    requireValue(Array.isArray(page.data) && models.length + page.data.length <= 1000, 'CODEX_MODEL_SCHEMA', 'Invalid or excessive public model inventory');
    models.push(...page.data); cursor = page.nextCursor;
    requireValue(!cursor || typeof cursor === 'string' && !cursors.has(cursor), 'CODEX_MODEL_SCHEMA', 'Repeated/invalid model pagination cursor');
    if (cursor) cursors.add(cursor);
  } while (cursor);
  const matches = models.filter(item => item.model === model);
  await onCatalog({ requested_model: model, requested_effort: effort, inventory_count: models.length,
    match_count: matches.length, effort_supported: matches.length === 1 && Boolean(matches[0].supportedReasoningEfforts?.some(item => item.reasoningEffort === effort)),
    model_ids: models.map(item => item.model).filter(item => typeof item === 'string' && /^[A-Za-z0-9._:/-]{1,128}$/.test(item)).join(',').slice(0,4096) });
  requireValue(matches.length === 1, 'CODEX_MODEL_UNAVAILABLE', `Authenticated App Server model/list did not uniquely return ${model} (matches: ${matches.length}, inventory: ${models.length})`);
  requireValue(matches[0].supportedReasoningEfforts?.some(item => item.reasoningEffort === effort), 'CODEX_MODEL_UNAVAILABLE', `Authenticated model ${model} does not advertise reasoning effort ${effort}`);
  return matches[0];
}
