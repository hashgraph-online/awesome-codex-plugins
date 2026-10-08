import { createReadStream } from 'node:fs';
import { lstat } from 'node:fs/promises';
import { homedir } from 'node:os';
import { isAbsolute, join, relative, sep } from 'node:path';
import { createInterface } from 'node:readline';
import { requireValue } from '../workflow-paths.mjs';
import { withNativeAgentObserver } from './native-agent-observer.mjs';
import { canonicalSessionPath } from './local-session-path.mjs';

const modelId = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$/.test(value);
const effortId = value => typeof value === 'string' && /^[a-z][a-z0-9_-]{0,31}$/.test(value);

// Read only host metadata from the exact caller's journal. Prompts and outputs
// never enter a model context, and no model name is stored in the Workflow.
export async function readMainTurnContext(thread, home) {
  requireValue(typeof thread?.id === 'string' && typeof thread.path === 'string', 'MAIN_MODEL_SESSION', 'Main model inheritance requires the exact caller thread and rollout path');
  requireValue(isAbsolute(thread.path), 'MAIN_MODEL_SESSION_PATH', 'Caller rollout must be an absolute local file');
  // Reject links in the supplied paths, then compare physical identities so
  // Windows short names, casing and extended spellings remain valid.
  const { root, path } = await canonicalSessionPath(thread.path, home), rel = relative(root, path);
  requireValue(rel && rel !== '..' && !rel.startsWith('..' + sep) && !isAbsolute(rel), 'MAIN_MODEL_SESSION_PATH', 'Caller rollout must be inside the selected Codex home sessions directory');
  const stat = await lstat(path);
  requireValue(stat.isFile() && stat.nlink === 1, 'MAIN_MODEL_SESSION_PATH', 'Caller rollout must be a regular file');
  let matched = false, selection;
  const input = createReadStream(path);
  const lines = createInterface({ input, crlfDelay: Infinity });
  try {
    for await (const line of lines) {
      const type = /"type"\s*:\s*"([^"]+)"/.exec(line.slice(0, 4096))?.[1];
      if (type !== 'session_meta' && type !== 'turn_context') continue;
      let row;
      try { row = JSON.parse(line); }
      catch (cause) { throw Object.assign(new Error('Caller session metadata is malformed', { cause }), { code: 'MAIN_MODEL_SESSION_SCHEMA' }); }
      if (row.type === 'session_meta') {
        requireValue(!matched && row.payload?.id === thread.id, 'MAIN_MODEL_SESSION_IDENTITY', 'Caller rollout identity does not match the authenticated thread');
        matched = true;
      } else {
        requireValue(matched && modelId(row.payload?.model), 'MAIN_MODEL_SESSION_SCHEMA', 'Caller turn has no valid model selection');
        selection = { model: row.payload.model, effort: row.payload.effort ?? null };
      }
    }
  } finally { lines.close(); input.destroy(); }
  requireValue(matched && selection, 'MAIN_MODEL_SESSION_CONTEXT', 'Caller session has no current turn model selection');
  return selection;
}

async function resolvedEffort(client, model, effort) {
  if (effortId(effort)) return effort;
  requireValue(effort === null || effort === undefined || effort === '', 'MAIN_MODEL_EFFORT', 'Main reasoning selection is invalid');
  let cursor; const seen = new Set();
  do {
    const page = await client.call('model/list', { includeHidden: true, limit: 100, ...(cursor ? { cursor } : {}) });
    requireValue(Array.isArray(page.data), 'MAIN_MODEL_CATALOG', 'Codex model inventory is invalid');
    const match = page.data.filter(item => item.model === model);
    requireValue(match.length <= 1, 'MAIN_MODEL_CATALOG', 'Codex model inventory contains duplicate model identities');
    if (match.length) {
      requireValue(effortId(match[0].defaultReasoningEffort), 'MAIN_MODEL_EFFORT', 'Selected model has no resolved default reasoning selection');
      return match[0].defaultReasoningEffort;
    }
    cursor = page.nextCursor;
    requireValue(!cursor || typeof cursor === 'string' && !seen.has(cursor), 'MAIN_MODEL_CATALOG', 'Codex model inventory repeats a page');
    if (cursor) seen.add(cursor);
  } while (cursor);
  requireValue(false, 'MAIN_MODEL_UNAVAILABLE', 'Current Main model is absent from the Codex model inventory');
}

export async function resolveMainModelSelection(record, settings, { env = process.env, observe = withNativeAgentObserver } = {}) {
  const parent = record.state?.constraints?.native_parent_thread_id;
  // Explicit settings remain readable for isolated experiments. A real calling
  // chat always owns Main's model selection, even if old settings still exist.
  if (!parent && settings.main_model && settings.main_reasoning_effort) {
    requireValue(modelId(settings.main_model) && effortId(settings.main_reasoning_effort), 'MAIN_MODEL_SELECTION', 'Explicit experiment model selection is invalid');
    return { model: settings.main_model, effort: settings.main_reasoning_effort };
  }
  return observe(async client => {
    let selection;
    if (parent) {
      const result = await client.call('thread/read', { threadId: parent, includeTurns: false });
      requireValue(result.thread?.id === parent, 'MAIN_MODEL_SESSION_IDENTITY', 'Main model lookup returned a different caller thread');
      selection = await readMainTurnContext(result.thread, env.CODEX_HOME || join(homedir(), '.codex'));
    } else {
      const result = await client.call('config/read', { includeLayers: false });
      selection = { model: settings.main_model || result.config?.model, effort: settings.main_reasoning_effort || result.config?.model_reasoning_effort };
    }
    requireValue(modelId(selection.model), 'MAIN_MODEL_SELECTION', 'Codex has no resolved Main model selection');
    return { model: selection.model, effort: await resolvedEffort(client, selection.model, selection.effort) };
  }, { env });
}
