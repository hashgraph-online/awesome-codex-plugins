import { readFile } from 'node:fs/promises';
import { isAbsolute, join } from 'node:path';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { ensureDirectory, requireValue } from '../workflow-paths.mjs';
import { writeDurableJSON } from '../workflow-events.mjs';

export async function prepareDirectToolCatalog({ metadata, model, directory }) {
  requireValue(metadata && typeof metadata === 'object' && !Array.isArray(metadata),
    'DIRECT_TOOL_CATALOG_METADATA', 'Authenticated model metadata must be an object');
  requireValue(typeof model === 'string' && model.length > 0 && metadata.slug === model,
    'DIRECT_TOOL_CATALOG_MODEL', 'Authenticated model metadata must match the requested model');
  requireValue(typeof directory === 'string' && isAbsolute(directory),
    'DIRECT_TOOL_CATALOG_PATH', 'Direct-tool catalog directory must be an absolute Host-selected path');

  const source_sha256 = digest(Buffer.from(canonicalJSON(metadata), 'utf8'));
  const catalogModel = structuredClone(metadata);
  const changed_fields = [];
  const added_fields = [];

  if (!Object.hasOwn(catalogModel, 'base_instructions')) {
    const instructions = catalogModel.model_messages?.instructions_template;
    requireValue(typeof instructions === 'string', 'DIRECT_TOOL_CATALOG_INSTRUCTIONS',
      'Authenticated model metadata has no base instructions or exact instructions template');
    catalogModel.base_instructions = instructions;
    added_fields.push('base_instructions');
  }
  if (!Object.hasOwn(catalogModel, 'supports_parallel_tool_calls')) {
    catalogModel.supports_parallel_tool_calls = true;
    added_fields.push('supports_parallel_tool_calls');
  }
  if (!Object.hasOwn(catalogModel, 'tool_mode')) added_fields.push('tool_mode');
  else if (catalogModel.tool_mode !== 'direct') changed_fields.push('tool_mode');
  catalogModel.tool_mode = 'direct';

  if (!Object.hasOwn(catalogModel, 'shell_type')) added_fields.push('shell_type');
  else if (catalogModel.shell_type !== 'disabled') changed_fields.push('shell_type');
  catalogModel.shell_type = 'disabled';

  const truncation = catalogModel.truncation_policy;
  if (!Object.hasOwn(catalogModel, 'truncation_policy')) added_fields.push('truncation_policy');
  else if (truncation?.mode !== 'tokens' || !Number.isSafeInteger(truncation.limit) || truncation.limit < 64000)
    changed_fields.push('truncation_policy');
  if (truncation?.mode !== 'tokens' || !Number.isSafeInteger(truncation.limit) || truncation.limit < 64000)
    catalogModel.truncation_policy = { mode: 'tokens', limit: 64000 };

  const catalog = { models: [catalogModel] };
  const directoryPath = await ensureDirectory(directory);
  const path = join(directoryPath, 'models-direct.json');
  await writeDurableJSON(path, catalog);
  const sha256 = digest(await readFile(path));
  return { path, sha256, source_sha256, changed_fields, added_fields };
}
