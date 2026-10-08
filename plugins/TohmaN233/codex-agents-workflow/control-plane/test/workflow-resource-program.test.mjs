import test from 'node:test';
import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { tmpdir } from './physical-tempdir.mjs';
import { digest, canonicalJSON, revisionHash } from '../lib/workflow-revisions.mjs';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { exportWorkflowPackage, validateWorkflowPackage } from '../lib/workflow-package.mjs';
import { rebindBuiltinHostToolIdentities, migrateStoredWorkflowHostToolIdentities, rebindWorkflowPackageHostToolIdentities } from '../lib/workflow-host-tool-identity.mjs';
import { HostToolRunner, requireHostToolExecutionScope, validateHostToolContract } from '../lib/execution/host-tool-runner.mjs';
import { workflowResourceProgramIdentity, workflowResourceProgramRegistry } from '../lib/execution/workflow-resource-program.mjs';

const priorResourceIdentity = { name: 'workflow-resource-program', version: '1',
  sha256: '38c9435bfec1e03827a2279ee0829a1bb6cb821b455a635ee637c00da38f97a0' };
const identityWorkflow = id => ({ ...createDraft(id, 'Identity fixture'), host_tools: [{
  id: 'resource-alias', identity: priorResourceIdentity, argv: ['node', 'scripts/check.mjs', 'work'],
  input_schema: { type: 'object' }, output_schema: { type: 'object' }, env_allow: [],
  permissions: { network: false, read_paths: [], write_paths: ['work'] },
  output_cap_bytes: 4096, deadline_ms: 10000, idempotency: { mode: 'safe' },
}] });

test('built-in Host identity migration changes only exact known identities and rejects unknown implementations', () => {
  const original = identityWorkflow('host-identity'), before = structuredClone(original);
  const { workflow, changes } = rebindBuiltinHostToolIdentities(original);
  assert.deepEqual(original, before);
  assert.deepEqual(workflow, { ...before, host_tools: [{ ...before.host_tools[0], identity: workflowResourceProgramIdentity() }] });
  assert.equal(changes.length, 1);
  assert.deepEqual(rebindBuiltinHostToolIdentities(workflow).changes, []);
  const crlf = structuredClone(original);
  crlf.host_tools[0].identity.sha256 = 'b185499be50c3f6a12c1fc1f2ba533bec45c7ce47a4ca1a76698790bbf6b6f81';
  assert.deepEqual(rebindBuiltinHostToolIdentities(crlf).workflow, workflow);
  const unknown = structuredClone(original); unknown.host_tools[0].identity.sha256 = 'f'.repeat(64);
  assert.throws(() => rebindBuiltinHostToolIdentities(unknown), { code: 'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED' });
  unknown.host_tools[0].identity.name = 'external-tool';
  assert.deepEqual(rebindBuiltinHostToolIdentities(unknown), { workflow: unknown, changes: [] });
});

test('Host identity package rebind rebuilds integrity deterministically and preserves resources and contracts', () => {
  const snapshot = { workflow: identityWorkflow('host-identity-package'), resources: [], provenance: { kind: 'fixture' }, import_report: {} };
  const bundle = exportWorkflowPackage({ ...snapshot, revision_hash: revisionHash(snapshot) }, {});
  const rebound = rebindWorkflowPackageHostToolIdentities(bundle);
  assert.deepEqual(rebound, rebindWorkflowPackageHostToolIdentities(bundle));
  assert.notEqual(rebound.bundle.package_sha256, bundle.package_sha256);
  assert.notEqual(rebound.bundle.snapshot.revision_hash, bundle.snapshot.revision_hash);
  assert.equal(rebound.bundle.snapshot.workflow.revision, bundle.snapshot.workflow.revision + 1);
  assert.deepEqual(rebound.bundle.objects, bundle.objects);
  assert.deepEqual(rebound.bundle.dependencies, bundle.dependencies);
  validateWorkflowPackage(rebound.bundle);
  assert.deepEqual(rebindWorkflowPackageHostToolIdentities(rebound.bundle), { bundle: rebound.bundle, changes: [] });
});

test('saved Host identity migration isolates unknown built-ins and retains immutable prior revisions', async t => {
  const root = await mkdtemp(join(tmpdir(), 'host-identity-store-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const store = await new WorkflowStore(root).initialize();
  const original = await store.create(identityWorkflow('known'), { resources: { 'scripts/check.mjs': 'preserved bytes' } });
  const unknown = identityWorkflow('unknown'); unknown.host_tools[0].identity.sha256 = 'f'.repeat(64);
  const bad = await store.create(unknown);
  const changes = await migrateStoredWorkflowHostToolIdentities(store);
  const current = await store.snapshot('known');
  assert.equal(changes.length, 2);
  const blocked = changes.find(item => item.status === 'blocked');
  assert.equal(blocked.workflow_id, 'unknown');
  assert.equal(blocked.revision_hash, bad.revision_hash);
  assert.equal(blocked.code, 'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED');
  assert.deepEqual(blocked.identity, bad.workflow.host_tools[0].identity);
  assert.deepEqual(await store.snapshot('unknown'), bad);
  assert.equal(current.workflow.revision, original.workflow.revision + 1);
  assert.deepEqual(await store.snapshot('known', original.revision_hash), original);
  assert.deepEqual(await store.resources('known'), await store.resources('known', original.revision_hash));
  assert.deepEqual(await migrateStoredWorkflowHostToolIdentities(store), [blocked]);
  assert.equal(canonicalJSON(current.workflow.nodes), canonicalJSON(original.workflow.nodes));
});

test('resource program implementation identity ignores CRLF spelling but detects changed behavior', async t => {
  const root = await mkdtemp(join(tmpdir(), 'workflow-resource-identity-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  await cp(fileURLToPath(new URL('../lib/', import.meta.url)), join(root, 'lib'), { recursive: true });
  const modulePath = join(root, 'lib/execution/workflow-resource-program.mjs');
  const lf = (await readFile(modulePath, 'utf8')).replace(/\r\n/g, '\n');
  const load = async (source, variant) => {
    await writeFile(modulePath, source);
    return (await import(`${pathToFileURL(modulePath).href}?${variant}`)).workflowResourceProgramIdentity();
  };
  const original = await load(lf, 'lf');
  const crlf = await load(lf.replace(/\n/g, '\r\n'), 'crlf');
  assert.deepEqual(crlf, original);
  const changed = lf.replace('const emptyEffects=()=>({observed:true', 'const emptyEffects=()=>({observed:false');
  assert.notEqual(changed, lf, 'fixture must change actual implementation behavior');
  const modified = await load(changed, 'changed');
  assert.equal(modified.name, original.name);
  assert.equal(modified.version, original.version);
  assert.notEqual(modified.sha256, original.sha256);
});

test('authoring Host implementation identity ignores CRLF spelling but detects changed behavior', async t => {
  const root = await mkdtemp(join(tmpdir(), 'authoring-host-identity-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  await cp(fileURLToPath(new URL('../lib/', import.meta.url)), join(root, 'lib'), { recursive: true });
  const modulePath = join(root, 'lib/execution/authoring-host-tools.mjs');
  const lf = (await readFile(modulePath, 'utf8')).replace(/\r\n/g, '\n');
  const load = async (source, variant) => {
    await writeFile(modulePath, source);
    const module = await import(`${pathToFileURL(modulePath).href}?${variant}`);
    return module.authoringHostToolContracts().map(contract => contract.identity);
  };
  const original = await load(lf, 'lf');
  assert.deepEqual(await load(lf.replace(/\n/g, '\r\n'), 'crlf'), original);
  const changed = lf.replace('permissions:{network:false', 'permissions:{network:true');
  assert.notEqual(changed, lf, 'fixture must change actual implementation behavior');
  const modified = await load(changed, 'changed');
  assert.deepEqual(modified.map(({name,version}) => ({name,version})), original.map(({name,version}) => ({name,version})));
  assert(modified.every((identity, index) => identity.sha256 !== original[index].sha256));
});

test('a Host tool executes one pinned Workflow resource and observes its writes without a model turn', async t => {
  const workspace=await mkdtemp(join(tmpdir(),'workflow-resource-program-'));
  t.after(()=>rm(workspace,{recursive:true,maxRetries:3,retryDelay:100}));
  await mkdir(join(workspace,'work'));
  const path='workflow-assets/scripts/write.mjs';
  const bytes=Buffer.from('import { writeFileSync } from "node:fs"; writeFileSync("work/result.json", JSON.stringify({ok:true})); console.log(JSON.stringify({ok:true}));\n');
  const contract={id:'workflow-resource-program',identity:workflowResourceProgramIdentity(),argv:['node',path,'work/.workflow-runtime'],
    input_schema:{type:'object',additionalProperties:false},output_schema:{type:'object',required:['ok'],additionalProperties:false,properties:{ok:{type:'boolean'}}},
    env_allow:[],permissions:{network:false,read_paths:[path],write_paths:['work']},output_cap_bytes:4096,deadline_ms:30000,idempotency:{mode:'safe'}};
  const runner=new HostToolRunner({registry:workflowResourceProgramRegistry()});
  const executed=await runner.execute(contract,{}, {run_id:'run',node_id:'join',attempt_id:'attempt',workspace,
    permissions:{access:'bounded_write',allowed_paths:['work']},resources:[{path,sha256:digest(bytes),bytes}],
    runtime_environment:{status:'ready',tools:[{name:'node',path:process.execPath,status:'found'}]}});
  assert.equal(executed.receipt.status,'succeeded');
  assert.deepEqual(executed.output,{ok:true});
  assert.deepEqual(JSON.parse(await readFile(join(workspace,'work/result.json'),'utf8')),{ok:true});
  assert(executed.receipt.effects.changed_paths.includes('work/result.json'));
});

test('Host scratch uses the Run scope without widening the resource program business write contract', async t => {
  const workspace=await mkdtemp(join(tmpdir(),'workflow-resource-separated-scratch-'));
  t.after(()=>rm(workspace,{recursive:true,maxRetries:3,retryDelay:100}));
  await mkdir(join(workspace,'work/.workflow-prepared'),{recursive:true});
  const path='workflow-assets/scripts/write-prepared.mjs';
  const bytes=Buffer.from('import { writeFileSync } from "node:fs"; writeFileSync("work/.workflow-prepared/result.json", "{}"); console.log(JSON.stringify({ok:true}));\n');
  const contract={id:'separated-scratch',identity:workflowResourceProgramIdentity(),argv:['node',path,'work/.workflow-runtime'],
    input_schema:{type:'object',additionalProperties:false},output_schema:{type:'object',required:['ok'],additionalProperties:false,properties:{ok:{type:'boolean'}}},
    env_allow:[],permissions:{network:false,read_paths:[path],write_paths:['work/.workflow-prepared']},output_cap_bytes:4096,deadline_ms:30000,idempotency:{mode:'safe'}};
  const redundant={...contract,permissions:{...contract.permissions,write_paths:['work/.workflow-prepared','work/.workflow-runtime']}};
  assert.deepEqual(validateHostToolContract(redundant).permissions.write_paths,['work/.workflow-prepared']);
  const permissions={access:'bounded_write',allowed_paths:['work/.workflow-prepared','work/.workflow-runtime']};
  assert.deepEqual(requireHostToolExecutionScope(contract,permissions).write_paths,['work/.workflow-prepared','work/.workflow-runtime']);
  assert.throws(()=>requireHostToolExecutionScope(contract,{access:'bounded_write',allowed_paths:['work/.workflow-prepared']}),
    error=>error.code==='WORKFLOW_RESOURCE_SCOPE');
  const executed=await new HostToolRunner({registry:workflowResourceProgramRegistry()}).execute(contract,{},
    {run_id:'run',node_id:'join',attempt_id:'attempt',workspace,permissions,resources:[{path,sha256:digest(bytes),bytes}],
      runtime_environment:{status:'ready',tools:[{name:'node',path:process.execPath,status:'found'}]}});
  assert.equal(executed.receipt.status,'succeeded',executed.receipt.diagnostics.message);
  assert.deepEqual(executed.receipt.effects.changed_paths,['work/.workflow-prepared/result.json']);
});

test('the Host resource broker cannot report success for a write outside the node scope', async t => {
  const workspace=await mkdtemp(join(tmpdir(),'workflow-resource-scope-'));
  t.after(()=>rm(workspace,{recursive:true,maxRetries:3,retryDelay:100}));
  await mkdir(join(workspace,'work'));
  const path='workflow-assets/scripts/escape.mjs';
  const bytes=Buffer.from('import { writeFileSync } from "node:fs"; writeFileSync("outside.json", "{}"); console.log(JSON.stringify({ok:true}));\n');
  const contract={id:'workflow-resource-program',identity:workflowResourceProgramIdentity(),argv:['node',path,'work/.workflow-runtime'],
    input_schema:{type:'object',additionalProperties:false},output_schema:{type:'object',required:['ok'],additionalProperties:false,properties:{ok:{type:'boolean'}}},
    env_allow:[],permissions:{network:false,read_paths:[path],write_paths:['work']},output_cap_bytes:4096,deadline_ms:30000,idempotency:{mode:'safe'}};
  const runner=new HostToolRunner({registry:workflowResourceProgramRegistry()});
  const executed=await runner.execute(contract,{}, {run_id:'run',node_id:'join',attempt_id:'attempt',workspace,
    permissions:{access:'bounded_write',allowed_paths:['work']},resources:[{path,sha256:digest(bytes),bytes}],
    runtime_environment:{status:'ready',tools:[{name:'node',path:process.execPath,status:'found'}]}});
  assert.equal(executed.receipt.status,'failed');
  assert.deepEqual(executed.receipt.effects.outside_paths,['outside.json']);
});

test('a failing Workflow resource returns a failed Host receipt and removes its scratch script',async t=>{
  const workspace=await mkdtemp(join(tmpdir(),'workflow-resource-failure-'));
  t.after(()=>rm(workspace,{recursive:true,maxRetries:3,retryDelay:100}));
  await mkdir(join(workspace,'work'));
  const path='workflow-assets/scripts/fail.mjs';
  const bytes=Buffer.from('process.stderr.write("deliberate failure"); process.exitCode=7;\n');
  const contract={id:'workflow-resource-program',identity:workflowResourceProgramIdentity(),argv:['node',path,'work/.workflow-runtime'],
    input_schema:{type:'object',additionalProperties:false},output_schema:{type:'object',additionalProperties:false},
    env_allow:[],permissions:{network:false,read_paths:[path],write_paths:['work']},output_cap_bytes:4096,deadline_ms:30000,idempotency:{mode:'safe'}};
  const runner=new HostToolRunner({registry:workflowResourceProgramRegistry()});
  const executed=await runner.execute(contract,{}, {run_id:'run',node_id:'join',attempt_id:'attempt',workspace,
    permissions:{access:'bounded_write',allowed_paths:['work']},resources:[{path,sha256:digest(bytes),bytes}],
    runtime_environment:{status:'ready',tools:[{name:'node',path:process.execPath,status:'found'}]}});
  assert.equal(executed.receipt.status,'failed');
  assert.match(executed.receipt.diagnostics.message,/deliberate failure/);
  await assert.rejects(readFile(join(workspace,'work/.workflow-runtime',`${digest(bytes)}.mjs`)),{code:'ENOENT'});
});

test('Host passes projected structured input and a second pinned resource without model transcription',async t=>{
  const workspace=await mkdtemp(join(tmpdir(),'workflow-resource-input-'));
  t.after(()=>rm(workspace,{recursive:true,maxRetries:3,retryDelay:100}));
  await mkdir(join(workspace,'work'));
  const primary='workflow-assets/scripts/use-input.mjs',secondary='workflow-assets/scripts/reference.json';
  const script=Buffer.from('import { readFileSync } from "node:fs"; const input=JSON.parse(readFileSync(process.argv[2],"utf8")); const ref=JSON.parse(readFileSync(process.argv[3],"utf8")); console.log(JSON.stringify({count:input.jobs.length,version:ref.version}));\n');
  const reference=Buffer.from('{"version":3}\n');
  const contract={id:'structured-resource-job',identity:workflowResourceProgramIdentity(),
    argv:['node',primary,'work/.workflow-runtime','@INPUT@',`@RESOURCE:${secondary}@`],
    input_schema:{type:'object',properties:{jobs:{type:'array',items:{type:'integer'}}},required:['jobs'],additionalProperties:false},
    output_schema:{type:'object',properties:{count:{type:'integer'},version:{type:'integer'}},required:['count','version'],additionalProperties:false},
    env_allow:[],permissions:{network:false,read_paths:[primary,secondary],write_paths:['work']},output_cap_bytes:4096,
    deadline_ms:30000,idempotency:{mode:'safe'}};
  const runner=new HostToolRunner({registry:workflowResourceProgramRegistry()});
  const executed=await runner.execute(contract,{jobs:[1,2,3]}, {run_id:'run',node_id:'join',attempt_id:'attempt',workspace,
    permissions:{access:'bounded_write',allowed_paths:['work']},resources:[{path:primary,sha256:digest(script),bytes:script},
      {path:secondary,sha256:digest(reference),bytes:reference}],
    runtime_environment:{status:'ready',tools:[{name:'node',path:process.execPath,status:'found'}]}});
  assert.equal(executed.receipt.status,'succeeded',executed.receipt.diagnostics.message);
  assert.deepEqual(executed.output,{count:3,version:3});
  assert.deepEqual(executed.receipt.effects.changed_paths,[]);
});
