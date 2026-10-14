import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, readdir, rm, stat, writeFile, rename, symlink } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import filesystem from 'node:fs/promises';
import { syncBuiltinESMExports } from 'node:module';
import { tmpdir } from './physical-tempdir.mjs';
import { dirname, join } from 'node:path';
import { createHash } from 'node:crypto';
import { canonicalJSON } from '../lib/workflow-revisions.mjs';
import {compilePrompt} from '../lib/workflow-executor.mjs';
import { HOST_MAIN_INLINE_BUDGETS, NATIVE_TASK_INLINE_LIMIT, materializeMainTaskBundle, materializeNativeTaskBundle, materializeNodeInputs, prepareHostMainContext, readMainTaskProjection, readNativeTaskProjection,readTerminalMainInputs,TERMINAL_MAIN_INPUT_BUDGET } from '../lib/execution/node-input-materials.mjs';

test('terminal semantic input carrier preserves UTF8 physical bytes and exact canonical reference on item/total limits',async t=>{
  const root=await fixture(t);
  const inputs={a:'🌱\r\n中\rLF\n'.repeat(1300)+'no-final-newline',b:'b'.repeat(33000),c:'c'.repeat(30000),d:'d'.repeat(30000)};
  const receipt=await materializeMainTaskBundle({directory:join(root,'terminal'),envelope:{workspace:root,access:'read_only',inputs,resources:[],prompt_template:'Neutral final acceptance'}});
  const result=await readTerminalMainInputs(receipt);
  assert.equal(result.semantic_inputs.a.content,inputs.a);assert.equal(result.semantic_inputs.a.format,'text');
  assert(result.semantic_input_files.b.path.endsWith('.txt'));assert.equal(await readFile(result.semantic_input_files.b.path,'utf8'),inputs.b);
  assert(result.semantic_input_files.d,'The aggregate budget must keep a complete file reference');
  assert(Object.values(result.semantic_inputs).reduce((bytes,item)=>bytes+Buffer.byteLength(item.content),0)<=TERMINAL_MAIN_INPUT_BUDGET.total_bytes);
  assert.doesNotMatch(JSON.stringify(result),/context_preparation|sha256|lease|receipt|controller/);
  const metadata=JSON.parse(await readFile(join(root,'terminal','context-preparation.json'),'utf8'));
  await writeFile(metadata.inputs.find(item=>item.name==='a').path,'changed');
  await assert.rejects(readTerminalMainInputs(receipt),{code:'MAIN_ORCHESTRATION_BUNDLE'});
});

test('terminal semantic input carrier excludes resources and verified binary files',async t=>{
  const root=await fixture(t),binary=join(root,'neutral.bin');await writeFile(binary,Buffer.from([0,255,128]));
  const bytes=Buffer.from('export default "private executable bytes";');
  const receipt=await materializeMainTaskBundle({directory:join(root,'terminal'),envelope:{workspace:root,access:'read_only',inputs:{source:binary},
    resources:['neutral.mjs'],prompt_template:'Neutral task'},resources:[{path:'neutral.mjs',bytes,size:bytes.length,sha256:sha256(bytes)}]});
  assert.deepEqual(await readTerminalMainInputs(receipt),{});
});

test('terminal JSON carrier supplies its complete native value without a second JSON string encoding',async t=>{
  const root=await fixture(t);
  const value={pages:[{source:'Quote "hello", path \\neutral and line\r\n🌱'.repeat(260)}],settings:{enabled:true,count:3}};
  const receipt=await materializeMainTaskBundle({directory:join(root,'terminal-native-json'),
    envelope:{workspace:root,access:'read_only',inputs:{manuscripts:value},resources:[],prompt_template:'Read the complete manuscript'}});
  const carrier=await readTerminalMainInputs(receipt);
  assert.equal(carrier.semantic_inputs.manuscripts.format,'json');
  assert.equal(typeof carrier.semantic_inputs.manuscripts.content,'object','Host must supply a native JSON value');
  assert.deepEqual(carrier.semantic_inputs.manuscripts.content,value);
  assert(JSON.stringify(carrier).length<JSON.stringify({semantic_inputs:{manuscripts:{format:'json',content:canonicalJSON(value)}}}).length);
  const metadata=JSON.parse(await readFile(join(root,'terminal-native-json','context-preparation.json'),'utf8'));
  const input=metadata.inputs.find(item=>item.name==='manuscripts');
  assert.equal(await readFile(input.path,'utf8'),canonicalJSON(value),'Canonical bound bytes remain unchanged');
  await writeFile(input.path,canonicalJSON({pages:[]}));
  await assert.rejects(readTerminalMainInputs(receipt),{code:'MAIN_ORCHESTRATION_BUNDLE'});
});

test('native public carrier uses an exact 1024 UTF8 byte boundary for legacy semantic projections',async t=>{
  const root=await fixture(t);
  for(const [size,prefix]of [[1024,''],[1025,''],[1025,'雪'.repeat(200)]]){
    await t.test(`${size} bytes with ${prefix.length} multibyte characters`,async()=>{
    const directory=join(root,'native-boundary-'+size+'-'+prefix.length);await mkdir(directory);
    const bundle={schema_version:1,task:'',workspace:root,access:'read_only',writable_paths:[],resources:[],verified_files:[],result_schema:{type:'string'}};
    bundle.task=prefix+'x'.repeat(size-Buffer.byteLength(canonicalJSON(bundle))-Buffer.byteLength(prefix));
    const bytes=Buffer.from(canonicalJSON(bundle));assert.equal(bytes.length,size);
    const path=join(directory,'task.json');await writeFile(path,bytes);
    const receipt={task_bundle_path:path,task_bundle_sha256:sha256(bytes),task_sha256:sha256(bundle.task),resource_count:0,verified_file_count:0,allowed_paths:[]};
    const carrier=await readNativeTaskProjection(receipt,{materialize:true});
    assert.equal(carrier.inline,size<=1024,'Carrier selection must count UTF8 bytes, independently of Main 12000');
    if(prefix)assert(canonicalJSON(bundle).length<1024,'The multi-byte case must fit the old character count');
    if(carrier.inline)assert.deepEqual(carrier.task_bundle,bundle);
    else{
      assert.equal(carrier.task_bundle_path,join(directory,'semantic-task.json'));
      assert.deepEqual(JSON.parse(await readFile(carrier.task_bundle_path,'utf8')),bundle);
      assert.deepEqual(await readNativeTaskProjection(receipt),carrier);
      await writeFile(carrier.task_bundle_path,'changed');
      await assert.rejects(readNativeTaskProjection(receipt),{code:'NATIVE_TASK_BUNDLE'});
    }
    assert((await readFile(path)).equals(bytes),'Historical canonical bytes must remain exact');
    });
  }
});

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'node-input-materials-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  return root;
}

function sha256(value) { return createHash('sha256').update(value).digest('hex'); }

for (const kind of ['native','main']) test(`Host budgets the entire ${kind} UTF8 JSON index before committing inline content`,async t=>{
  const root=await fixture(t), directory=join(root,kind+'-whole-budget');
  const source='\\"雪'.repeat(900);
  const resource=Buffer.from('Check the actual document.\n'.repeat(85));
  const envelope={workspace:root,access:'bounded_write',inputs:{findings:source,decision:'Keep the evidence complete.'},
    resources:['checklist.md'],prompt_template:'Apply the complete original scope and evidence. '.repeat(110)};
  const options={directory,envelope,resources:[{path:'checklist.md',bytes:resource,size:resource.length,sha256:sha256(resource)}]};
  const resultSchema={type:'object',properties:{handover:{type:'string',description:'Preserve all requested facts. '.repeat(55)}}};
  const receipt=kind==='native'?await materializeNativeTaskBundle({...options,resultSchema,allowedPaths:['docs']}):await materializeMainTaskBundle(options);
  assert(receipt.task_bundle_bytes<=16*1024);
  const bundle=JSON.parse(await readFile(receipt.task_bundle_path,'utf8'));
  const metadata=JSON.parse(await readFile(receipt.context_preparation?.path??join(directory,'context-preparation.json'),'utf8'));
  assert(metadata.audit.index_spill_count>0,'A serialized overflow must change delivery, not merely raise its limit');
  const finding=metadata.inputs.find(item=>item.name==='findings');
  assert.equal(finding.delivery,'file');
  assert.equal(await readFile(finding.path,'utf8'),source,'File delivery retains every original byte');
  const displayed=JSON.parse(bundle.task.split('\nInputs:\n')[1].split('\nResources:\n')[0]);
  assert(displayed.findings.includes(canonicalJSON(finding.path)));
  if(kind==='native'){
    const projection=await readNativeTaskProjection(receipt,{materialize:true});
    assert.equal(projection.inline,false);assert.deepEqual(JSON.parse(await readFile(projection.task_bundle_path,'utf8')).result_schema,resultSchema);
  }
  const replay=kind==='native'?await materializeNativeTaskBundle({...options,resultSchema,allowedPaths:['docs']}):await materializeMainTaskBundle(options);
  assert.equal(replay.task_bundle_sha256,receipt.task_bundle_sha256);
});

function projectionStorage(root) {
  return { artifactStore: { directory: () => root, saveArtifact: async (_id, label, bytes) => {
    const hash = sha256(bytes), artifact = `artifact-${label}-${hash}.bin`;
    await writeFile(join(root, artifact), bytes, { flag: 'wx' });
    return { artifact, sha256: hash, bytes: bytes.length };
  } }, runId: 'fixture-run', attemptId: 'fixture-attempt' };
}

for (const target of ['canonical', 'preparation', 'public']) test(`Main projection descriptor rejects identical-byte ${target} link replacement after the initial path check`, async t => {
  const root = await fixture(t), directory = join(root, 'main'), storage = projectionStorage(root);
  const receipt = await materializeMainTaskBundle({ directory, envelope: { workspace: root, access: 'read_only', inputs: {}, resources: [],
    prompt_template: 'instruction '.repeat(1000) } });
  const publicTask = await readMainTaskProjection(receipt, { ...storage, materialize: true });
  const path = target === 'canonical' ? receipt.task_bundle_path : target === 'preparation' ? join(directory, 'context-preparation.json') : publicTask.task_bundle_path;
  const originalRead = filesystem.readFile, originalOpen = filesystem.open, originalStat = filesystem.lstat;
  let swapped = false;
  const swap = value => { if (String(value) === path) swapped = true; };
  filesystem.readFile = (...args) => { swap(args[0]); return originalRead(...args); };
  filesystem.open = (...args) => { swap(args[0]); return originalOpen(...args); };
  filesystem.lstat = async (...args) => String(args[0]) === path && swapped
    ? { isSymbolicLink: () => true, isFile: () => false, isDirectory: () => false } : originalStat(...args);
  syncBuiltinESMExports();
  try {
    await assert.rejects(readMainTaskProjection(receipt, storage), /symbolic|symlink|link|changed/i);
    assert.equal(swapped, true);
  } finally {
    filesystem.readFile = originalRead; filesystem.open = originalOpen; filesystem.lstat = originalStat; syncBuiltinESMExports();
  }
});

for (const target of ['canonical', 'preparation', 'public']) for (const fault of [
  'nonregular', 'missing', 'oversize', 'opened_identity', 'opened_nonregular', 'post_read_swap', 'post_read_missing',
  'post_read_link', 'post_read_ancestor_link', 'growth', 'truncate', 'close', 'read_and_close',
]) test(`Main projection descriptor rejects ${target} ${fault} and closes owned handles`, async t => {
  const root = await fixture(t), directory = join(root, 'main'), storage = projectionStorage(root);
  const receipt = await materializeMainTaskBundle({ directory, envelope: { workspace: root, access: 'read_only', inputs: {}, resources: [],
    prompt_template: 'instruction '.repeat(1000) } });
  const publicTask = await readMainTaskProjection(receipt, { ...storage, materialize: true });
  const path = target === 'canonical' ? receipt.task_bundle_path : target === 'preparation' ? join(directory, 'context-preparation.json') : publicTask.task_bundle_path;
  const originalOpen = filesystem.open, originalStat = filesystem.lstat;
  let opens = 0, closes = 0, read = false, modified = false;
  if (fault === 'missing') await rm(path);
  filesystem.lstat = async (...args) => {
    if (String(args[0]) === path && fault === 'post_read_missing' && read) throw Object.assign(new Error('Removed after descriptor read'), { code: 'ENOENT' });
    const info = await originalStat(...args);
    if (read && (fault === 'post_read_link' && String(args[0]) === path || fault === 'post_read_ancestor_link' && String(args[0]) === dirname(path)))
      return Object.assign(Object.create(info), { isSymbolicLink: () => true });
    if (String(args[0]) !== path) return info;
    if (fault === 'nonregular') return Object.assign(Object.create(info), { isFile: () => false });
    if (fault === 'oversize') return Object.assign(Object.create(info), { size: args[1]?.bigint ? 64n * 1024n * 1024n + 1n : 64 * 1024 * 1024 + 1 });
    return info;
  };
  filesystem.open = async (...args) => {
    const handle = await originalOpen(...args);
    if (String(args[0]) !== path) return handle;
    opens++;
    const originalHandleStat = handle.stat.bind(handle), originalHandleRead = handle.read.bind(handle), originalClose = handle.close.bind(handle);
    handle.stat = async (...values) => {
      const info = await originalHandleStat(...values);
      if (fault === 'opened_identity') return Object.assign(Object.create(info), { ino: info.ino + 1n });
      if (fault === 'opened_nonregular') return Object.assign(Object.create(info), { isFile: () => false });
      return info;
    };
    handle.read = async (...values) => {
      if (fault === 'read_and_close') throw Object.assign(new Error('Descriptor read failed'), { code: 'FIXTURE_READ' });
      const result = await originalHandleRead(...values); read = true;
      if (!modified && fault === 'post_read_swap') {
        const bytes = await readFile(path); await rename(path, path + '.original'); await writeFile(path, bytes); modified = true;
      }
      if (!modified && fault === 'growth') { await writeFile(path, Buffer.concat([await readFile(path), Buffer.from(' ')])); modified = true; }
      if (!modified && fault === 'truncate') { await writeFile(path, ''); modified = true; }
      return result;
    };
    handle.close = async () => {
      closes++; await originalClose();
      if (['close', 'read_and_close'].includes(fault)) throw Object.assign(new Error('Descriptor close failed'), { code: 'FIXTURE_CLOSE' });
    };
    return handle;
  };
  syncBuiltinESMExports();
  try {
    const expected = fault === 'close' ? 'FIXTURE_CLOSE' : fault === 'read_and_close' ? 'FIXTURE_READ'
      : ['post_read_link', 'post_read_ancestor_link'].includes(fault) ? 'WORKFLOW_SYMLINK' : 'MAIN_ORCHESTRATION_BUNDLE';
    await assert.rejects(readMainTaskProjection(receipt, storage), error => {
      assert.equal(error.code, expected);
      if (fault === 'read_and_close') assert.deepEqual(error.errors.map(item => item.code), ['FIXTURE_READ', 'FIXTURE_CLOSE']);
      return true;
    });
    assert.equal(closes, opens);
    if (['missing', 'nonregular', 'oversize'].includes(fault)) assert.equal(opens, 0);
    else assert.equal(opens, 1);
  } finally { filesystem.open = originalOpen; filesystem.lstat = originalStat; syncBuiltinESMExports(); }
});

test('Main projection descriptor POSIX raced identical-byte symlink is rejected at open', { skip: process.platform === 'win32' ? 'Windows Node lacks POSIX no-follow open guarantee' : false }, async t => {
  const root = await fixture(t), receipt = await materializeMainTaskBundle({ directory: join(root, 'main'),
    envelope: { workspace: root, access: 'read_only', inputs: {}, resources: [] } });
  const originalOpen = filesystem.open; let raced = false;
  filesystem.open = async (...args) => {
    if (String(args[0]) === receipt.task_bundle_path) {
      const retained = receipt.task_bundle_path + '.original'; await rename(receipt.task_bundle_path, retained);
      await symlink(retained, receipt.task_bundle_path); raced = true;
    }
    return originalOpen(...args);
  };
  syncBuiltinESMExports();
  try { await assert.rejects(readMainTaskProjection(receipt), error => error.code === 'MAIN_ORCHESTRATION_BUNDLE' && error.details.read_error_code === 'ELOOP'); assert(raced); }
  finally { filesystem.open = originalOpen; syncBuiltinESMExports(); }
});

test('Main projection metadata retains a separately bounded manifest larger than the task index', async t => {
  const root = await fixture(t), receipt = await materializeMainTaskBundle({ directory: join(root, 'main'),
    envelope: { workspace: root, access: 'read_only', inputs: {}, resources: [] } });
  const bundle = JSON.parse(await readFile(receipt.task_bundle_path)), metadata = JSON.parse(await readFile(bundle.context_preparation.path));
  metadata.diagnostic_extension = 'retained Host metadata '.repeat(1200);
  const metadataBytes = Buffer.from(canonicalJSON(metadata)); assert(metadataBytes.length > 16 * 1024);
  await writeFile(bundle.context_preparation.path, metadataBytes); bundle.context_preparation.sha256 = sha256(metadataBytes);
  const canonicalBytes = Buffer.from(canonicalJSON(bundle)); await writeFile(receipt.task_bundle_path, canonicalBytes);
  receipt.task_bundle_sha256 = sha256(canonicalBytes);
  const result = await readMainTaskProjection(receipt);
  assert.deepEqual(result.task_bundle, { schema_version: 2, task: bundle.task });
  assert.equal(JSON.stringify(result).includes('retained Host metadata'), false);
});

test('Main projection descriptor POSIX raced FIFO opens without blocking and is rejected', { skip: process.platform === 'win32' ? 'Windows Node lacks POSIX nonblocking/no-follow open guarantees' : false }, async t => {
  const root = await fixture(t), receipt = await materializeMainTaskBundle({ directory: join(root, 'main'),
    envelope: { workspace: root, access: 'read_only', inputs: {}, resources: [] } });
  const originalOpen = filesystem.open; let raced = false, closed = false;
  filesystem.open = async (...args) => {
    if (String(args[0]) === receipt.task_bundle_path) {
      await rename(receipt.task_bundle_path, receipt.task_bundle_path + '.original');
      execFileSync('mkfifo', [receipt.task_bundle_path]); raced = true;
      const handle = await originalOpen(...args), close = handle.close.bind(handle);
      handle.close = async () => { closed = true; return close(); }; return handle;
    }
    return originalOpen(...args);
  };
  syncBuiltinESMExports();
  try { await assert.rejects(readMainTaskProjection(receipt), { code: 'MAIN_ORCHESTRATION_BUNDLE' }); assert(raced); assert(closed); }
  finally { filesystem.open = originalOpen; syncBuiltinESMExports(); }
});

test('Main semantic projection applies the exact UTF-8 inline boundary and retains canonical index limits', async t => {
  const root = await fixture(t), overhead = Buffer.byteLength(canonicalJSON({ schema_version: 2, task: '' }));
  for (const size of [12000, 12001, 16 * 1024 + 1]) {
    const directory = join(root, String(size)); await mkdir(directory);
    const task = '雪'.repeat(Math.floor((size - overhead) / 3)) + 'x'.repeat((size - overhead) % 3);
    const metadata = Buffer.from(canonicalJSON({ schema_version: 1, kind: 'host_main_context', prompt_sha256: sha256(task) }));
    const preparationPath = join(directory, 'context-preparation.json'); await writeFile(preparationPath, metadata);
    const bytes = Buffer.from(canonicalJSON({ schema_version: 2, task, context_preparation: { path: preparationPath, sha256: sha256(metadata) } }));
    const path = join(directory, 'task.json'); await writeFile(path, bytes);
    const receipt = { task_bundle_path: path, task_bundle_sha256: sha256(bytes) };
    if (size > 16 * 1024) {
      await assert.rejects(readMainTaskProjection(receipt, { materialize: true }), { code: 'MAIN_ORCHESTRATION_BUNDLE' });
      continue;
    }
    const storage = projectionStorage(directory);
    const result = await readMainTaskProjection(receipt, { ...storage, materialize: true });
    assert.equal(result.inline, size === 12000);
    assert.deepEqual(await readFile(path), bytes);
    if (!result.inline) {
      assert.equal((await readFile(result.task_bundle_path)).length, size);
      assert.equal(sha256(await readFile(result.task_bundle_path)), result.task_bundle_sha256);
      assert.deepEqual(await readMainTaskProjection(receipt, storage), result);
    }
  }
});

test('Main semantic projection rejects linked canonical, preparation and public indices', async t => {
  const root = await fixture(t), directory = join(root, 'main');
  const receipt = await materializeMainTaskBundle({ directory, envelope: { workspace: root, access: 'read_only', inputs: {}, resources: [],
    prompt_template: 'instruction '.repeat(1000) } });
  const storage = projectionStorage(root);
  const publicTask = await readMainTaskProjection(receipt, { ...storage, materialize: true }); assert.equal(publicTask.inline, false);
  const original = filesystem.lstat;
  for (const path of [receipt.task_bundle_path, join(directory, 'context-preparation.json'), publicTask.task_bundle_path]) {
    filesystem.lstat = async (...args) => String(args[0]) === path
      ? { isSymbolicLink: () => true, isFile: () => false, isDirectory: () => false } : original(...args);
    syncBuiltinESMExports();
    try { await assert.rejects(readMainTaskProjection(receipt, { ...storage, materialize: true }), /symbolic|symlink|link/i); }
    finally { filesystem.lstat = original; syncBuiltinESMExports(); }
  }
});

test('Main bundle refuses preparation metadata replaced between commit and consumption',async t=>{
  const root=await fixture(t),directory=join(root,'main'),path=join(directory,'context-preparation.json');
  const original=filesystem.readFile;let replaced=false;
  filesystem.readFile=async (...args)=>{
    if(String(args[0])===path&&!replaced){
      const body=JSON.parse(await original(...args));body.resources.push({path:'undeclared.mjs',sha256:'a'.repeat(64),bytes:1});
      await writeFile(path,canonicalJSON(body));replaced=true;
    }
    return original(...args);
  };
  syncBuiltinESMExports();
  try{
    await assert.rejects(materializeMainTaskBundle({directory,envelope:{workspace:root,access:'read_only',inputs:{task:'A declared question'},resources:[]}}),{code:'NODE_INPUT_MATERIALS_CONFLICT'});
    assert.equal(replaced,true);
    await assert.rejects(stat(join(directory,'task.json')),{code:'ENOENT'});
  }finally{filesystem.readFile=original;syncBuiltinESMExports();}
});

test('Main bundle checks the preparation path for a link before consuming metadata',async t=>{
  const root=await fixture(t),directory=join(root,'main'),path=join(directory,'context-preparation.json');
  const original=filesystem.lstat;let detected=false;
  filesystem.lstat=async (...args)=>{
    const info=await original(...args);
    if(String(args[0])===path&&info.isFile()){
      detected=true;return {isSymbolicLink:()=>true,isFile:()=>false,isDirectory:()=>false};
    }
    return info;
  };
  syncBuiltinESMExports();
  try{
    await assert.rejects(materializeMainTaskBundle({directory,envelope:{workspace:root,access:'read_only',inputs:{task:'A declared question'},resources:[]}}),/symbolic|symlink|link/i);
    assert.equal(detected,true);
    await assert.rejects(stat(join(directory,'task.json')),{code:'ENOENT'});
  }finally{filesystem.lstat=original;syncBuiltinESMExports();}
});

test('Main context budgets count UTF-8 bytes and apply deterministic aggregate admission', async t => {
  const root = await fixture(t), directory = join(root, 'main');
  const resources = ['z.md', 'a.md', 'm.md'].map(path => {
    const bytes = Buffer.from(path + '雪'.repeat(1100));
    return { path, bytes, size: bytes.length, sha256: sha256(bytes) };
  });
  const inputs = { z: '雪'.repeat(1000), a: '雪'.repeat(1000), m: '雪'.repeat(1000), oversized: '雪'.repeat(1500) };
  const envelope = { workspace: root, node_id: 'main', inputs, resources: resources.map(item => item.path),
    context_projection: { references: resources.map(item => item.path) }, prompt_template: 'Use the declared context.' };
  const result = await prepareHostMainContext({ directory, envelope, resources });
  const manifestBytes = await readFile(result.preparation_path), manifest = JSON.parse(manifestBytes);
  assert.equal(sha256(manifestBytes), result.preparation_sha256);
  assert.deepEqual(manifest.resources.map(item => [item.path, item.delivery]), [['a.md', 'inline'], ['m.md', 'inline'], ['z.md', 'file']]);
  assert.deepEqual(manifest.inputs.map(item => [item.name, item.delivery]), [['a', 'inline'], ['m', 'file'], ['oversized', 'file'], ['z', 'file']]);
  assert.equal(result.audit.inline_resource_bytes, 6608); assert.equal(result.audit.inline_input_bytes, 3000);
  assert.equal(result.audit.inline_total_bytes, 9608); assert.deepEqual(result.audit.budgets, HOST_MAIN_INLINE_BUDGETS);
  assert.equal(result.audit.prompt_bytes, Buffer.byteLength(result.prompt));
  for (const item of manifest.resources) assert.equal(sha256(await readFile(item.local_path)), item.sha256);
  for (const item of manifest.inputs) if (item.delivery === 'file') assert.equal(sha256(await readFile(item.path)), item.sha256);
  else assert.equal(Object.hasOwn(item, 'path'), false, 'inline-only values must not advertise nonexistent files');
  const repeated = await prepareHostMainContext({ directory, envelope: { ...envelope, resources: [...envelope.resources].reverse() }, resources: [...resources].reverse() });
  assert.deepEqual(repeated, result);
  await assert.rejects(prepareHostMainContext({ directory, envelope: { ...envelope, inputs: { ...inputs, a: 'changed' } }, resources }), { code: 'NODE_INPUT_MATERIALS_CONFLICT' });
});

test('Main preparation rejects undeclared, missing, duplicated and changed pinned resources', async t => {
  const root = await fixture(t), bytes = Buffer.from('behavior'), resource = { path: 'behavior.md', bytes, size: bytes.length, sha256: sha256(bytes) };
  const envelope = { inputs: {}, resources: [resource.path], context_projection: { references: [resource.path] } };
  const prepare = (resources, projected = envelope) => prepareHostMainContext({ directory: join(root, 'main'), envelope: projected, resources });
  await assert.rejects(prepare([]), { code: 'NODE_RESOURCE_DECLARATION' });
  await assert.rejects(prepare([resource, { ...resource, path: 'ambient.md' }]), { code: 'NODE_RESOURCE_DECLARATION' });
  await assert.rejects(prepare([resource], { ...envelope, context_projection: { references: ['ambient.md'] } }), { code: 'NODE_RESOURCE_DECLARATION' });
  await assert.rejects(prepare([resource, resource]), { code: 'NODE_RESOURCE_DECLARATION' });
  await assert.rejects(prepare([{ ...resource, bytes: Buffer.from('changed!') }]), { code: 'NATIVE_TASK_RESOURCE' });
  await assert.rejects(prepare([{ ...resource, size: bytes.length + 1 }]), { code: 'NATIVE_TASK_RESOURCE' });
});

test('Main projects usable resource addresses once and keeps complete integrity metadata in its committed manifest', async t => {
  const root = await fixture(t), directory = join(root, 'main');
  const resources = ['instructions.md', 'render.mjs'].map(path => {
    const bytes = Buffer.from(path === 'instructions.md' ? 'Neutral declared behavior.' : 'EXECUTABLE_BODY_STAYS_LOCAL');
    return { path, bytes, size: bytes.length, sha256: sha256(bytes) };
  });
  const envelope = { workspace: root, inputs: { task: 'Apply declared behavior.' },
    resources: resources.map(item => item.path), context_projection: { references: resources.map(item => item.path) } };
  const prepared = await prepareHostMainContext({ directory, envelope, resources });
  const manifestBytes = await readFile(prepared.preparation_path), manifest = JSON.parse(manifestBytes);
  assert.equal(sha256(manifestBytes), prepared.preparation_sha256);
  const projected = JSON.parse(prepared.prompt.split('Resources:\n')[1].split('\n')[0]);
  for (const item of manifest.resources) {
    const source = resources.find(resource => resource.path === item.path);
    assert.equal(item.sha256, source.sha256);
    assert.equal(item.bytes, source.size);
    assert.equal(sha256(await readFile(item.local_path)), item.sha256);
    const reference = projected.find(reference => reference.path === item.path);
    assert.deepEqual(reference, { path: item.path,
      ...(item.delivery === 'inline' ? { content: source.bytes.toString('utf8') } : {local_path:item.local_path}) });
    if(item.delivery==='inline')assert.equal(prepared.prompt.includes(item.local_path),false,'Complete inline text must not also advertise a reread address');
  }
  assert.equal(projected.length, resources.length);
  assert.equal(prepared.prompt.includes('EXECUTABLE_BODY_STAYS_LOCAL'), false);
  assert.equal(prepared.prompt.split('Neutral declared behavior.').length - 1, 1);
  assert.deepEqual(prepared.audit.budgets, HOST_MAIN_INLINE_BUDGETS);
  await writeFile(manifest.resources[0].local_path, 'changed');
  await assert.rejects(prepareHostMainContext({ directory, envelope, resources }), { code: 'NODE_INPUT_MATERIALS_CONFLICT' });
});

test('Main includes a medium semantic acceptance packet once within unchanged aggregate budgets', async t => {
  const root=await fixture(t),value='SEMANTIC_ACCEPTANCE_'+ '雪'.repeat(1840);
  assert(Buffer.byteLength(value)>4096&&Buffer.byteLength(value)<8192);
  const envelope={workspace:root,node_id:'main',inputs:{result:value},resources:[],prompt_template:'Review the supplied result.'};
  const result=await prepareHostMainContext({directory:join(root,'main'),envelope});
  const manifest=JSON.parse(await readFile(result.preparation_path));
  assert.equal(manifest.inputs[0].delivery,'inline');
  assert.equal(result.prompt.split(value).length-1,1);
  assert.equal(result.audit.inline_input_bytes,Buffer.byteLength(value));
  assert.equal(HOST_MAIN_INLINE_BUDGETS.resource_bytes,8192);
  assert.equal(HOST_MAIN_INLINE_BUDGETS.input_bytes,8192);
  assert.equal(HOST_MAIN_INLINE_BUDGETS.total_bytes,12000);
  const large=await prepareHostMainContext({directory:join(root,'large'),envelope:{...envelope,inputs:{result:'雪'.repeat(2800)}}});
  assert.equal(JSON.parse(await readFile(large.preparation_path)).inputs[0].delivery,'file');
  await assert.rejects(prepareHostMainContext({directory:join(root,'main'),envelope:{...envelope,inputs:{result:value+'changed'}}}),{code:'NODE_INPUT_MATERIALS_CONFLICT'});
});

test('Main copies exact verified bound files and fails on changed sources and local copies', async t => {
  const root = await fixture(t), source = join(root, 'source.json'), bytes = Buffer.from('{"body":"declared"}');
  await writeFile(source, bytes);
  const envelope = { workspace: root, access: 'read_only', node_id: 'main', inputs: { source_path: source, source_sha256: sha256(bytes),
    packet: { source_path: source, source_sha256: sha256(bytes) } }, resources: [] };
  const result = await prepareHostMainContext({ directory: join(root, 'main'), envelope });
  const manifest = JSON.parse(await readFile(result.preparation_path));
  assert.equal(manifest.verified_files.length, 1);
  assert.equal(await readFile(manifest.verified_files[0].local_path, 'utf8'), bytes.toString());
  assert.ok(result.prompt.includes(canonicalJSON(manifest.verified_files[0].local_path)));
  assert.deepEqual(await prepareHostMainContext({ directory: join(root, 'main'), envelope }), result);
  const native = await materializeNativeTaskBundle({ directory: join(root, 'native'), envelope });
  assert.deepEqual(await materializeNativeTaskBundle({ directory: join(root, 'native'), envelope }), native);
  await writeFile(manifest.verified_files[0].local_path, 'conflict');
  await assert.rejects(prepareHostMainContext({ directory: join(root, 'main'), envelope }), { code: 'NODE_INPUT_MATERIALS_CONFLICT' });
  await writeFile(source, 'changed');
  await assert.rejects(prepareHostMainContext({ directory: join(root, 'fresh'), envelope }), { code: 'NATIVE_TASK_FILE_CHANGED' });
});

test('Main delivers a small hash-bound text file once in prepared context and retains its verified copy',async t=>{
  const root=await fixture(t),source=join(root,'draft.md'),text='# Neutral explanation\n\nExact declared text.\n';
  await writeFile(source,text);
  const ref={source_path:source,source_sha256:sha256(text)};
  const envelope={workspace:root,access:'read_only',node_id:'writer',inputs:{source:ref,repeated:ref},resources:[],prompt_template:'Revise the declared draft.'};
  const prepared=await prepareHostMainContext({directory:join(root,'main'),envelope});
  const manifest=JSON.parse(await readFile(prepared.preparation_path));
  assert.equal(manifest.verified_files.length,1);assert.equal(manifest.verified_files[0].delivery,'inline');
  assert.equal(prepared.prompt.split(JSON.stringify(text)).length-1,1);
  assert.equal(prepared.audit.inline_verified_file_count,1);assert.equal(prepared.audit.inline_verified_file_bytes,Buffer.byteLength(text));
  assert.equal(prepared.audit.inline_total_bytes,prepared.audit.inline_resource_bytes+prepared.audit.inline_input_bytes);
  assert.equal(sha256(await readFile(manifest.verified_files[0].local_path)),ref.source_sha256);
  const native=await materializeNativeTaskBundle({directory:join(root,'native'),envelope});
  const nativeBundle=JSON.parse(await readFile(native.task_bundle_path));
  assert(nativeBundle.task.includes(JSON.stringify(text)));
  const nativeProjection=await readNativeTaskProjection(native,{materialize:true});
  const delivered=nativeProjection.inline?nativeProjection.task_bundle:JSON.parse(await readFile(nativeProjection.task_bundle_path));
  assert.equal(delivered.task,nativeBundle.task);assert(!nativeBundle.task.includes('"sha256"'));assert(!nativeBundle.task.includes('"bytes"'));
  assert.deepEqual(await prepareHostMainContext({directory:join(root,'main'),envelope}),prepared);
  await writeFile(source,'changed');
  await assert.rejects(prepareHostMainContext({directory:join(root,'changed'),envelope}),{code:'NATIVE_TASK_FILE_CHANGED'});
});

test('Main file delivery preserves executable, oversized, unverified and over-budget inputs',async t=>{
  const root=await fixture(t),inputs={};
  for(const [name,text] of [['program.mjs','NEUTRAL_EXECUTABLE_BODY'],['large.md','NEUTRAL_LARGE_BODY'.repeat(700)],['unicode.md','雪'.repeat(2700)]]){
    const path=join(root,name);await writeFile(path,text);inputs[name]={source_path:path,source_sha256:sha256(text)};
  }
  const unverified=join(root,'unverified.md');await writeFile(unverified,'UNVERIFIED_TEXT_BODY');inputs.unverified=unverified;
  const result=await prepareHostMainContext({directory:join(root,'main'),envelope:{workspace:root,inputs,resources:[]}});
  const manifest=JSON.parse(await readFile(result.preparation_path));
  assert(manifest.verified_files.every(item=>item.delivery==='file'));
  assert.equal(result.audit.inline_verified_file_count,0);
  for(const marker of ['NEUTRAL_EXECUTABLE_BODY','NEUTRAL_LARGE_BODY','UNVERIFIED_TEXT_BODY','雪'])assert(!result.prompt.includes(marker));
  assert.deepEqual(result.audit.budgets,HOST_MAIN_INLINE_BUDGETS);
});

test('Main rejects invalid UTF-8 in a declared small text document before committing context',async t=>{
  const root=await fixture(t),source=join(root,'draft.md'),bytes=Buffer.from([0xc3,0x28]);await writeFile(source,bytes);
  await assert.rejects(prepareHostMainContext({directory:join(root,'main'),envelope:{workspace:root,resources:[],
    inputs:{source_path:source,source_sha256:sha256(bytes)}}}),/encoding|encoded|UTF/i);
  await assert.rejects(stat(join(root,'main','context-preparation.json')),{code:'ENOENT'});
});

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
  assert.equal(bundle.schema_version,2);
  const metadata=JSON.parse(await readFile(bundle.context_preparation.path,'utf8'));
  assert.match(bundle.task,/Implement assigned cards/);
  assert.deepEqual(bundle.writable_paths,['zz']);
  assert.deepEqual(result.item_positions,[3,4]);
  assert.equal(Object.hasOwn(bundle,'item_positions'),false);
  assert.deepEqual(bundle.result_schema,resultSchema);
  assert.equal(metadata.resources.length,1);
  assert.equal(await readFile(metadata.resources[0].local_path,'utf8'),resourceBytes.toString('utf8'));
  assert.deepEqual(metadata.verified_files.map(item=>item.path),[absolutePath,relativePath]);
  assert.deepEqual(await Promise.all(metadata.verified_files.map(item=>readFile(item.local_path,'utf8'))),
    [absoluteBytes.toString('utf8'),relativeBytes.toString('utf8')]);
  assert.deepEqual(metadata.verified_files.map(item=>item.references),[['/jobs/0/packet_path'],['/jobs/1/packet_path']]);
  const boundInputs=JSON.parse(bundle.task.match(/\nInputs:\n([^\n]+)/)[1]);
  assert.deepEqual(boundInputs.jobs.map(item=>item.packet_path),metadata.verified_files.map(item=>item.local_path));
  const carrier=await readNativeTaskProjection(result,{materialize:true});
  assert.equal(carrier.inline,false);assert.equal(JSON.parse(await readFile(carrier.task_bundle_path)).task,bundle.task);
  assert.ok((await stat(result.task_bundle_path)).size<16*1024);
  assert.doesNotMatch(await readFile(result.task_bundle_path,'utf8'),/A-001|R-002/);
  await writeFile(join(workspace,relativePath),'changed');
  await assert.rejects(materializeNativeTaskBundle({directory:join(workspace,'work','partition-1'),envelope,
    resources:[{path:'contract.md',sha256:sha256(resourceBytes),size:resourceBytes.length,bytes:resourceBytes}]}),
    {code:'NATIVE_TASK_FILE_CHANGED'});
});

test('native semantic delivery shares exact Main inline input and resource budgets',async t=>{
  const root=await fixture(t),directory=join(root,'native');
  const body=Buffer.from('R'.repeat(4000)),inputs={a:'A'.repeat(7000),b:'B'.repeat(1300),c:'C'.repeat(8193)};
  const receipt=await materializeNativeTaskBundle({directory,envelope:{workspace:root,access:'read_only',resources:['one.md'],inputs},
    resources:[{path:'one.md',sha256:sha256(body),size:body.length,bytes:body}]});
  const bundle=JSON.parse(await readFile(receipt.task_bundle_path)),metadata=JSON.parse(await readFile(bundle.context_preparation.path));
  assert.deepEqual(metadata.audit.budgets,HOST_MAIN_INLINE_BUDGETS);
  assert.deepEqual(metadata.inputs.map(item=>[item.name,item.delivery]),[['a','inline'],['b','file'],['c','file']]);
  assert.equal(metadata.audit.inline_total_bytes,11000);
  const delivered=await readNativeTaskProjection(receipt,{materialize:true});
  const semantic=delivered.inline?delivered.task_bundle:JSON.parse(await readFile(delivered.task_bundle_path));
  assert(semantic.task.includes(inputs.a));assert(!semantic.task.includes(inputs.b));assert(!semantic.task.includes(inputs.c));
  assert(!JSON.stringify(semantic).includes('context_preparation'));
});

test('historical native schema1 receipt retains semantic material addresses without rewriting canonical bytes',async t=>{
  const root=await fixture(t),path=join(root,'task.json'),resource=join(root,'reference.md'),verified=join(root,'source.json');
  await writeFile(resource,'declared reference');await writeFile(verified,'{"id":"one"}');
  const material=async(path,name)=>({path:name,local_path:path,sha256:sha256(await readFile(path)),bytes:(await stat(path)).size});
  const bundle={schema_version:1,task:'Historical task',workspace:root,access:'bounded_write',writable_paths:['page'],result_schema:{type:'object'},
    resources:[await material(resource,'reference.md')],verified_files:[await material(verified,'source.json')]};
  const bytes=Buffer.from(canonicalJSON(bundle));await writeFile(path,bytes);
  const projected=await readNativeTaskProjection({task_bundle_path:path,task_bundle_sha256:sha256(bytes)});
  assert.deepEqual(projected.task_bundle.resources,[{path:'reference.md',local_path:resource}]);
  assert.deepEqual(projected.task_bundle.verified_files,[{path:'source.json',local_path:verified}]);
  assert.deepEqual(await readFile(path),bytes);assert.equal((await readdir(root)).length,3);
  await writeFile(verified,'changed');
  await assert.rejects(readNativeTaskProjection({task_bundle_path:path,task_bundle_sha256:sha256(bytes)}),{code:'NATIVE_TASK_FILE_CHANGED'});
});

for(const change of ['none','large semantic','input','resource','resource file','input file','scope','schema','unknown canonical'])test(`pending historical native materialization validates ${change} without rewriting or creating preparation`,async t=>{
  const root=await fixture(t),directory=join(root,'native'),inputDirectory=join(directory,'inputs'),resourceDirectory=join(directory,'resources');
  await mkdir(inputDirectory,{recursive:true});await mkdir(resourceDirectory);
  const inputPath=join(inputDirectory,`input-${sha256('jobs')}.json`),content=Buffer.from('old exact pinned text'),resourcePath=join(resourceDirectory,`resource-${sha256(content)}.md`);
  const inputs={jobs:[{id:'one',task:'exact assigned work'}]};await writeFile(inputPath,canonicalJSON(inputs.jobs));await writeFile(resourcePath,content);
  const references=[{path:'reference.md',sha256:sha256(content),bytes:content.length}];
  const envelope={workspace:root,access:'read_only',node_id:'writer',prompt_template:change==='large semantic'?'Complete the assigned work. '.repeat(460):'Complete the assigned work.',inputs,resources:['reference.md'],context_projection:{references}};
  const reference=`Read this bound input from the local file at ${canonicalJSON(inputPath)} (format: json).`;
  const bundle={schema_version:1,task:compilePrompt({...envelope,inputs:{jobs:reference}},64000),workspace:root,access:'read_only',writable_paths:[],
    result_schema:{type:'object'},resources:[{path:'reference.md',sha256:sha256(content),bytes:content.length,local_path:resourcePath}],verified_files:[]};
  const path=join(directory,'task.json'),bytes=Buffer.from(canonicalJSON(bundle));await writeFile(path,bytes);
  const args={directory,envelope,resources:[{path:'reference.md',sha256:sha256(content),size:content.length,bytes:content}],resultSchema:{type:'object'},allowedPaths:[]};
  if(change==='input')args.envelope={...envelope,inputs:{jobs:[{id:'other',task:'foreign work'}]}};
  if(change==='resource'){const changed=Buffer.from('different pinned text');args.resources=[{path:'reference.md',sha256:sha256(changed),size:changed.length,bytes:changed}];}
  if(change==='resource file')await writeFile(resourcePath,'changed');
  if(change==='input file')await writeFile(inputPath,'changed');
  if(change==='scope')args.allowedPaths=['different'];
  if(change==='schema')args.resultSchema={type:'string'};
  if(change==='unknown canonical')await writeFile(path,canonicalJSON({...bundle,schema_version:99}));
  const canonicalBefore=await readFile(path);
  let semanticSidecar=false;
  if(['none','large semantic'].includes(change)){
    const retained=await materializeNativeTaskBundle(args);assert.equal(retained.task_bundle_sha256,sha256(bytes));
    const projection=await readNativeTaskProjection(retained,{materialize:true});
    let semantic=projection.task_bundle;
    if(!projection.inline){
      semanticSidecar=true;
      const sidecar=await readFile(projection.task_bundle_path);
      assert(sidecar.length>NATIVE_TASK_INLINE_LIMIT,'A sidecar is needed only above the existing inline byte limit');
      assert.equal(sha256(sidecar),projection.task_bundle_sha256);
      semantic=JSON.parse(sidecar);
    }else assert(Buffer.byteLength(canonicalJSON(semantic))<=NATIVE_TASK_INLINE_LIMIT);
    assert.equal(semantic.schema_version,1);
    assert.equal(semantic.task,bundle.task);
    assert.equal(semantic.workspace,root);
    assert.deepEqual(semantic.resources,[{path:'reference.md',local_path:resourcePath}]);
    if(change==='large semantic')assert.equal(projection.inline,false);
  }else await assert.rejects(materializeNativeTaskBundle(args),error=>['NODE_INPUT_MATERIALS_CONFLICT','NATIVE_TASK_FILE_CHANGED','NATIVE_TASK_BUNDLE'].includes(error.code));
  assert.deepEqual(await readFile(path),canonicalBefore);
  assert.deepEqual(await readdir(directory),semanticSidecar?['inputs','resources','semantic-task.json','task.json']:['inputs','resources','task.json']);
});

test('native semantic sidecar is bounded and verified exactly after saving and on replay',async t=>{
  const root=await fixture(t),receipt=await materializeNativeTaskBundle({directory:join(root,'native'),
    envelope:{workspace:root,access:'read_only',inputs:{},prompt_template:'Long authored instruction. '.repeat(490)}});
  const projected=await readNativeTaskProjection(receipt,{materialize:true});assert.equal(projected.inline,false);
  const bytes=await readFile(projected.task_bundle_path);assert(bytes.length>12000&&bytes.length<=16*1024);
  assert.equal(sha256(bytes),projected.task_bundle_sha256);assert.deepEqual(await readNativeTaskProjection(receipt),projected);
  assert(!bytes.includes(Buffer.from('context_preparation')));
  await writeFile(projected.task_bundle_path,Buffer.from('changed'));
  await assert.rejects(readNativeTaskProjection(receipt,{materialize:true}),{code:'NODE_INPUT_MATERIALS_CONFLICT'});
  await assert.rejects(readNativeTaskProjection(receipt),{code:'NATIVE_TASK_BUNDLE'});
  await assert.rejects(materializeNativeTaskBundle({directory:join(root,'too-large'),
    envelope:{workspace:root,access:'read_only',inputs:{},prompt_template:'x'.repeat(17000)}}),{code:'NATIVE_TASK_INDEX_LIMIT'});
});

for(const target of ['canonical','preparation','resource','verified','input','scope','schema'])test(`native semantic projection rejects changed ${target} before delivery`,async t=>{
  const root=await fixture(t),source=join(root,'draft.md'),resource=Buffer.from('exact declared reference');await writeFile(source,'declared draft');
  const receipt=await materializeNativeTaskBundle({directory:join(root,'native'),envelope:{workspace:root,access:'bounded_write',resources:['reference.md'],
    inputs:{source:{source_path:source,source_sha256:sha256('declared draft')},large:'X'.repeat(9000)}},allowedPaths:['page'],resultSchema:{type:'object'},
    resources:[{path:'reference.md',sha256:sha256(resource),size:resource.length,bytes:resource}]});
  const bundle=JSON.parse(await readFile(receipt.task_bundle_path)),metadata=JSON.parse(await readFile(bundle.context_preparation.path));
  if(target==='canonical')await writeFile(receipt.task_bundle_path,'changed');
  else if(target==='preparation')await writeFile(bundle.context_preparation.path,'changed');
  else if(['scope','schema'].includes(target)){
    if(target==='scope')bundle.writable_paths=['other'];else bundle.result_schema={type:'string'};
    const bytes=Buffer.from(canonicalJSON(bundle));await writeFile(receipt.task_bundle_path,bytes);receipt.task_bundle_sha256=sha256(bytes);
  }else{
    const material=target==='resource'?metadata.resources[0]:target==='verified'?metadata.verified_files[0]:metadata.inputs.find(item=>item.delivery==='file');
    await writeFile(material.local_path??material.path,'changed');
  }
  await assert.rejects(readNativeTaskProjection(receipt),error=>['MAIN_ORCHESTRATION_BUNDLE','NATIVE_TASK_BUNDLE','NATIVE_TASK_FILE_CHANGED'].includes(error.code));
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
  const metadata=JSON.parse(await readFile(bundle.context_preparation.path,'utf8'));
  assert.equal(metadata.verified_files.length,10);
  assert.ok(Buffer.byteLength(bundleText)<16*1024);
  assert.equal(bundleText.includes('x'.repeat(100)),false);
  assert.deepEqual(await Promise.all(metadata.verified_files.map(async item=>(await stat(item.local_path)).size)),
    jobs.map(()=>JSON.stringify({card_id:'card-0',body:'x'.repeat(6000)}).length));
});
