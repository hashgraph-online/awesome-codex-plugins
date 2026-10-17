import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { setImmediate } from 'node:timers/promises';
import { readFile } from 'node:fs/promises';
import { canonicalJSON } from '../lib/workflow-revisions.mjs';
import { workflowToolDefinitions } from '../lib/workflow-tools.mjs';
import { handleRpc, DEFAULT_CONFIG_PATH } from '../server.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { WORKFLOW_WAIT_SECONDS, WORKFLOW_EXECUTION_TOOL_NAMESPACE, WORKFLOW_DIRECT_TOOLS, workflowMcpTransport } from '../lib/workflow-call-policy.mjs';
import { WORKFLOW_WAIT_MS } from '../lib/workflow-wait.mjs';
import { WORKFLOW_CALL_DEFAULTS, WORKFLOW_LONG_CALL_TOOLS, workflowCallInvocation,
  workflowLegacyCallAdapterDescriptor as workflowCallAdapterDescriptor, workflowCallArguments, workflowCallResume,
  workflowOrchestrationArguments, workflowOrchestrationInvocation, workflowLegacyStartupAdapterDescriptor as workflowStartupAdapterDescriptor,
  workflowLegacyOrdinaryStartupAdapterDescriptor as workflowOrdinaryStartupAdapterDescriptor,
  workflowLegacyNativeSpawnBatchAdapterDescriptor as workflowNativeSpawnBatchAdapterDescriptor,
  workflowLegacyPreparedStartupAdapterDescriptor as workflowPreparedStartupAdapterDescriptor,
  workflowLegacyStartupReferenceAdapterDescriptor as workflowStartupReferenceAdapterDescriptor } from '../lib/execution/workflow-call-adapter.mjs';
import * as direct from '../lib/execution/workflow-call-adapter.mjs';

test('complete prepared startup treats semantic values as canonical data and owns all call syntax',async()=>{
 const output=JSON.parse('{"__proto__":{"marker":"data"},"text":"quoted \\\"data\\\" ` ${literal}"}');
 const descriptor=workflowPreparedStartupAdapterDescriptor(startArgs(),'a'.repeat(64),output);
 assert.equal(descriptor.slot,'none');assert(!Object.hasOwn(descriptor,'code_prefix'));
 let received;
 await execute(descriptor.code,'workflow_start',async args=>{received=args;});
 assert.deepEqual(JSON.parse(JSON.stringify(received.initial_output)),output);
 assert(Object.hasOwn(received.initial_output,'__proto__'));assert.equal(Object.getPrototypeOf(received.initial_output).marker,undefined);
 for(const key of ['initial_output','revision_hash','launch_key'])
  assert.throws(()=>workflowPreparedStartupAdapterDescriptor({...startArgs(),[key]:'replacement'},'a'.repeat(64),output),{code:'WORKFLOW_STARTUP_FIELDS'});
 assert.throws(()=>workflowPreparedStartupAdapterDescriptor(startArgs(),'invalid',output),{code:'WORKFLOW_STARTUP_REVISION'});
 assert.throws(()=>workflowPreparedStartupAdapterDescriptor(startArgs(),'a'.repeat(64),output,{}),{code:'WORKFLOW_CALL_OPTIONS'});
});

const startArgs = () => ({ workflow_id: 'example', workspace: 'G:\\Baiduyun', access: 'bounded_write', allowed_paths: ['output'] });
const execute = (code, toolName, call, text = () => {}, context = {}) => {
  context.tools = { [`mcp__codex_agents_workflow__${toolName}`]: call }; context.text = text;
  return new vm.Script(`(async () => {\n${code}\n})()`).runInNewContext(context);
};

test('generic controller adapters bind exact resume and cancel authority without a model-filled slot',async()=>{
 const authority={run_id:'ordinary-fixture',control_token:'host-only-"token" ` ${data}'};
 for(const operation of ['resume','cancel']){
  const adapter=direct.workflowControllerAdapterDescriptor(operation,authority);
  assert.equal(adapter.slot,'none');assert.equal(adapter.scope,'workflow_controller_only');
  assert.equal(adapter.tool_name,`workflow_${operation}`);
  let received;
  await execute(adapter.code,adapter.tool_name,async args=>{received=JSON.parse(JSON.stringify(args));return {content:[{type:'text',text:'exact-result'}]};},text=>assert.equal(text,'exact-result'));
  assert.deepEqual(received,authority);assert.equal(Object.hasOwn(adapter,'code_prefix'),false);
 }
 assert.throws(()=>direct.workflowControllerAdapterDescriptor('delete',authority),{code:'WORKFLOW_CONTROLLER_OPERATION'});
 assert.throws(()=>direct.workflowControllerAdapterDescriptor('resume',authority,{}),{code:'WORKFLOW_CALL_OPTIONS'});
 assert.throws(()=>direct.workflowControllerAdapterDescriptor('cancel',{run_id:authority.run_id}),/control_token|required/);
});

test('authoring controller adapters bind exact authority with no model-filled slot',async()=>{
 const authority={run_id:'authoring-fixture',control_token:'host-only-"token" ` ${data}'};
 for(const operation of ['drive','resume','cancel']){
  const adapter=direct.workflowAuthoringControllerAdapterDescriptor(operation,authority);
  assert.equal(adapter.slot,'none');assert.equal(adapter.scope,'authoring_controller_only');
  assert.equal(adapter.tool_name,`workflow_${operation}`);
  assert(adapter.code.startsWith('// @exec: {"max_output_tokens":10000,"yield_time_ms":3600000}'));
  let received;
  await execute(adapter.code,adapter.tool_name,async args=>{received=JSON.parse(JSON.stringify(args));return {content:[{type:'text',text:'exact-result'}]};},text=>assert.equal(text,'exact-result'));
  assert.deepEqual(received,authority);assert.equal(Object.hasOwn(adapter,'code_prefix'),false);
 }
 assert.throws(()=>direct.workflowAuthoringControllerAdapterDescriptor('delete',authority),{code:'AUTHORING_CONTROLLER_OPERATION'});
 assert.throws(()=>direct.workflowAuthoringControllerAdapterDescriptor('drive',authority,{}),{code:'WORKFLOW_CALL_OPTIONS'});
 assert.throws(()=>direct.workflowAuthoringControllerAdapterDescriptor('drive',{run_id:authority.run_id}),/control_token|required/);
});

test('normal prepared adapters embed only the exact reference with an optional fresh semantic JSON slot',async()=>{
 const reference='12345678-1234-4234-8234-123456789abc';
 const output=JSON.parse('{"__proto__":{"marker":"data"},"text":"quoted \\"data\\" ` ${literal}"}');
 for(const typed of [true,false]){
  const descriptor=workflowStartupReferenceAdapterDescriptor(reference,typed);
  const code=typed?descriptor.code:descriptor.code_prefix+canonicalJSON(output)+descriptor.code_suffix;
  assert.equal(descriptor.slot,typed?'none':'initial_output');assert.equal(descriptor.tool_name,'workflow_start_prepared');
  for(const field of ['revision_hash','startup_inputs_sha256','workspace','access','launch_key'])assert(!code.includes(field));
  let received;await execute(code,'workflow_start_prepared',async args=>{received=JSON.parse(JSON.stringify(args));});
  assert.deepEqual(received,{startup_reference:reference,...(typed?{}:{initial_output:output})});
 }
 for(const invalid of ['',reference.toUpperCase(),'../'+reference])assert.throws(()=>workflowStartupReferenceAdapterDescriptor(invalid,false),{code:'WORKFLOW_PREPARATION_REFERENCE'});
 assert.throws(()=>workflowStartupReferenceAdapterDescriptor(reference,false,{}),{code:'WORKFLOW_CALL_OPTIONS'});
});

test('all adopted adapters present exact singleton MCP text without reserializing its envelope', async () => {
  const pinned = workflowStartupAdapterDescriptor(startArgs(), 'a'.repeat(64));
  const invocations = [
    ...WORKFLOW_LONG_CALL_TOOLS.map(name => ({ name, code: workflowCallInvocation(name, name === 'workflow_start_prepared' ? {startup_reference:'12345678-1234-4234-8234-123456789abc'} : name === 'workflow_start' ? startArgs()
      : name === 'workflow_orchestration_complete' ? { output: { conclusion: 'done' } } : {}) })),
    { name: 'workflow_start', code: pinned.code_prefix + canonicalJSON({ conclusion: 'startup' }) + pinned.code_suffix },
    { name: 'workflow_start', code: workflowOrdinaryStartupAdapterDescriptor(startArgs()).code },
    { name: 'workflow_native_spawned_batch', code: workflowNativeSpawnBatchAdapterDescriptor('b'.repeat(64)).code },
  ];
  for (const { name, code } of invocations) for (const value of ['{"status":"succeeded","value":"雪\\n${literal}"}', 'opaque text, not JSON', '\n  opaque text \r\n\t', '']) {
    let calls = 0; const outputs = [], result = { content: [{ type: 'text', text: value }] };
    await execute(code, name, async () => { calls++; return result; }, value => outputs.push(value));
    assert.equal(calls, 1); assert.deepEqual(outputs, [value]);
    assert.deepEqual(JSON.parse(code.split('\n')[0].slice('// @exec: '.length)), WORKFLOW_CALL_DEFAULTS);
  }
});

test('adopted result presentation preserves complete errors, metadata, multipart and raw values', async () => {
  const block = () => ({ type: 'text', text: '{"status":"succeeded"}' });
  const results = [
    { content: [block()], isError: true }, { content: [block()], isError: false },
    { content: [block()], structuredContent: { status: 'succeeded' } }, { content: [block()], _meta: { observation: 'retain' } },
    { content: [block(), block()] }, { content: [{ type: 'image', data: 'AA==', mimeType: 'image/png' }] },
    { content: [{ ...block(), annotations: { audience: ['user'] } }] }, { content: [{ ...block(), _meta: { observation: 'retain' } }] }, { content: [{ ...block(), extra: 'retain' }] },
    { content: [{ type: 'text', text: 17 }] }, { content: [{ type: 'text' }] }, { content: [null] },
    { content: [] }, { content: 'raw' }, { content: [block()], status: 'unknown' },
    Object.defineProperty({ content: [block()] }, 'metadata', { value: 'retain' }),
    { content: [Object.defineProperty(block(), 'metadata', { value: 'retain' })] },
    { content: Object.assign([block()], { metadata: 'retain' }) },
    { content: [block()], [Symbol('metadata')]: 'retain' },
    undefined, null, 'raw text', 17, false, [block()], { result: { content: [block()] } },
  ];
  for (const result of results) {
    const outputs = [];
    await execute(workflowCallInvocation('workflow_native_next', {}), 'workflow_native_next', async () => result, value => outputs.push(value));
    assert.equal(outputs.length, 1); assert.equal(outputs[0], result, 'The whole original value, including metadata, stays intact');
  }
});

test('native spawn acknowledgement adapter fixes one exact Host batch without an authored slot',async()=>{
  const batch='a'.repeat(64),descriptor=workflowNativeSpawnBatchAdapterDescriptor(batch);
  assert.equal(descriptor.slot,'none');assert.equal(descriptor.tool_name,'workflow_native_spawned_batch');
  for(let index=0;index<2;index++)await execute(descriptor.code,'workflow_native_spawned_batch',async args=>
    assert.deepEqual(JSON.parse(JSON.stringify(args)),{batch_id:batch}));
  for(const invalid of ['', 'a'.repeat(63), 'g'.repeat(64), undefined])
    assert.throws(()=>workflowNativeSpawnBatchAdapterDescriptor(invalid),{code:'NATIVE_AGENT_BATCH_ID'});
  assert.throws(()=>workflowNativeSpawnBatchAdapterDescriptor(batch,{}),{code:'WORKFLOW_CALL_OPTIONS'});
});

test('ordinary startup adapter never asks a model to transcribe Host pins or initial semantic output',async()=>{
 const args=startArgs(),descriptor=workflowOrdinaryStartupAdapterDescriptor(args);let received;
 await execute(descriptor.code,'workflow_start',async value=>{received=JSON.parse(JSON.stringify(value));});
 assert.match(received.launch_key,/^[0-9a-f-]{36}$/);
 const key=received.launch_key;delete received.launch_key;
 assert.deepEqual(received,args);assert.equal(descriptor.slot,'none');
 await execute(descriptor.code,'workflow_start',async value=>assert.equal(value.launch_key,key));
 const next=workflowOrdinaryStartupAdapterDescriptor(args);
 await execute(next.code,'workflow_start',async value=>assert.notEqual(value.launch_key,key));
 for(const field of ['revision_hash','startup_inputs_sha256','initial_output']){
   assert(!descriptor.code.includes(field));
   assert.throws(()=>workflowOrdinaryStartupAdapterDescriptor({...args,[field]:'value'}),{code:'WORKFLOW_STARTUP_FIELDS'});
 }
 const schema=workflowToolDefinitions().find(t=>t.name==='workflow_start').inputSchema;
 assert.match(schema.properties.initial_output.description,/Host startup contract adapter/);
 assert.match(schema.properties.initial_output.description,/revision_hash/);
 assert(!schema.properties.initial_output.description.includes('submit only this'));
});

test('startup adapter fixes business fields and pin while preserving all semantic keys as data',async()=>{
 const business={...startArgs(),inputs:{task:'Use `text` and ${literal}.'}},pin='a'.repeat(64);
 const descriptor=workflowStartupAdapterDescriptor(business,pin);
 const output=JSON.parse('{"__proto__":{"marker":"data"},"revision_hash":"semantic value","mode":"video"}');
 let received;
 await execute(descriptor.code_prefix+canonicalJSON(output)+descriptor.code_suffix,'workflow_start',async args=>{received=args;});
 const key=received.launch_key;assert.match(key,/^[0-9a-f-]{36}$/);
 assert.deepEqual(JSON.parse(JSON.stringify(received)),{...business,revision_hash:pin,launch_key:key,initial_output:output});
 await execute(descriptor.code_prefix+canonicalJSON(output)+descriptor.code_suffix,'workflow_start',async value=>assert.equal(value.launch_key,key));
 assert.equal(Object.getPrototypeOf(received.initial_output).marker,undefined);
 assert.equal(descriptor.slot,'initial_output');assert.match(descriptor.code_prefix,/yield_time_ms":3600000/);
 assert.throws(()=>workflowStartupAdapterDescriptor({...business,revision_hash:pin},pin),{code:'WORKFLOW_STARTUP_FIELDS'});
 assert.throws(()=>workflowStartupAdapterDescriptor({...business,initial_output:{}},pin),{code:'WORKFLOW_STARTUP_FIELDS'});
 assert.throws(()=>workflowStartupAdapterDescriptor(business,'invalid'),{code:'WORKFLOW_STARTUP_REVISION'});
});

test('registered model-facing tools describe typed direct calls without executable wait hints', async () => {
  for (const protocolVersion of ['2025-11-25', '2026-07-28']) {
    const listed = await handleRpc({ jsonrpc: '2.0', id: 'preset', method: 'tools/list',
      params: { _meta: { 'io.modelcontextprotocol/protocolVersion': protocolVersion } } },{env:{WORKFLOW_MCP_TRANSPORT:'direct_mcp'}});
    assert.equal(listed.error, undefined);
    for (const name of WORKFLOW_LONG_CALL_TOOLS) {
      const tool = listed.result.tools.find(tool => tool.name === name);
      assert.ok(tool, name);
      assert(tool.description.includes(WORKFLOW_EXECUTION_TOOL_NAMESPACE + name));
      assert.match(tool.description, /typed business arguments/);
      assert.doesNotMatch(tool.description, /functions\.exec|functions\.wait|@exec|yield_time_ms|code_prefix|code_suffix/);
      for (const field of ['yield_time_ms', 'max_output_tokens', 'wait_seconds']) {
        assert.equal(Object.hasOwn(tool.inputSchema.properties, field), false, 'only business arguments enter MCP');
      }
    }
    assert.equal(listed.result.tools.find(tool => tool.name === 'workflow_get').description.includes('// @exec:'), false);
  }
});

test('plugin registration binds compatible management and seven direct tools to the same portable launcher and inner timeout', async () => {
  const { mcpServers } = JSON.parse(await readFile(new URL('../../.mcp.json', import.meta.url), 'utf8'));
  const management = mcpServers['codex-agents-workflow'], execution = mcpServers['caw-execution'];
  assert.deepEqual(Object.keys(mcpServers), ['codex-agents-workflow', 'caw-execution']);
  assert.equal(management.disabled_tools, undefined);
  assert.deepEqual(execution.enabled_tools, WORKFLOW_DIRECT_TOOLS);
  assert.deepEqual(execution.omit_tools_from, ['code_mode', 'deferred']);
  assert.equal(management.env.WORKFLOW_MCP_TRANSPORT,'code_mode');
  assert.equal(execution.env.WORKFLOW_MCP_TRANSPORT,'direct_mcp');
  const { env: managementEnv, ...managementLauncher } = management;
  const { env: executionEnv, enabled_tools, omit_tools_from, ...executionLauncher } = execution;
  assert.deepEqual(executionLauncher, managementLauncher);
  const {WORKFLOW_MCP_TRANSPORT:managementTransport,...managementInherited}=managementEnv,
    {WORKFLOW_MCP_TRANSPORT:executionTransport,...executionInherited}=executionEnv;
  assert.deepEqual(executionInherited,managementInherited);
  assert.equal(execution.tool_timeout_sec, 3660); assert.equal(execution.enabled, true);
  const listed = workflowToolDefinitions().map(tool => tool.name);
  assert.deepEqual(listed.filter(name => execution.enabled_tools.includes(name)).sort(), [...WORKFLOW_DIRECT_TOOLS].sort());
  assert(listed.length > WORKFLOW_DIRECT_TOOLS.length);
  assert(WORKFLOW_DIRECT_TOOLS.every(name=>(WORKFLOW_EXECUTION_TOOL_NAMESPACE+name).length<=64));
});

test('untagged management keeps its fixed legacy contract while direct scope is explicit and unknown scope fails',async()=>{
 assert.equal(workflowMcpTransport({}),'code_mode');
 for(const transport of ['code_mode','direct_mcp']){
  const env={WORKFLOW_MCP_TRANSPORT:transport},service=new WorkflowService({configPath:'transport-contract-fixture.json',defaultConfigPath:DEFAULT_CONFIG_PATH,env});
  const expected=transport==='code_mode'?'functions_exec':'direct_mcp';
  for(const name of WORKFLOW_LONG_CALL_TOOLS){
   const value=service.modelResult({next_action:name,...(name==='workflow_native_spawned_batch'?{batch_id:'a'.repeat(64)}:{})});
   assert.equal(value.invocation_adapter.kind,expected,name);
  }
  const nested=service.modelResult({next_action_args:{continuation:{next_action:'workflow_native_next'}}});
  assert.equal(nested.next_action_args.continuation.invocation_adapter.kind,expected);
  env.WORKFLOW_MCP_TRANSPORT=transport==='code_mode'?'direct_mcp':'code_mode';
  assert.equal(service.invocationTransport,transport,'The service contract is immutable after launcher selection');
  assert.throws(()=>{service.invocationTransport='unknown';},TypeError);
  assert.throws(()=>{service.invocationAdapters={};},TypeError);
 }
 const legacy=new WorkflowService({configPath:'untagged-management-fixture.json',defaultConfigPath:DEFAULT_CONFIG_PATH,env:{}});
 const descriptor=legacy.modelResult({next_action:'workflow_native_next'}).invocation_adapter;
 assert.equal(descriptor.kind,'functions_exec');assert(descriptor.code_suffix.includes('mcp__codex_agents_workflow__workflow_native_next'));
 const listed=await handleRpc({jsonrpc:'2.0',id:'legacy',method:'tools/list'},{env:{}});
 for(const name of WORKFLOW_LONG_CALL_TOOLS){
  const description=listed.result.tools.find(tool=>tool.name===name).description;
  assert(description.includes('// @exec:'));assert(description.includes('3600000'));assert(description.includes('functions.wait'));
  assert(!description.includes('mcp__caw_execution__'));
 }
 for(const transport of ['unknown','',null,1000]){
  const env={WORKFLOW_MCP_TRANSPORT:transport};
  assert.throws(()=>new WorkflowService({configPath:'unused',defaultConfigPath:DEFAULT_CONFIG_PATH,env}),{code:'WORKFLOW_MCP_TRANSPORT'});
  await assert.rejects(handleRpc({jsonrpc:'2.0',id:'unknown',method:'initialize'},{env}),{code:'WORKFLOW_MCP_TRANSPORT'});
 }
});

test('default descriptors expose the exact direct tool and only real business or semantic slots', () => {
  const schemas = new Map(workflowToolDefinitions().map(tool => [tool.name, tool.inputSchema]));
  for (const name of WORKFLOW_LONG_CALL_TOOLS) {
    const descriptor = direct.workflowCallAdapterDescriptor(name), orchestration = name === 'workflow_orchestration_complete';
    assert(descriptor.tool.length <= 64, 'qualified direct tool names must fit the public function-name limit');
    assert.deepEqual(descriptor, { schema_version: 2, kind: 'direct_mcp', tool_name: name,
      tool: WORKFLOW_EXECUTION_TOOL_NAMESPACE + name, arguments: {}, slot: orchestration ? 'output' : 'arguments',
      slot_schema: orchestration ? schemas.get(name).properties.output : schemas.get(name), scope: 'direct_mcp_only' });
    assert.doesNotMatch(JSON.stringify(descriptor), /functions\.exec|functions\.wait|@exec|code_prefix|code_suffix|yield_time_ms|max_output_tokens/);
  }
  assert.throws(() => direct.workflowCallAdapterDescriptor('workflow_get'), { code: 'WORKFLOW_CALL_TOOL' });
  assert.throws(() => direct.workflowCallAdapterDescriptor('workflow_native_next', {}), { code: 'WORKFLOW_CALL_OPTIONS' });
});

test('direct startup and acknowledgement descriptors bind stable Host arguments with an opaque preparation reference', () => {
  const reference = '12345678-1234-4234-8234-123456789abc', batch = 'a'.repeat(64);
  for (const typed of [true, false]) {
    const descriptor = direct.workflowStartupReferenceAdapterDescriptor(reference, typed);
    assert.equal(descriptor.kind, 'direct_mcp'); assert.equal(descriptor.slot, typed ? 'none' : 'initial_output');
    assert.deepEqual(descriptor.arguments, { startup_reference: reference });
    assert.equal(descriptor.tool, WORKFLOW_EXECUTION_TOOL_NAMESPACE + 'workflow_start_prepared');
    for (const field of ['revision_hash', 'startup_inputs_sha256', 'workspace', 'access', 'launch_key', 'code'])
      assert(!Object.hasOwn(descriptor.arguments, field));
  }
  const ack = direct.workflowNativeSpawnBatchAdapterDescriptor(batch);
  assert.equal(ack.slot, 'none'); assert.deepEqual(ack.arguments, { batch_id: batch });
  const ordinary = direct.workflowOrdinaryStartupAdapterDescriptor(startArgs()), { launch_key, ...business } = ordinary.arguments;
  assert.match(launch_key, /^[0-9a-f-]{36}$/); assert.deepEqual(business, startArgs());
  assert.notEqual(direct.workflowOrdinaryStartupAdapterDescriptor(startArgs()).arguments.launch_key, launch_key);
  for (const field of ['revision_hash', 'startup_inputs_sha256', 'initial_output', 'launch_key'])
    assert.throws(() => direct.workflowOrdinaryStartupAdapterDescriptor({ ...startArgs(), [field]: 'replacement' }), { code: 'WORKFLOW_STARTUP_FIELDS' });
  assert.throws(() => direct.workflowStartupReferenceAdapterDescriptor(reference.toUpperCase(), false), { code: 'WORKFLOW_PREPARATION_REFERENCE' });
  assert.throws(() => direct.workflowStartupReferenceAdapterDescriptor(reference, 'typed'), { code: 'WORKFLOW_PREPARATION_FIELDS' });
  assert.throws(() => direct.workflowNativeSpawnBatchAdapterDescriptor('invalid'), { code: 'NATIVE_AGENT_BATCH_ID' });
});

test('typed direct invocation validates unchanged public schemas and preserves hostile JSON as data', () => {
  const output = JSON.parse('{"__proto__":{"marker":"data"},"text":"` ${literal} \\\" ; globalThis.injected=true"}');
  const call = direct.workflowDirectCallInvocation('workflow_orchestration_complete', { output });
  assert.deepEqual(call, { tool: WORKFLOW_EXECUTION_TOOL_NAMESPACE + 'workflow_orchestration_complete', arguments: { output } });
  assert(Object.hasOwn(call.arguments.output, '__proto__')); assert.equal(Object.getPrototypeOf(call.arguments.output).marker, undefined);
  const prepared = direct.workflowPreparedStartupAdapterDescriptor(startArgs(), 'a'.repeat(64), output);
  assert.equal(prepared.slot, 'none'); assert.deepEqual(prepared.arguments.initial_output, output);
  for (const field of ['run_id', 'control_token', 'main_actor', 'native_parent_thread_id', 'yield_time_ms', 'timeout_ms'])
    assert.throws(() => direct.workflowDirectCallInvocation('workflow_start', { ...startArgs(), [field]: 'untrusted' }), { code: 'DATA_INVALID' });
  assert.throws(() => direct.workflowDirectCallInvocation('workflow_start', {}), { code: 'DATA_INVALID' });
  assert.throws(() => direct.workflowDirectCallInvocation('workflow_orchestration_complete', { output: [] }), { code: 'DATA_INVALID' });
  assert.throws(() => direct.workflowDirectCallInvocation('workflow_native_next', {}, { timeout_ms: 1 }), { code: 'WORKFLOW_CALL_OPTIONS' });
  for (const invalid of [undefined, NaN, Infinity, () => {}, 1n])
    assert.throws(() => direct.workflowDirectCallInvocation('workflow_start', { ...startArgs(), inputs: invalid }), { code: 'INVALID_JSON' });
});

test('generated invocations use the actual directive with fixed one-hour execution defaults', () => {
  assert.equal(WORKFLOW_WAIT_SECONDS, 3600);
  assert.equal(WORKFLOW_WAIT_MS, WORKFLOW_WAIT_SECONDS * 1000);
  assert.equal(WORKFLOW_CALL_DEFAULTS.yield_time_ms, WORKFLOW_WAIT_MS);
  assert.deepEqual(WORKFLOW_CALL_DEFAULTS, { yield_time_ms: 3600000, max_output_tokens: 10000 });
  assert.ok(Object.isFrozen(WORKFLOW_CALL_DEFAULTS));
  assert.deepEqual(WORKFLOW_LONG_CALL_TOOLS, ['workflow_start', 'workflow_start_prepared', 'workflow_native_next', 'workflow_native_spawned_batch', 'workflow_native_followed_up', 'workflow_orchestration_complete']);
  for (const name of WORKFLOW_LONG_CALL_TOOLS) {
    const args = name === 'workflow_start_prepared' ? {startup_reference:'12345678-1234-4234-8234-123456789abc'} : name === 'workflow_start' ? startArgs() : name === 'workflow_orchestration_complete' ? { output: { accepted: true } } : {};
    const code = workflowCallInvocation(name, args);
    const [directive] = code.split('\n');
    assert.match(directive, /^\/\/ @exec: /);
    assert.deepEqual(JSON.parse(directive.slice('// @exec: '.length)), WORKFLOW_CALL_DEFAULTS);
    assert.ok(code.includes(`await tools.mcp__codex_agents_workflow__${name}(`));
    const descriptor = workflowCallAdapterDescriptor(name);
    const orchestration = name === 'workflow_orchestration_complete';
    assert.equal(descriptor.slot, orchestration ? 'output' : 'arguments');
    assert.equal(descriptor.scope, 'adopted_invocations_only');
    assert.equal(descriptor.arguments_encoding, orchestration ? 'canonical_semantic_output_json' : 'canonical_business_json');
    assert.equal(descriptor.code_prefix + workflowCallArguments(name, args) + descriptor.code_suffix, code);
  }
});

test('every supported invocation executes its exact named public tool with business data once', async () => {
  for (const name of WORKFLOW_LONG_CALL_TOOLS) {
    const args = name === 'workflow_start_prepared' ? {startup_reference:'12345678-1234-4234-8234-123456789abc'} : name === 'workflow_start' ? { ...startArgs(), inputs: { packet: [1, true, null] } }
      : name === 'workflow_orchestration_complete' ? { output: { value: 'done', run_id: 'semantic data' } } : {};
    let calls = 0, outputs = 0;
    const returned = { tool: name };
    await execute(workflowCallInvocation(name, args), name, async received => {
      calls++; assert.deepEqual(JSON.parse(JSON.stringify(received)), args); return returned;
    }, result => { outputs++; assert.equal(result, returned); });
    assert.equal(calls, 1); assert.equal(outputs, 1);
  }
});

test('the model-facing slot accepts an ordinary JSON value without a second string-escaping layer', async () => {
  for (const name of WORKFLOW_LONG_CALL_TOOLS) {
    const value = name === 'workflow_start_prepared' ? {startup_reference:'12345678-1234-4234-8234-123456789abc'} : name === 'workflow_start' ? startArgs() : name === 'workflow_orchestration_complete'
      ? { conclusion: 'Quoted "text", a backslash \\ and a newline\nremain data.', accepted: true } : {};
    const descriptor = workflowCallAdapterDescriptor(name);
    let received;
    await execute(descriptor.code_prefix + canonicalJSON(value) + descriptor.code_suffix,
      name, async args => { received = JSON.parse(JSON.stringify(args)); });
    assert.deepEqual(received, name === 'workflow_orchestration_complete' ? { output: value } : value);
  }
});

test('orchestration descriptor owns the public output envelope while its only slot is semantic output', async () => {
  const descriptor = workflowCallAdapterDescriptor('workflow_orchestration_complete');
  assert.equal(descriptor.slot, 'output');
  assert.equal(descriptor.arguments_encoding, 'canonical_semantic_output_json');
  const output = { conclusion: 'Semantic decision', result: 'A valid semantic field, not a protocol envelope' };
  let received;
  await execute(descriptor.code_prefix + canonicalJSON(output) + descriptor.code_suffix,
    'workflow_orchestration_complete', async args => { received = args; });
  assert.deepEqual(JSON.parse(JSON.stringify(received)), { output });
  assert.equal(workflowOrchestrationArguments(output), canonicalJSON(output));
  assert.equal(workflowOrchestrationInvocation(output), workflowCallInvocation('workflow_orchestration_complete', { output }));
  assert.equal(descriptor.code_prefix + workflowOrchestrationArguments(output) + descriptor.code_suffix, workflowOrchestrationInvocation(output));
  const schema = workflowToolDefinitions().find(tool => tool.name === 'workflow_orchestration_complete').inputSchema;
  assert.deepEqual(schema.required, ['output']); assert.deepEqual(Object.keys(schema.properties), ['output']);
  for (const value of [null, [], 'text', 1]) assert.throws(() => workflowOrchestrationInvocation(value), { code: 'DATA_INVALID' });
  assert.throws(() => workflowOrchestrationInvocation(output, { yield_time_ms: 10 }), { code: 'WORKFLOW_CALL_OPTIONS' });
  assert.throws(() => workflowOrchestrationArguments(output, { max_output_tokens: 1 }), { code: 'WORKFLOW_CALL_OPTIONS' });
});

test('the ordinary JSON descriptor preserves every own prototype-named data key',async()=>{
  const descriptor=workflowCallAdapterDescriptor('workflow_orchestration_complete');
  for(const value of [null,'neutral string',17,{marker:'neutral data'}]){
    const output=JSON.parse('{"__proto__":null,"nested":{"__proto__":null}}');
    output.__proto__=value;output.nested.__proto__=value;
    let received;
    await execute(descriptor.code_prefix+canonicalJSON(output)+descriptor.code_suffix,
      'workflow_orchestration_complete',async args=>{received=args.output;});
    assert.deepEqual(JSON.parse(JSON.stringify(received)),output);
    assert(Object.hasOwn(received,'__proto__'));assert(Object.hasOwn(received.nested,'__proto__'));
    assert.notEqual(Object.getPrototypeOf(received),null);
    assert.equal(Object.getPrototypeOf(received).marker,undefined);
    assert.equal(Object.getPrototypeOf(received.nested).marker,undefined);
  }
});

test('the descriptor rejects executable expressions without evaluating its data slot',async()=>{
  const descriptor=workflowCallAdapterDescriptor('workflow_orchestration_complete'),context={};let calls=0;
  await assert.rejects(execute(descriptor.code_prefix+'{"value":(globalThis.injected=true)}'+descriptor.code_suffix,
    'workflow_orchestration_complete',async()=>{calls++;},()=>{},context),error=>error.name==='SyntaxError');
  assert.equal(context.injected,undefined);assert.equal(calls,0);
});

test('actual generated VM execution stays pending beyond simulated short observation deadlines and returns once', async () => {
  let release, calls = 0, settled = false;
  const gate = new Promise(resolve => { release = resolve; }), outputs = [], args = startArgs();
  const expectedResult = { status: 'completed', result: { value: 'done' } };
  const pending = execute(workflowCallInvocation('workflow_start', args), 'workflow_start', async received => {
    calls++; assert.deepEqual(JSON.parse(JSON.stringify(received)), args); return gate;
  }, result => outputs.push(result));
  pending.then(() => { settled = true; });
  // This checks promise execution, not elapsed platform time or client yielding.
  for (const simulatedObservationMs of [10001, 30001, 60001]) {
    await setImmediate();
    assert.equal(settled, false, `gate is pending at simulated ${simulatedObservationMs}ms observation`);
    assert.equal(calls, 1); assert.equal(outputs.length, 0);
  }
  release(expectedResult); await pending;
  assert.equal(calls, 1); assert.equal(outputs.length, 1); assert.equal(outputs[0], expectedResult);
});

test('safe argument slot preserves hostile and long JSON data without running injected source', async () => {
  const hostile = '\" ); globalThis.injected = true; // ` ${process.env.SECRET} $() \\ \u2028 \u2029 雪';
  const payload = JSON.parse('{"__proto__":{"danger":"data"},"constructor":"data"}');
  payload.hostile = hostile; payload.long = hostile.repeat(4000); payload.list = [null, false, 0, { text: hostile }];
  const args = { output: payload }, code = workflowCallInvocation('workflow_orchestration_complete', args);
  assert.equal(workflowOrchestrationInvocation(payload), code);
  let received, calls = 0, result; const context = {};
  await execute(code, 'workflow_orchestration_complete', async value => { received = value; calls++; return 'success'; }, value => { result = value; }, context);
  assert.equal(calls, 1); assert.equal(result, 'success');
  assert.deepEqual(JSON.parse(JSON.stringify(received)), JSON.parse(canonicalJSON(args)));
  assert.ok(Object.hasOwn(received.output, '__proto__')); assert.equal(received.output.__proto__.danger, 'data');
  assert.equal(Object.getPrototypeOf(received.output).danger, undefined);
  assert.equal(context.injected, undefined);
  assert.equal(code.includes('\u2028'), false); assert.equal(code.includes('\u2029'), false);
});

test('only real public long-call schemas validate business arguments and options cannot override defaults', () => {
  const schemas = new Map(workflowToolDefinitions().map(tool => [tool.name, tool.inputSchema]));
  for (const name of WORKFLOW_LONG_CALL_TOOLS) assert.ok(schemas.has(name));
  for (const extra of ['run_id', 'node_id', 'attempt_id', 'control_token', 'lease_token', 'request_id', 'main_actor', 'native_parent_thread_id', 'yield_time_ms', 'max_output_tokens', 'timeout_ms', 'options']) {
    assert.throws(() => workflowCallInvocation('workflow_start', { ...startArgs(), [extra]: extra === 'options' ? {} : 1 }), { code: 'DATA_INVALID' });
  }
  for (const name of ['workflow_native_next', 'workflow_native_spawned_batch', 'workflow_native_followed_up']) {
    assert.throws(() => workflowCallInvocation(name, { run_id: 'untrusted' }), { code: 'DATA_INVALID' });
  }
  assert.throws(() => workflowCallInvocation('workflow_start', {}), { code: 'DATA_INVALID' });
  assert.throws(() => workflowCallInvocation('workflow_start', { ...startArgs(), access: 'invalid' }), { code: 'DATA_INVALID' });
  assert.throws(() => workflowCallInvocation('workflow_orchestration_complete', { output: [] }), { code: 'DATA_INVALID' });
  for (const invalid of [null, [], 'json', undefined]) assert.throws(() => workflowCallInvocation('workflow_native_next', invalid));
  for (const invalid of [undefined, NaN, Infinity, () => {}, 1n]) assert.throws(() => workflowCallInvocation('workflow_start', { ...startArgs(), inputs: invalid }), { code: 'INVALID_JSON' });
  for (const name of ['workflow_wait', 'workflow_get', 'workflow_begin_main', 'start', 'workflow_start);text("injected")']) {
    assert.throws(() => workflowCallInvocation(name, {}), { code: 'WORKFLOW_CALL_TOOL' });
  }
  assert.throws(() => workflowCallInvocation('workflow_start', startArgs(), { yield_time_ms: 10 }), { code: 'WORKFLOW_CALL_OPTIONS' });
  assert.throws(() => workflowCallArguments('workflow_start', startArgs(), {}), { code: 'WORKFLOW_CALL_OPTIONS' });
  assert.throws(() => workflowCallAdapterDescriptor('workflow_start', {}), { code: 'WORKFLOW_CALL_OPTIONS' });
});

test('generated execution propagates the exact tool rejection without text or retries', async () => {
  const failure = Object.assign(new Error('Host failure'), { code: 'EXACT_FAILURE' }); let calls = 0, texts = 0;
  await assert.rejects(execute(workflowCallInvocation('workflow_native_next', {}), 'workflow_native_next', async () => { calls++; throw failure; }, () => texts++), error => error === failure);
  assert.equal(calls, 1); assert.equal(texts, 0);
});

test('cell recovery accepts only an exact cell ID with fixed wait parameters', () => {
  assert.deepEqual(workflowCallResume('actual-cell-7'), { tool: 'functions.wait', arguments: { cell_id: 'actual-cell-7', yield_time_ms: 3600000, max_tokens: 10000 } });
  for (const value of [undefined, null, '', ' ', ' cell ', {}, { cell_id: 'actual-cell-7' }, 7, 'cell\n7']) assert.throws(() => workflowCallResume(value), { code: 'WORKFLOW_CALL_CELL' });
  assert.throws(() => workflowCallResume('actual-cell-7', { yield_time_ms: 10, max_tokens: 1 }), { code: 'WORKFLOW_CALL_OPTIONS' });
});
