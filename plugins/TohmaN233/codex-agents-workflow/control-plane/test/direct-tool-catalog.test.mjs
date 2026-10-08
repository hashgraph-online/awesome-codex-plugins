import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, readdir, rm } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join } from 'node:path';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { prepareDirectToolCatalog } from '../lib/execution/direct-tool-catalog.mjs';

async function fixture(t) {
  const directory = await mkdtemp(join(tmpdir(), 'direct-tool-catalog-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  return directory;
}

test('preserves rich model metadata while replacing only shell transport and raising its result budget', async t => {
  const directory = await fixture(t);
  const instructions = 'Exact instruction template: preserve every line.\nSecond line: image and clock remain available.';
  const metadata = {
    slug: 'gpt-fixture-rich',
    display_name: 'Fixture model',
    description: 'Metadata fixture',
    tool_mode: 'codemode',
    input_modalities: ['text', 'image', 'audio'],
    supports_image_detail_original: true,
    supports_verbosity: true,
    support_verbosity: { levels: ['low', 'high'], default: 'high' },
    model_messages: {
      instructions_template: instructions,
      nested: { clock: { supports_time: true }, preserved: ['one', { two: 2 }] },
    },
    experimental_supported_tools: ['image', 'clock', 'search'],
    use_responses_lite: false,
    context_window: 256000,
    max_context_window: 512000,
    shell_type: 'unified_exec',
    truncation_policy: { mode: 'tokens', limit: 10000 },
    other_capability: { preserve: true },
  };
  const result = await prepareDirectToolCatalog({ metadata, model: metadata.slug, directory });
  const bytes = await readFile(result.path);
  const catalog = JSON.parse(bytes).models[0];
  const expected = {
    ...metadata,
    base_instructions: instructions,
    supports_parallel_tool_calls: true,
    tool_mode: 'direct',
    shell_type: 'disabled',
    truncation_policy: { mode: 'tokens', limit: 64000 },
  };

  assert.deepEqual(catalog, expected);
  assert.equal(result.path, join(directory, 'models-direct.json'));
  assert.equal(result.source_sha256, digest(Buffer.from(canonicalJSON(metadata), 'utf8')));
  assert.equal(result.sha256, digest(bytes));
  assert.deepEqual(result.changed_fields, ['tool_mode', 'shell_type', 'truncation_policy']);
  assert.deepEqual(result.added_fields, ['base_instructions', 'supports_parallel_tool_calls']);
  assert.equal(catalog.base_instructions, instructions);
  assert.deepEqual(catalog.input_modalities, ['text', 'image', 'audio']);
  assert.deepEqual(catalog.experimental_supported_tools, ['image', 'clock', 'search']);
  assert.equal(catalog.model_messages.nested.clock.supports_time, true);
});

test('preserves existing instructions and an explicit parallel-call capability', async t => {
  const directory = await fixture(t);
  const metadata = {
    slug: 'gpt-fixture-explicit',
    tool_mode: 'direct',
    base_instructions: 'Existing exact instructions',
    supports_parallel_tool_calls: false,
    shell_type: 'disabled',
    truncation_policy: { mode: 'tokens', limit: 64000 },
    model_messages: { instructions_template: 'Do not replace this template.' },
    input_modalities: ['text'],
  };
  const result = await prepareDirectToolCatalog({ metadata, model: metadata.slug, directory });
  const catalog = JSON.parse(await readFile(result.path, 'utf8')).models[0];
  assert.deepEqual(catalog, metadata);
  assert.deepEqual(result.changed_fields, []);
  assert.deepEqual(result.added_fields, []);
});

test('reports tool_mode as added when source metadata omitted it', async t => {
  const directory = await fixture(t);
  const metadata = {
    slug: 'gpt-fixture-no-tool-mode',
    base_instructions: 'Exact existing instructions',
    supports_parallel_tool_calls: true,
    model_messages: { instructions_template: 'Preserve the source template.' },
  };
  const result = await prepareDirectToolCatalog({ metadata, model: metadata.slug, directory });
  const catalog = JSON.parse(await readFile(result.path, 'utf8')).models[0];
  assert.deepEqual(catalog, { ...metadata, tool_mode: 'direct', shell_type: 'disabled', truncation_policy: { mode: 'tokens', limit: 64000 } });
  assert.deepEqual(result.changed_fields, []);
  assert.deepEqual(result.added_fields, ['tool_mode', 'shell_type', 'truncation_policy']);
});

test('model mismatch fails before writing a catalog', async t => {
  const directory = await fixture(t);
  const metadata = { slug: 'observed-model', model_messages: { instructions_template: 'Exact text' } };
  await assert.rejects(prepareDirectToolCatalog({ metadata, model: 'requested-model', directory }), { code: 'DIRECT_TOOL_CATALOG_MODEL' });
  assert.deepEqual(await readdir(directory), []);
});

test('missing both instruction sources fails before writing a catalog', async t => {
  const directory = await fixture(t);
  const metadata = { slug: 'model-without-instructions', tool_mode: 'codemode' };
  await assert.rejects(prepareDirectToolCatalog({ metadata, model: metadata.slug, directory }), { code: 'DIRECT_TOOL_CATALOG_INSTRUCTIONS' });
  assert.deepEqual(await readdir(directory), []);
});
