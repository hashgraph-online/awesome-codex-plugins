import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, readdir, rm, stat, writeFile } from 'node:fs/promises';
import filesystem from 'node:fs/promises';
import { syncBuiltinESMExports } from 'node:module';
import { tmpdir } from './physical-tempdir.mjs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { canonicalJSON } from '../lib/workflow-revisions.mjs';
import { materializeNativeTaskBundle, materializeNodeInputs } from '../lib/execution/node-input-materials.mjs';

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'node-input-materials-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  return root;
}

function sha256(value) { return createHash('sha256').update(value).digest('hex'); }

test('serialized JSON inputs never probe the filesystem even with a workspace', async t => {
  const root = await fixture(t), workspace = join(root, 'workspace');
  await mkdir(workspace);
  const value = JSON.stringify([{ payload: 'JSON_PAYLOAD_' + 'x'.repeat(6000) }]);
  const original = filesystem.realpath;
  let probes = 0;
  filesystem.realpath = async (...args) => {
    if (String(args[0]).includes('JSON_PAYLOAD_')) {
      probes++;
      throw Object.assign(new Error('serialized content is not a filename'), { code: 'ENAMETOOLONG' });
    }
    return original(...args);
  };
  syncBuiltinESMExports();
  try {
    const envelope = { workspace, access: 'read_only', node_id: 'writer', inputs: { jobs_json: value }, prompt_template: 'Read assigned jobs.' };
    const result = await materializeNodeInputs({ directory: join(root, 'attempt'), envelope });
    assert.equal(probes, 0);
    assert.equal(result.manifest[0].format, 'json');
    assert.deepEqual(JSON.parse(await readFile(result.manifest[0].path, 'utf8')), JSON.parse(value));
    const native = await materializeNativeTaskBundle({ directory: join(root, 'native'), envelope });
    assert.equal(probes, 0);
    assert.equal(native.bound_input_count, 1);
  } finally {
    filesystem.realpath = original;
    syncBuiltinESMExports();
  }
});

test('filesystem lookup failures for real input addresses remain visible', async t => {
  const root = await fixture(t), path = join(root, 'source.md');
  await writeFile(path, 'source');
  const original = filesystem.realpath;
  filesystem.realpath = async (...args) => {
    if (args[0] === path) throw Object.assign(new Error('address access denied'), { code: 'EACCES' });
    return original(...args);
  };
  syncBuiltinESMExports();
  try {
    await assert.rejects(materializeNodeInputs({ directory: join(root, 'attempt'),
      envelope: { workspace: root, inputs: { source_path: path } } }), { code: 'EACCES' });
  } finally {
    filesystem.realpath = original;
    syncBuiltinESMExports();
  }
});

test('plain semantic inputs that cannot be filesystem names become sidecars with a workspace', async t => {
  const root = await fixture(t), value = 'PLAIN_SEMANTIC_BODY_' + 'x'.repeat(6000);
  const original = filesystem.realpath, originalLstat = filesystem.lstat;
  let probes = 0;
  filesystem.realpath = async (...args) => {
    if (String(args[0]).includes('PLAIN_SEMANTIC_BODY_')) {
      probes++;
      throw Object.assign(new Error('value exceeds the filesystem name limit'), { code: 'ENAMETOOLONG' });
    }
    return original(...args);
  };
  filesystem.lstat = async (...args) => {
    if (String(args[0]).includes('PLAIN_SEMANTIC_BODY_'))
      throw Object.assign(new Error('verified filename exceeds the filesystem name limit'), { code: 'ENAMETOOLONG' });
    return originalLstat(...args);
  };
  syncBuiltinESMExports();
  try {
    const envelope = { workspace: root, access: 'read_only', node_id: 'writer', inputs: { context: value, verification: value },
      prompt_template: '{{context}}\n{{verification}}' };
    const result = await materializeNodeInputs({ directory: join(root, 'attempt'), envelope });
    assert.equal(probes, 2);
    assert.equal(result.manifest.length, 2);
    for (const item of result.manifest) assert.equal(await readFile(item.path, 'utf8'), value);
    assert.equal(result.prompt.includes('PLAIN_SEMANTIC_BODY_'), false);
    const native = await materializeNativeTaskBundle({ directory: join(root, 'native'), envelope });
    assert.equal(native.bound_input_count, 2);
    assert.equal(probes, 4);
    await assert.rejects(materializeNativeTaskBundle({ directory: join(root, 'verified'),
      envelope: { ...envelope, inputs: { packet_path: value, packet_sha256: sha256(value) } } }),
    { code: 'ENAMETOOLONG' }, 'An explicit verified file address must fail rather than become semantic content');
  } finally {
    filesystem.realpath = original;
    filesystem.lstat = originalLstat;
    syncBuiltinESMExports();
  }
});

test('materializes projected inputs as exact sidecars and compiles only local references', async t => {
  const root = await fixture(t);
  const directory = join(root, 'attempt-opaque-🧪', 'partition-A7');
  const unicode = '𠜎雪🌱 e\u0301 🧪';
  const opaqueId = 'Opaque/ID: 𠜎-9f3a';
  const absolute = 'C:\\workspace\\source files\\A🧪.json';
  const relative = '../source files/A🧪.json';
  const context = `CONTEXT_BODY_${unicode}_${opaqueId}_${absolute}_${relative}`;
  const verification = `VERIFY_BODY_${unicode}_${relative}`;
  const validJson = '{"z":"雪","opaque":"' + opaqueId + '","a":[1,true]}';
  const invalidJson = `not valid JSON: ${unicode} ${opaqueId}`;
  const envelope = {
    workflow_id: 'workflow-opaque/7',
    node_id: 'node-opaque 🧩',
    provider: { name: 'Provider fixture' },
    prompt_template: 'Authored requirement: preserve the stated decision.\nTask={{task}}\nContext={{context}}\nVerify={{verification}}',
    inputs: {
      task: 'TASK_BODY_user request',
      context,
      verification,
      opaque_id: opaqueId,
      absolute_path: absolute,
      relative_path: relative,
      valid_json: validJson,
      invalid_json: invalidJson,
    },
    context_projection: {
      mode: 'declared_bindings',
      bindings: ['context', 'verification'],
      references: [{ path: 'workflow-assets/guide.md', sha256: 'a'.repeat(64), bytes: 42 }],
    },
    constraints: { execution_binding: { source: 'host', token: 'example-keep-metadata' } },
    completion_contract: { required: ['result'] },
  };

  const result = await materializeNodeInputs({ directory, envelope });
  assert.equal(result.prompt.includes(envelope.inputs.task), true);
  assert.match(result.prompt, /Authored requirement: preserve the stated decision\./);
  assert.match(result.prompt, /workflow-assets\/guide\.md/);
  assert.match(result.prompt, /Read this bound input from the local file/);
  for (const body of [context, verification, opaqueId, absolute, relative, validJson, invalidJson]) {
    assert.equal(result.prompt.includes(body), false, `input body should stay out of prompt: ${body}`);
  }

  const expectedNames = ['absolute_path', 'context', 'invalid_json', 'opaque_id', 'relative_path', 'valid_json', 'verification'];
  assert.deepEqual(result.manifest.map(item => item.name), expectedNames);
  assert.equal(result.manifest.some(item => item.name.includes('sibling')), false);
  const loaded = new Map();
  for (const item of result.manifest) loaded.set(item.name, await readFile(item.path, 'utf8'));
  assert.equal(loaded.get('context'), context);
  assert.equal(loaded.get('verification'), verification);
  assert.equal(loaded.get('opaque_id'), opaqueId);
  assert.equal(loaded.get('absolute_path'), absolute);
  assert.equal(loaded.get('relative_path'), relative);
  assert.equal(loaded.get('valid_json'), canonicalJSON(JSON.parse(validJson)));
  assert.equal(loaded.get('invalid_json'), invalidJson);

  const index = JSON.parse(await readFile(result.inputs_path, 'utf8'));
  assert.deepEqual(index, { schema_version: 1, inputs: result.manifest });
  assert.equal(result.prompt_sha256, sha256(result.prompt));
  for (const item of result.manifest) assert.equal(item.sha256, sha256(await readFile(item.path)));

  const repeated = await materializeNodeInputs({ directory, envelope });
  assert.deepEqual(repeated, result);
  await assert.rejects(
    materializeNodeInputs({ directory, envelope: { ...envelope, inputs: { ...envelope.inputs, context: context + ' changed' } } }),
    { code: 'NODE_INPUT_MATERIALS_CONFLICT' },
  );
});

test('long context and verification stay in sidecars without prompt field cutoffs', async t => {
  const root = await fixture(t);
  const directory = join(root, 'long-attempt');
  const context = 'LONG_CONTEXT_🧪'.repeat(9000);
  const verification = 'LONG_VERIFY_雪'.repeat(5000);
  const envelope = {
    workspace: root,
    workflow_id: 'opaque-workflow',
    node_id: 'opaque-node',
    prompt_template: 'Task={{task}}\nContext={{context}}\nVerification={{verification}}\nPreserve output schema.',
    inputs: { task: 'task survives', context, verification },
    context_projection: { mode: 'declared_bindings', bindings: ['context', 'verification'], references: [] },
    outputs_schema: { type: 'object', required: ['done'] },
  };
  const result = await materializeNodeInputs({ directory, envelope });
  assert.match(result.prompt, /Preserve output schema\./);
  assert.match(result.prompt, /task survives/);
  assert.equal(result.prompt.includes('LONG_CONTEXT_'), false);
  assert.equal(result.prompt.includes('LONG_VERIFY_'), false);
  const byName = new Map(result.manifest.map(item => [item.name, item]));
  assert.equal(await readFile(byName.get('context').path, 'utf8'), context);
  assert.equal(await readFile(byName.get('verification').path, 'utf8'), verification);
});

test('existing absolute and workspace-relative file or directory inputs stay as prompt addresses', async t => {
  const root = await fixture(t);
  const workspace = join(root, 'workspace');
  const data = join(workspace, 'data');
  const nested = join(data, 'nested');
  await mkdir(nested, { recursive: true });
  const absoluteFile = join(data, 'source.md');
  const absoluteDirectory = nested;
  await writeFile(absoluteFile, 'source content is read on demand');
  const relativeFile = 'data/source.md';
  const relativeDirectory = 'data/nested';
  const opaqueText = 'opaque/path-id that is not present on disk';
  const envelope = {
    workspace,
    workflow_id: 'opaque-workflow',
    node_id: 'opaque-node',
    prompt_template: 'Task={{task}}\nContext={{context}}\nVerification={{verification}}',
    inputs: {
      task: 'inspect only referenced paths',
      context: absoluteFile,
      verification: relativeDirectory,
      absolute_directory: absoluteDirectory,
      relative_file: relativeFile,
      relative_directory: relativeDirectory,
      unknown_text: opaqueText,
    },
    context_projection: { mode: 'declared_bindings', bindings: [], references: [] },
  };
  const result = await materializeNodeInputs({ directory: join(root, 'attempt'), envelope });

  assert.match(result.prompt, new RegExp(`Context=${absoluteFile.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`));
  assert.match(result.prompt, new RegExp(`Verification=${absoluteDirectory.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`));
  assert.ok(result.prompt.includes(JSON.stringify(absoluteDirectory)));
  assert.ok(result.prompt.includes(JSON.stringify(absoluteFile)));
  assert.equal(result.manifest.length, 1);
  assert.equal(result.manifest[0].name, 'unknown_text');
  assert.equal(await readFile(result.manifest[0].path, 'utf8'), opaqueText);
});

test('requires an absolute Host-selected material directory', async () => {
  await assert.rejects(materializeNodeInputs({ directory: 'relative/attempt', envelope: { inputs: {} } }), { code: 'NODE_INPUT_MATERIALS_PATH' });
});

test('one native task index points at pinned resources and verified absolute and relative input files',async t=>{
  const root=await fixture(t),workspace=join(root,'workspace'),packets=join(workspace,'packets');
  await mkdir(packets,{recursive:true});
  const absolutePath=join(packets,'absolute.json'),relativePath='packets/relative.json';
  const absoluteBytes=Buffer.from('{"card":"absolute","id":"A-001"}','utf8');
  const relativeBytes=Buffer.from('{"card":"relative","id":"R-002"}','utf8');
  await writeFile(absolutePath,absoluteBytes);await writeFile(join(workspace,relativePath),relativeBytes);
  const resourceBytes=Buffer.from('Pinned authoring contract.','utf8');
  const envelope={workspace,workflow_id:'bundle',node_id:'writer',access:'bounded_write',
    prompt_template:'{{task}} Use only the assigned packets.',inputs:{task:'Implement assigned cards',jobs:[
      {packet_path:absolutePath,packet_sha256:sha256(absoluteBytes)},
      {packet_path:relativePath,packet_sha256:sha256(relativeBytes)},
    ]},context_projection:{mode:'declared_bindings',bindings:[],references:[{path:'contract.md',sha256:sha256(resourceBytes),bytes:resourceBytes.length}]}};
  const resultSchema={type:'object',required:['done'],properties:{done:{type:'boolean'}}};
  const result=await materializeNativeTaskBundle({directory:join(workspace,'work','partition-0'),envelope,
    resources:[{path:'contract.md',sha256:sha256(resourceBytes),size:resourceBytes.length,bytes:resourceBytes}],
    resultSchema,allowedPaths:['zz'],itemPositions:[3,4]});
  const bundle=JSON.parse(await readFile(result.task_bundle_path,'utf8'));
  assert.equal(bundle.schema_version,1);
  assert.match(bundle.task,/Implement assigned cards/);
  assert.deepEqual(bundle.writable_paths,['zz']);
  assert.deepEqual(result.item_positions,[3,4]);
  assert.equal(Object.hasOwn(bundle,'item_positions'),false);
  assert.deepEqual(bundle.result_schema,resultSchema);
  assert.equal(bundle.resources.length,1);
  assert.deepEqual({...bundle.resources[0],local_path:undefined},{path:'contract.md',sha256:sha256(resourceBytes),bytes:resourceBytes.length,local_path:undefined});
  assert.equal(await readFile(bundle.resources[0].local_path,'utf8'),resourceBytes.toString('utf8'));
  assert.deepEqual(bundle.verified_files.map(item=>item.path),[absolutePath,relativePath]);
  assert.deepEqual(await Promise.all(bundle.verified_files.map(item=>readFile(item.local_path,'utf8'))),
    [absoluteBytes.toString('utf8'),relativeBytes.toString('utf8')]);
  assert.deepEqual(bundle.verified_files.map(item=>item.references),[['/jobs/0/packet_path'],['/jobs/1/packet_path']]);
  const boundFiles=await readdir(join(workspace,'work','partition-0','inputs'));
  assert.equal(boundFiles.length,1);
  const boundJobs=JSON.parse(await readFile(join(workspace,'work','partition-0','inputs',boundFiles[0]),'utf8'));
  assert.deepEqual(boundJobs.map(item=>item.packet_path),bundle.verified_files.map(item=>item.local_path));
  assert.ok((await stat(result.task_bundle_path)).size<16*1024);
  assert.doesNotMatch(await readFile(result.task_bundle_path,'utf8'),/A-001|R-002/);
  await writeFile(join(workspace,relativePath),'changed');
  await assert.rejects(materializeNativeTaskBundle({directory:join(workspace,'work','partition-1'),envelope}),
    {code:'NATIVE_TASK_FILE_CHANGED'});
});

test('ten-card native assignment keeps large packets out of the single-read task index',async t=>{
  const root=await fixture(t),workspace=join(root,'workspace'),packets=join(workspace,'packets');
  await mkdir(packets,{recursive:true});
  const jobs=[];
  for(let index=0;index<10;index++){
    const path=join(packets,`card-${index}.json`),bytes=Buffer.from(JSON.stringify({card_id:`card-${index}`,body:'x'.repeat(6000)}));
    await writeFile(path,bytes);jobs.push({packet_path:path,packet_sha256:sha256(bytes)});
  }
  const envelope={workspace,workflow_id:'ten-card',node_id:'writer',access:'bounded_write',
    prompt_template:'Implement the assigned cards.',inputs:{jobs},context_projection:{mode:'declared_bindings',bindings:[],references:[]}};
  const result=await materializeNativeTaskBundle({directory:join(workspace,'work','partition-0'),envelope,
    resultSchema:{type:'object'},allowedPaths:['zz'],itemPositions:Array.from({length:10},(_,index)=>index)});
  const bundleText=await readFile(result.task_bundle_path,'utf8'),bundle=JSON.parse(bundleText);
  assert.equal(bundle.verified_files.length,10);
  assert.ok(Buffer.byteLength(bundleText)<16*1024);
  assert.equal(bundleText.includes('x'.repeat(100)),false);
  assert.deepEqual(await Promise.all(bundle.verified_files.map(async item=>(await stat(item.local_path)).size)),
    jobs.map(()=>JSON.stringify({card_id:'card-0',body:'x'.repeat(6000)}).length));
});
