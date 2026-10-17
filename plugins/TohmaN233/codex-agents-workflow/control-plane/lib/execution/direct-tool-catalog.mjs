import { readFile } from 'node:fs/promises';
import { isAbsolute, join } from 'node:path';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { ensureDirectory, requireValue } from '../workflow-paths.mjs';
import { writeDurableJSON } from '../workflow-events.mjs';

export async function prepareInheritedToolCatalog({ metadata, model, directory }) {
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
  const javascriptAggregation=metadata.tool_mode==null?null:['code_mode','code_mode_only','codemode'].includes(metadata.tool_mode);
  // Match upstream Lite's client-executed search selection without changing
  // authenticated metadata or the user's web-search mode.
  const standaloneWebSearch=metadata.use_responses_lite===true&&javascriptAggregation===true;

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
  // Ordinary Cooperative workers inherit the authenticated native shell, just
  // as they inherit code mode and search. Owned Workflow program tools are
  // additional resource interfaces, not replacements for ordinary commands.
  // Legacy metadata without this required catalog field retains its existing
  // disabled-shell adapter; do not invent an observed native capability.
  if (!Object.hasOwn(catalogModel, 'shell_type')) {
    added_fields.push('shell_type');
    catalogModel.shell_type = 'disabled';
  }

  const catalog = { models: [catalogModel] };
  const directoryPath = await ensureDirectory(directory);
  const path = join(directoryPath, 'models-direct.json');
  await writeDurableJSON(path, catalog);
  const sha256 = digest(await readFile(path));
  return { path, sha256, source_sha256, changed_fields, added_fields,
    execution_overrides:standaloneWebSearch?['features.standalone_web_search=true']:[],
    interface: { source_tool_mode: metadata.tool_mode ?? null, execution_tool_mode: metadata.tool_mode ?? null,
      javascript_aggregation:javascriptAggregation, changed_fields, added_fields,
      native_shell: { source: metadata.shell_type ?? null, execution: catalogModel.shell_type },
      ...(standaloneWebSearch?{standalone_web_search:{source:'authenticated_model_metadata',
        basis:'use_responses_lite_and_javascript_aggregation',source_use_responses_lite:true,execution_override:true}}:{}) } };
}

// Keep the exported API for existing callers; routing is inherited, never forced.
export const prepareDirectToolCatalog = prepareInheritedToolCatalog;
