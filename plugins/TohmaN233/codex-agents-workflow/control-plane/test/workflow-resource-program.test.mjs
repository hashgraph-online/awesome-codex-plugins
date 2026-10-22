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
import { HostToolRunner, PROGRAM_ENVIRONMENT_ADMISSION, requireHostToolExecutionScope, validateHostToolContract } from '../lib/execution/host-tool-runner.mjs';
import { workflowResourceProgramIdentity, workflowResourceProgramRegistry } from '../lib/execution/workflow-resource-program.mjs';

const priorResourceIdentity = { name: 'workflow-resource-program', version: '1',
  sha256: '38c9435bfec1e03827a2279ee0829a1bb6cb821b455a635ee637c00da38f97a0' };
test('program admission upgrade rebinds only the exact installed dependency predecessor',()=>{
  const workflow=structuredClone(identityWorkflow('program-admission-upgrade'));
  workflow.host_tools[0].identity.sha256='2a9a9d29b2055e0e187914c3d35d247a4ad0dfede2855f2ad809551a9e35e6c9';
  const before=structuredClone(workflow),result=rebindBuiltinHostToolIdentities(workflow);
  assert.deepEqual(workflow,before);assert.equal(result.changes.length,1);
  assert.deepEqual(result.workflow.host_tools[0].identity,workflowResourceProgramIdentity());
  workflow.host_tools[0].identity.sha256='d'.repeat(64);
  assert.throws(()=>rebindBuiltinHostToolIdentities(workflow),{code:'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED'});
});
const identityWorkflow = id => ({ ...createDraft(id, 'Identity fixture'), host_tools: [{
  id: 'resource-alias', identity: priorResourceIdentity, argv: ['node', 'scripts/check.mjs', 'work'],
  input_schema: { type: 'object' }, output_schema: { type: 'object' }, env_allow: [],
  permissions: { network: false, read_paths: [], write_paths: ['work'] },
  output_cap_bytes: 4096, deadline_ms: 10000, idempotency: { mode: 'safe' },
}] });

test('Host input cap is opt-in, bounded, and retained in portable package integrity', () => {
  const original=identityWorkflow('input-cap-package');
  const normalized=validateHostToolContract(original.host_tools[0]);
  assert.equal(Object.hasOwn(normalized,'input_cap_bytes'),false);
  const declared={...original.host_tools[0],input_cap_bytes:16*1024*1024};
  assert.equal(validateHostToolContract(declared).input_cap_bytes,16*1024*1024);
  for(const bad of [0,-1,1.5,16*1024*1024+1,null,'262144',Infinity,NaN]){
    assert.throws(()=>validateHostToolContract({...declared,input_cap_bytes:bad}),{code:'HOST_TOOL_CONTRACT'});
  }
  const snapshot={workflow:{...original,host_tools:[declared]},resources:[],provenance:{kind:'fixture'},import_report:{}};
  const bundle=exportWorkflowPackage({...snapshot,revision_hash:revisionHash(snapshot)},{});
  validateWorkflowPackage(bundle);
  assert.equal(bundle.snapshot.workflow.host_tools[0].input_cap_bytes,16*1024*1024);
  const altered=structuredClone(bundle);altered.snapshot.workflow.host_tools[0].input_cap_bytes-=1;
  assert.throws(()=>validateWorkflowPackage(altered));
});

test('actual resource execution admits declared large input and rejects overflow before any broker call', async t => {
  const workspace=await mkdtemp(join(tmpdir(),'workflow-resource-input-cap-'));
  t.after(()=>rm(workspace,{recursive:true,maxRetries:3,retryDelay:100}));
  await mkdir(join(workspace,'work'));
  const path='source/input.mjs',bytes=Buffer.from('import {readFileSync} from "node:fs";const input=JSON.parse(readFileSync(process.argv[2],"utf8"));console.log(JSON.stringify({bytes:Buffer.byteLength(input.text)}));');
  const contract={id:'input-cap',identity:workflowResourceProgramIdentity(),argv:['node',path,'work/.workflow-runtime','@INPUT@'],
    input_schema:{type:'object',required:['text'],properties:{text:{type:'string'}},additionalProperties:false},
    output_schema:{type:'object',required:['bytes'],properties:{bytes:{type:'integer'}},additionalProperties:false},
    env_allow:[],permissions:{network:false,read_paths:[path],write_paths:['work']},output_cap_bytes:4096,deadline_ms:30000,idempotency:{mode:'safe'}};
  const registry=workflowResourceProgramRegistry();let brokerCalls=0;
  for(const entry of Object.values(registry)){const execute=entry.execute;entry.execute=(...args)=>{brokerCalls++;return execute(...args);};}
  const runner=new HostToolRunner({registry}),context={run_id:'run',node_id:'tool',attempt_id:'attempt',workspace,
    permissions:{access:'bounded_write',allowed_paths:['work']},resources:[{path,bytes,sha256:digest(bytes)}],
    runtime_environment:{status:'ready',tools:[{name:'node',path:process.execPath,status:'found'}]}};
  const input={text:'x'.repeat(128*1024)},inputBytes=Buffer.byteLength(canonicalJSON(input));
  await assert.rejects(runner.execute(contract,input,context),{code:'HOST_TOOL_INPUT_LIMIT'});assert.equal(brokerCalls,0);
  const executed=await runner.execute({...contract,input_cap_bytes:inputBytes},input,context);
  assert.equal(executed.receipt.status,'succeeded',executed.receipt.diagnostics.message);
  assert.equal(executed.output.bytes,128*1024);assert.equal(brokerCalls,1);
  await assert.rejects(runner.execute({...contract,input_cap_bytes:inputBytes-1},input,context),{code:'HOST_TOOL_INPUT_LIMIT'});
  assert.equal(brokerCalls,1);
  // The default still accepts its exact byte boundary; JSON escaping is counted.
  const small={text:'x'.repeat(128*1024-Buffer.byteLength(canonicalJSON({text:''})))};
  assert.equal(Buffer.byteLength(canonicalJSON(small)),128*1024);
  assert.equal((await runner.execute(contract,small,context)).receipt.status,'succeeded');
  const escaped={text:'\u0001'.repeat(24000)};assert(Buffer.byteLength(canonicalJSON(escaped))>128*1024);
  await assert.rejects(runner.execute(contract,escaped,context),{code:'HOST_TOOL_INPUT_LIMIT'});assert.equal(brokerCalls,2);
});

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

test('worker completion slot upgrade recognizes only its exact immediate resource-program predecessor',()=>{
  const original=structuredClone(identityWorkflow('worker-slot-upgrade'));
  original.host_tools[0].identity.sha256='34b73488bfa8a67587e7e7365784513c79f94f420827352d35e2a8a02b181bb1';
  const before=structuredClone(original),changed=rebindBuiltinHostToolIdentities(original);
  assert.deepEqual(original,before);assert.equal(changed.changes.length,1);
  assert.deepEqual(changed.workflow,{...before,host_tools:[{...before.host_tools[0],identity:workflowResourceProgramIdentity()}]});
  original.host_tools[0].identity.sha256='f'.repeat(64);assert.throws(()=>rebindBuiltinHostToolIdentities(original),{code:'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED'});
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
  await mkdir(join(root,'control-plane'),{recursive:true});
  await cp(fileURLToPath(new URL('../lib/', import.meta.url)), join(root, 'control-plane/lib'), { recursive: true });
  await cp(fileURLToPath(new URL('../../scripts/', import.meta.url)),join(root,'scripts'),{recursive:true});
  await cp(fileURLToPath(new URL('../../agent-profiles/', import.meta.url)),join(root,'agent-profiles'),{recursive:true});
  const modulePath = join(root, 'control-plane/lib/execution/workflow-resource-program.mjs');
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

test('Host configured environment and registry helper PATH reach the actual resource child', async t => {
  const workspace=await mkdtemp(join(tmpdir(),'workflow-resource-env-'));
  t.after(()=>rm(workspace,{recursive:true,maxRetries:3,retryDelay:100}));
  await mkdir(join(workspace,'work'));const path='source/env.mjs';
  const bytes=Buffer.from('console.log(JSON.stringify({value:process.env.WORKFLOW_FIXTURE_ENV??null,path:process.env.PATH??null}));');
  const contract={id:'scoped-env',identity:workflowResourceProgramIdentity(),argv:['node',path,'work/.workflow-runtime'],
    input_schema:{type:'object',additionalProperties:false},output_schema:{type:'object',required:['value','path'],properties:{value:{type:'string'},path:{type:'string'}}},
    env_allow:['WORKFLOW_FIXTURE_ENV'],permissions:{network:false,read_paths:[path],write_paths:['work']},output_cap_bytes:8192,deadline_ms:30000,idempotency:{mode:'safe'}};
  const runner=new HostToolRunner({registry:workflowResourceProgramRegistry(),env:{WORKFLOW_FIXTURE_ENV:'host-configured-fixture'}});
  const executed=await runner.execute(contract,{}, {run_id:'run',node_id:'export',attempt_id:'attempt',workspace,
    permissions:{access:'bounded_write',allowed_paths:['work']},resources:[{path,sha256:digest(bytes),bytes}],
    runtime_environment:{status:'ready',tools:[{name:'node',path:process.execPath,status:'found'}]}});
  assert.equal(executed.receipt.status,'succeeded',executed.receipt.diagnostics.message);
  assert.equal(executed.output.value,'host-configured-fixture');
  assert(executed.output.path.includes(process.execPath.slice(0,process.execPath.lastIndexOf(process.platform==='win32'?'\\':'/'))));
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

const platformEnvironmentFixture=process.platform==='win32'?{
 pAtH:'C:\\fixture\\bin',pAtHeXt:'.COM;.EXE;.BAT;.CMD',tEmP:'C:\\fixture\\tmp',tMp:'C:\\fixture\\tmp',tMpDiR:42,
 sYsTeMrOoT:'C:\\Windows',WiNdIr:'C:\\Windows',hOmE:'C:\\Users\\fixture',uSeR:'fixture-user',lOgNaMe:'fixture-user',
 uSeRnAmE:'fixture-user',uSeRpRoFiLe:'C:\\Users\\fixture',hOmEdRiVe:'C:',hOmEpAtH:'\\Users\\fixture',
 lOcAlApPdAtA:'C:\\Users\\fixture\\AppData\\Local',aPpDaTa:'C:\\Users\\fixture\\AppData\\Roaming',
 aPp_MoDe:'render',aPi_KeY:'fixture-key',iNvAlId_VaLuE:{ignored:true},nOdE_OpTiOnS:'--require=fixture-hook',sEcReT_TokEn:'hidden',
}:{
 PATH:'/fixture/bin',TMPDIR:42,TMP:'/fixture/tmp',TEMP:'/fixture/tmp',HOME:'/home/fixture',USER:'fixture-user',LOGNAME:'fixture-user',
 APP_MODE:'render',API_KEY:'fixture-key',INVALID_VALUE:{ignored:true},NODE_OPTIONS:'--require=fixture-hook',SECRET_TOKEN:'hidden',
};
const environmentEffects={observed:true,changed_paths:[],outside_paths:[],artifacts:[]};

test('program-admitted Host tools receive only canonical string platform variables plus explicit allowlist values',async()=>{
 const identity=workflowResourceProgramIdentity(),registry=workflowResourceProgramRegistry(),program=registry['workflow-resource-program'];
 assert.equal(program[PROGRAM_ENVIRONMENT_ADMISSION],true);
 const contract={id:'workflow-resource-program',identity,argv:['node','fixture.mjs','work/.workflow-runtime'],
  input_schema:{type:'object',additionalProperties:false},output_schema:{type:'object',properties:{ok:{type:'boolean'}},required:['ok'],additionalProperties:false},
  env_allow:['APP_MODE','API_KEY','INVALID_VALUE','SYSTEMROOT','WINDIR'],permissions:{network:false,read_paths:[],write_paths:['work']},
  output_cap_bytes:1024,deadline_ms:1000,idempotency:{mode:'safe'}};
 let received;program.execute=async({env})=>{received=env;return {exit_code:0,diagnostic:'',effects:environmentEffects,output:{ok:true}};};
 const context={run_id:'run',node_id:'tool',attempt_id:'attempt',permissions:{access:'bounded_write',allowed_paths:['work']}};
 const result=await new HostToolRunner({registry,env:platformEnvironmentFixture}).execute(contract,{},context);
 assert.equal(result.receipt.status,'succeeded');
 const expected=process.platform==='win32'?{
  PATH:'C:\\fixture\\bin',PATHEXT:'.COM;.EXE;.BAT;.CMD',TEMP:'C:\\fixture\\tmp',TMP:'C:\\fixture\\tmp',
  SystemRoot:'C:\\Windows',windir:'C:\\Windows',HOME:'C:\\Users\\fixture',USER:'fixture-user',LOGNAME:'fixture-user',
  USERNAME:'fixture-user',USERPROFILE:'C:\\Users\\fixture',HOMEDRIVE:'C:',HOMEPATH:'\\Users\\fixture',
  LOCALAPPDATA:'C:\\Users\\fixture\\AppData\\Local',APPDATA:'C:\\Users\\fixture\\AppData\\Roaming',
  APP_MODE:'render',API_KEY:'fixture-key',
 }:{PATH:'/fixture/bin',TMP:'/fixture/tmp',TEMP:'/fixture/tmp',HOME:'/home/fixture',USER:'fixture-user',LOGNAME:'fixture-user',APP_MODE:'render',API_KEY:'fixture-key'};
 assert.deepEqual(received,expected);
 if(process.platform==='win32'){
  assert.equal(Object.keys(received).filter(name=>name.toUpperCase()==='SYSTEMROOT').join(','),'SystemRoot');
  assert.equal(Object.keys(received).filter(name=>name.toUpperCase()==='WINDIR').join(','),'windir');
 }
 for(const name of ['NODE_OPTIONS','SECRET_TOKEN','INVALID_VALUE','TMPDIR'])assert.equal(Object.hasOwn(received,name),false,name);
});

test('ordinary Host brokers receive only their explicit string env_allow values',async()=>{
 const identity={name:'fixture-tool',version:'1',sha256:'a'.repeat(64)},contract={id:'fixture-tool',identity,argv:['fixture-tool'],
  input_schema:{type:'object',additionalProperties:false},output_schema:{type:'object',properties:{ok:{type:'boolean'}},required:['ok'],additionalProperties:false},
  env_allow:['APP_MODE','API_KEY','INVALID_VALUE','SYSTEMROOT','WINDIR'],permissions:{network:false,read_paths:[],write_paths:[]},
  output_cap_bytes:1024,deadline_ms:1000,idempotency:{mode:'safe'}};
 let received;const entry={identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:identity,broker_id:'fixture',evidence_sha256:'b'.repeat(64)},
  async execute({env}){received=env;return {exit_code:0,diagnostic:'',effects:environmentEffects,output:{ok:true}};},
  async cancel(){return {termination_confirmed:true,evidence:[{kind:'fixture',sha256:'c'.repeat(64)}],effects:environmentEffects};}};
 const context={run_id:'run',node_id:'tool',attempt_id:'attempt',permissions:{access:'read_only',allowed_paths:[]}};
 const result=await new HostToolRunner({registry:{[contract.id]:entry},env:platformEnvironmentFixture}).execute(contract,{},context);
 assert.equal(result.receipt.status,'succeeded');
 const expected={APP_MODE:'render',API_KEY:'fixture-key',...(process.platform==='win32'?{SYSTEMROOT:'C:\\Windows',WINDIR:'C:\\Windows'}:{})};
 assert.deepEqual(received,expected);
});
