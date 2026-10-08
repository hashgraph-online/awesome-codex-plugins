import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, rm, symlink, writeFile } from 'node:fs/promises';
import { join, sep } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { createDraft, validateWorkflowShape } from '../lib/workflow-schema.mjs';
import { validateWorkflowGraph } from '../lib/workflow-validator.mjs';
import { managedNativeResultSchema } from '../lib/execution/host-main-automation.mjs';
import { codexStructuredSchema } from '../lib/execution/codex-structured-output.mjs';
import {
  WORKSPACE_SOURCE_LOCATIONS, WORKSPACE_SOURCE_LOCATIONS_SCHEMA,
  revalidateBoundSourceLocations, validateWorkspaceSourceLocations,
} from '../lib/workspace-source-locations.mjs';
import { boundedCompletionDiagnostic } from '../lib/execution/completion-preflight.mjs';

const sha = value => createHash('sha256').update(value).digest('hex');
async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'source-locations-'));
  const workspace = join(root, 'workspace');
  await mkdir(workspace);
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const content = 'export function calculate(value) {\n  return value + 1;\n}\n';
  await writeFile(join(workspace, 'source.mjs'), content);
  return { root, workspace, content,
    location: { path: 'source.mjs', file_sha256: sha(content), start_line: 1, end_line: 2,
      symbol: 'calculate', usage: 'Call calculate with the supplied value.' } };
}

test('valid bounded locations and an absent marker preserve legacy shape', async t => {
  const f = await fixture(t);
  assert.deepEqual(await validateWorkspaceSourceLocations([f.location], f.workspace), { verified: 1, canonical_locations:[f.location] });
  assert.deepEqual(await validateWorkspaceSourceLocations([{ ...f.location, symbol: '' }], f.workspace), { verified: 1, canonical_locations:[{ ...f.location, symbol: '' }] });
  const old = createDraft('legacy', 'Legacy output');
  old.nodes = [{ id: 'source', type: 'agent', outputs_schema: { type: 'object', properties: { result: { type: 'string' } }, required: ['result'], additionalProperties: false } }];
  assert.equal(validateWorkflowShape(old), old);
  await assert.rejects(validateWorkspaceSourceLocations([], f.workspace), { code: 'SOURCE_LOCATION_INVALID', reason: 'schema_invalid' });
});

test('absolute and relative in-workspace locations canonicalize identically without weakening evidence', async t => {
  const f=await fixture(t);
  await mkdir(join(f.workspace,'nested','module'),{recursive:true});
  await writeFile(join(f.workspace,'nested','module','source.mjs'),f.content);
  const relativePath='nested/module/source.mjs',absolutePath=join(f.workspace,'nested','module','source.mjs');
  const item={...f.location,path:relativePath};
  const expected={verified:1,canonical_locations:[item]};
  assert.deepEqual(await validateWorkspaceSourceLocations([item],f.workspace),expected);
  assert.deepEqual(await validateWorkspaceSourceLocations([{...item,path:absolutePath}],f.workspace),expected);
  assert.deepEqual(await validateWorkspaceSourceLocations([{...item,path:'./nested/module/source.mjs'}],f.workspace),expected);
  assert.deepEqual(await validateWorkspaceSourceLocations([{...item,path:'nested/module/../module/source.mjs'}],f.workspace),expected);
  assert.deepEqual(await validateWorkspaceSourceLocations([{...item,path:`${f.workspace}${sep}nested${sep}module${sep}..${sep}module${sep}source.mjs`}],f.workspace),expected);
  if(process.platform==='win32') {
    assert.match(absolutePath,/^[A-Za-z]:\\/);
    assert.deepEqual(await validateWorkspaceSourceLocations([{...item,path:absolutePath.replaceAll('\\','/')}],f.workspace),expected);
    assert.deepEqual(await validateWorkspaceSourceLocations([{...item,path:'nested\\module\\source.mjs'}],f.workspace),expected);
  }
  await writeFile(join(f.root,'outside.mjs'),f.content);
  await assert.rejects(validateWorkspaceSourceLocations([{...item,path:join(f.root,'outside.mjs')}],f.workspace),{code:'SOURCE_LOCATION_INVALID',reason:'path_escape'});
  await assert.rejects(validateWorkspaceSourceLocations([{...item,path:`${f.workspace}${sep}..${sep}outside.mjs`}],f.workspace),{code:'SOURCE_LOCATION_INVALID',reason:'path_escape'});
  await assert.rejects(validateWorkspaceSourceLocations([{...item,file_sha256:'0'.repeat(64),path:absolutePath}],f.workspace),{code:'SOURCE_LOCATION_INVALID',reason:'file_sha256_mismatch'});
  await assert.rejects(validateWorkspaceSourceLocations([{...item,symbol:'combined/label',path:absolutePath}],f.workspace),{code:'SOURCE_LOCATION_INVALID',reason:'symbol_anchor_missing'});
});

test('marked output needs the canonical location schema', () => {
  const workflow = createDraft('marked', 'Marked output');
  workflow.nodes = [{ id: 'source', type: 'agent', output_validators: { locations: WORKSPACE_SOURCE_LOCATIONS },
    outputs_schema: { type: 'object', properties: { locations: structuredClone(WORKSPACE_SOURCE_LOCATIONS_SCHEMA) }, required: ['locations'], additionalProperties: false } }];
  assert.equal(validateWorkflowShape(workflow), workflow);
  workflow.nodes[0].outputs_schema.properties.locations.items.properties.usage.maxLength = 501;
  assert.throws(() => validateWorkflowShape(workflow), { code: 'OUTPUT_VALIDATORS' });
});

test('a marked native Agent passes full workflow and strict model-output preparation', () => {
  const workflow = createDraft('marked-agent', 'Marked native Agent');
  workflow.status = 'ready';
  workflow.finalization = { required: true, node_id: 'final' };
  workflow.skill_policy = { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] };
  const source = { id: 'source', type: 'agent', executor: { kind: 'provider', provider_id: 'native' }, role: 'advisor',
    access: 'read_only', prompt_template: 'Locate the required source interface.', approval: { required: false },
    retry: { max_attempts: 1 }, input_bindings: {}, output_validators: { locations: WORKSPACE_SOURCE_LOCATIONS },
    outputs_schema: { type: 'object', properties: { locations: structuredClone(WORKSPACE_SOURCE_LOCATIONS_SCHEMA) },
      required: ['locations'], additionalProperties: false } };
  workflow.nodes = [{ id: 'start', type: 'start' }, source,
    { id: 'final', type: 'agent', executor: { kind: 'main' }, role: 'finalizer', access: 'read_only',
      prompt_template: 'Accept the source location.', approval: { required: false }, retry: { max_attempts: 1 },
      input_bindings: { locations: '/nodes/source/output/locations' } },
    { id: 'end', type: 'end' }];
  workflow.edges = [
    { id: 'start-source', source: 'start', target: 'source' },
    { id: 'source-final', source: 'source', target: 'final' },
    { id: 'final-end', source: 'final', target: 'end' },
  ];
  const checked = validateWorkflowGraph(workflow, { providers: [{ id: 'native', kind: 'native_agent', enabled: true,
    capabilities: { read: true, write: true }, config: { role: 'advisor' } }] });
  assert.equal(checked.valid, true, JSON.stringify(checked.errors));
  const prepared = managedNativeResultSchema(source);
  assert.deepEqual(prepared.properties.locations.items.required,
    ['path', 'file_sha256', 'start_line', 'end_line', 'symbol', 'usage']);
  assert.equal(prepared.properties.locations.minItems, 1);
  assert.equal(prepared.properties.locations.maxItems, 64);
  const codex = codexStructuredSchema(source.outputs_schema);
  assert.equal(codex.properties.locations.items.properties.symbol.type, 'string');
});

test('location rejects traversal, directory, mismatched hash, range and anchor', async t => {
  const f = await fixture(t);
  const check = (changes, reason) => assert.rejects(
    validateWorkspaceSourceLocations([{ ...f.location, ...changes }], f.workspace),
    { code: 'SOURCE_LOCATION_INVALID', reason });
  await check({ path: '../outside.mjs' }, 'path_escape');
  await check({ path: '.' }, 'not_regular_file');
  await check({ path: 'subdir' }, 'path_unavailable');
  await mkdir(join(f.workspace, 'subdir'));
  await check({ path: 'subdir' }, 'not_regular_file');
  await check({ file_sha256: '0'.repeat(64) }, 'file_sha256_mismatch');
  await check({ start_line: 1, end_line: 100 }, 'line_range_invalid');
  await check({ symbol: 'unknownSymbol' }, 'symbol_anchor_missing');
  await check({ symbol: undefined }, 'schema_invalid');
  await check({ usage: 'x'.repeat(501) }, 'schema_invalid');
  const longSource = Array.from({ length: 165 }, (_, index) => `line ${index + 1}`).join('\n');
  await writeFile(join(f.workspace, 'long.mjs'), longSource);
  const longLocation={...f.location,path:'long.mjs',file_sha256:sha(longSource),start_line:1,end_line:165,symbol:'line 1'};
  assert.equal((await validateWorkspaceSourceLocations([longLocation],f.workspace)).verified,1);
  await check({...longLocation,end_line:166},'line_range_invalid');
  await check({...longLocation,start_line:166,end_line:165},'line_range_invalid');
  await assert.rejects(validateWorkspaceSourceLocations([{...f.location,path:'../outside.mjs'}],f.workspace,{producer_node_id:'work',output_name:'locations'}),error=>error.code==='SOURCE_LOCATION_INVALID'&&error.reason==='path_escape'&&error.index===0&&error.path==='../outside.mjs'&&error.message.includes('locations[0]'));
  await assert.rejects(validateWorkspaceSourceLocations([{...f.location,path:'source\0.mjs'}],f.workspace,{producer_node_id:'work',output_name:'locations'}),error=>error.reason==='path_invalid'&&error.cause_code==='INVALID_SOURCE_PATH'&&error.message.includes('locations[0]'));
});

test('out-of-file range reports the declared 103-146 interval and actual 142 lines to correction', async t => {
  const f = await fixture(t);
  const content = Array.from({ length: 142 }, (_, index) => `line ${index + 1}`).join('\n');
  await writeFile(join(f.workspace, 'views.py'), content);
  const location = { ...f.location, path: 'views.py', file_sha256: sha(content), start_line: 103, end_line: 146, symbol: '' };
  await assert.rejects(validateWorkspaceSourceLocations([location], f.workspace, { producer_node_id: 'analysis', output_name: 'locations' }), error => {
    assert.equal(error.code, 'SOURCE_LOCATION_INVALID'); assert.equal(error.reason, 'line_range_invalid');
    assert.equal(error.index, 0); assert.equal(error.start_line, 103); assert.equal(error.end_line, 146);
    assert.equal(error.actual_line_count, 142);
    assert.match(error.message, /declared_lines=103-146 actual_line_count=142/);
    assert.deepEqual(boundedCompletionDiagnostic(error), {
      code: 'SOURCE_LOCATION_INVALID', reason: 'line_range_invalid', index: 0, path: 'views.py',
      start_line: 103, end_line: 146, actual_line_count: 142, message: error.message,
    });
    return true;
  });
});

test('location rejects a symlink escape', async t => {
  const f = await fixture(t);
  const outside = join(f.root, 'outside');
  await mkdir(outside);
  await writeFile(join(outside, 'source.mjs'), f.content);
  await symlink(outside, join(f.workspace, 'linked'), process.platform === 'win32' ? 'junction' : 'dir');
  await assert.rejects(validateWorkspaceSourceLocations([{ ...f.location, path: 'linked/source.mjs' }], f.workspace),
    { code: 'SOURCE_LOCATION_INVALID', reason: 'path_unavailable' });
  await assert.rejects(validateWorkspaceSourceLocations([{ ...f.location, path: join(f.workspace,'linked','source.mjs') }], f.workspace),
    { code: 'SOURCE_LOCATION_INVALID', reason: 'path_unavailable' });
});

test('revalidation checks only selected marked upstream bindings', async t => {
  const f = await fixture(t);
  const producer = { id: 'source', output_validators: { locations: WORKSPACE_SOURCE_LOCATIONS } };
  const consumer = { id: 'write', input_bindings: { handoff: '/nodes/source/output/locations/0/usage' } };
  const pins = { root: { workflow: { nodes: [producer, consumer] } } };
  const state = { permissions: { workspace: f.workspace }, inputs: {}, nodes: { source: { output: { locations: [f.location] } }, write: { output: null } } };
  assert.deepEqual(await revalidateBoundSourceLocations(consumer, state, pins), { verified: 1 });
  await writeFile(join(f.workspace, 'source.mjs'), f.content + '// changed\n');
  await assert.rejects(revalidateBoundSourceLocations(consumer, state, pins), {
    code: 'SOURCE_LOCATION_STALE', reason: 'file_sha256_mismatch', producer_node_id: 'source', output_name: 'locations', path: 'source.mjs',
  });
  assert.deepEqual(await revalidateBoundSourceLocations({ id: 'write', input_bindings: {} }, state, pins), { verified: 0 });
  assert.deepEqual(await revalidateBoundSourceLocations({ id: 'write', input_bindings: { other: '/nodes/source/output/other' } }, state, pins), { verified: 0 });
});
