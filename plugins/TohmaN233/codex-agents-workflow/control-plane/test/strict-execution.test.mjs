import test from 'node:test';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdtemp, mkdir, rm, writeFile, readFile, readdir, chmod, stat } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join, resolve } from 'node:path';
import { buildCodexProfile, cleanupCodexProfile, isolatedEnvironment, pinObservedModel, profileSettings } from '../lib/execution/codex-profile-builder.mjs';
import { createSkillPolicy, skillPathKey } from '../lib/execution/codex-skill-policy.mjs';
import { createCodexSession as createCodexSessionImpl, createStrictSession } from '../lib/execution/codex-session.mjs';
import { createManagedNativeSession as createManagedNativeSessionImpl } from '../lib/execution/managed-native-session.mjs';
import { digest } from '../lib/workflow-revisions.mjs';
import { processIdentity } from '../lib/execution/codex-process-ownership.mjs';
import { WorkflowRuntime } from '../lib/workflow-runtime.mjs';
import {OWNED_MCP_NAMESPACE} from '../lib/execution/owned-tool-mcp.mjs';
import {runHostCommand} from '../lib/execution/codex-command-runner.mjs';
import {persistCodexCommandAudits} from '../lib/execution/codex-result-evidence.mjs';

const testMetadata=async({model})=>({slug:model,tool_mode:'code_mode_only',base_instructions:'Unchanged normal instructions',input_modalities:['text','image'],supports_parallel_tool_calls:true,truncation_policy:{mode:'tokens',limit:10000}});
// Accept the emitted JSON literals and TOML inline table subset while keeping
// quoted command and namespace text intact.
const fixtureToml=raw=>JSON.parse(raw.replace(/"(?:\\.|[^"\\])*"|[A-Za-z_][\w-]*\s*(?==)|=/g,token=>
 token.startsWith('"')?token:token==='='?':':JSON.stringify(token.trim())));
function nativeConfigurationFixture(launch){
 const config={mcp_servers:{ordinary:{command:'ordinary-fixture',args:['ordinary'],enabled:false}}};
 for(const value of launch.overrides??[]){
  const assignment=value.indexOf('='),keys=value.slice(0,assignment).split('.');
  if(!['mcp_servers','features'].includes(keys[0]))continue;
  let target=config;for(const key of keys.slice(0,-1))target=target[key]??={};
  target[keys.at(-1)]=fixtureToml(value.slice(assignment+1));
 }
 if(config.mcp_servers[OWNED_MCP_NAMESPACE])config.mcp_servers[OWNED_MCP_NAMESPACE].enabled=true;
 return config;
}
function nativeConfigurationClientOptions(options){
 const originalFactory=options.clientFactory;
 return {...options,clientFactory:(binary,launch)=>{
  const client=originalFactory(binary,launch),originalCall=client.call.bind(client);
  client.call=async(method,args)=>method==='config/read'
   ?{config:await (options.configurationFixtureReader??nativeConfigurationFixture)(launch,args)}:originalCall(method,args);
  return client;
 }};
}
const createCodexSession=options=>createCodexSessionImpl({toolOutputConfigurationReader:async()=>({}),...nativeConfigurationClientOptions(options),dynamicToolFormat:'untagged_function',modelMetadataReader:testMetadata});
const createManagedNativeSession=options=>createManagedNativeSessionImpl({toolOutputConfigurationReader:async()=>({}),...nativeConfigurationClientOptions(options),dynamicToolFormat:'untagged_function',modelMetadataReader:testMetadata});
async function ownedToolCall(launch,params){
 const binding=launch.overrides.find(value=>/\.env\.CODEX_WORKFLOW_TOOL_ENDPOINT=/.test(value));
 assert(binding,'Native code-mode sessions must use the owned MCP broker transport');
  assert(launch.overrides.includes('features.code_mode_host=true'),'Inherited native code mode must activate the actual bundled host');
 const response=await fetch(JSON.parse(binding.slice(binding.indexOf('=')+1)),{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({method:'tools/call',params:{name:params.tool,arguments:params.arguments}})});
 assert.equal(response.status,200);return response.json();
}

const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };

test('rejected native command retains its precise bounded diagnostic before effects',async t=>{
 const root=await mkdtemp(join(tmpdir(),'command-rejection-diagnostic-'));let session,commandEffects=0;const observed=[];
 t.after(async()=>{await session?.close();await rm(root,{recursive:true,force:true});});
 const binary=join(root,'binary'),home=join(root,'home');await writeFile(binary,'fixture');await mkdir(home);
 session=await createCodexSession({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'diagnostic-model',effort:'high',access:'read_only',env:{CODEX_HOME:home},
  skillPolicy:{implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},onEvent:async event=>observed.push(event),
  clientFactory:(_binary,launch)=>{const client=lifecycleClient(root,'diagnostic-model','high'),call=client.call.bind(client);
   client.call=async(method,args)=>{
    if(method==='command/exec'){commandEffects++;assert.fail('Invalid command must fail before effects');}
    if(method==='thread/start')return {model:'diagnostic-model',modelProvider:'openai',sandbox:{type:'readOnly'},thread:{id:'diagnostic-thread'},instructionSources:[]};
    if(method==='turn/start'){
     await ownedToolCall(launch,{threadId:'diagnostic-thread',tool:'run_workspace_program',arguments:{program:process.execPath,args:['-e',''],yield_time_ms:1000},callId:'rejected-call'});
     client.events.push({method:'item/completed',params:{threadId:'diagnostic-thread',turnId:'diagnostic-turn',item:{type:'agentMessage',phase:'final_answer',text:'{"done":true}'}}});
     return {turn:{id:'diagnostic-turn'}};
    }return call(method,args);
   };
   client.waitFor=async()=>({method:'turn/completed',params:{threadId:'diagnostic-thread',turn:{id:'diagnostic-turn',status:'completed'}}});return client;
  }});
 await session.turn('neutral rejection fixture');assert.equal(commandEffects,0);
 const rejected=observed.find(e=>e.method==='workflow/command'&&e.phase==='rejected');assert.equal(rejected.error_code,'CODEX_COMMAND_ARGUMENTS');
 assert.match(rejected.diagnostic,/Foreground yield_time_ms must be 10000\.\.30000/);assert(rejected.diagnostic.length<=1000);
});

for(const native of [true,false])test(`${native?'native MCP':'dynamic tool'} completed command persists genuine terminal settlement in original session and artifact projection`,async t=>{
  const root=await mkdtemp(join(tmpdir(),'session-command-diagnostics-'));let session;
  t.after(async()=>{await session?.close();await rm(root,{recursive:true,force:true});});
  const binary=join(root,'binary'),home=join(root,'home');await writeFile(binary,'fixture');await mkdir(home);
  const ready=deferred(),release=deferred();
  const options={parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'diagnostic-model',effort:'high',access:'read_only',env:{CODEX_HOME:home},
    dynamicToolFormat:'untagged_function',toolOutputConfigurationReader:async()=>({}),
    modelMetadataReader:async()=>({...await testMetadata({model:'diagnostic-model'}),tool_mode:native?'code_mode_only':'function'}),
    skillPolicy:{implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    onEvent:async event=>{if(event.method==='workflow/command'&&event.phase==='completed'){ready.resolve();await release.promise;}},
    clientFactory:(_binary,launch)=>{
      const client=lifecycleClient(root,'diagnostic-model','high'),call=client.call.bind(client);
      client.call=async(method,args)=>{
        if(method==='command/exec'){
          const spec=JSON.parse(await readFile(args.command.at(-1),'utf8'));
          const receipt=await runHostCommand({...spec,argv:[process.execPath,'-e',"process.stdout.write('retained tail')"]});
          return {exitCode:receipt.exit_code,stdout:JSON.stringify(receipt),stderr:''};
        }
        if(method==='thread/start')return {model:'diagnostic-model',modelProvider:'openai',sandbox:{type:'readOnly'},thread:{id:'diagnostic-thread'},instructionSources:[]};
        if(method==='turn/start'){
          const params={threadId:'diagnostic-thread',tool:'run_workspace_command',arguments:{cmd:'fixture'},callId:'diagnostic-call'};
          if(native)await ownedToolCall(launch,params);else await launch.onToolCall(params);
          client.events.push({method:'item/completed',params:{threadId:'diagnostic-thread',turnId:'diagnostic-turn',item:{type:'agentMessage',phase:'final_answer',text:'{"done":true}'}}});
          return {turn:{id:'diagnostic-turn'}};
        }
        return call(method,args);
      };
      client.waitFor=async()=>({method:'turn/completed',params:{threadId:'diagnostic-thread',turn:{id:'diagnostic-turn',status:'completed'}}});return client;
    }};
  session=await createCodexSessionImpl(nativeConfigurationClientOptions(options));
  const turning=session.turn('neutral diagnostic fixture');await ready.promise;release.resolve();
  const result=await turning;
  assert.equal(result.command_audit[0].diagnostics.runner.status,'complete');
  assert.equal(result.command_audit[0].diagnostics.parent.settlement,'fulfilled');
  assert(result.command_audit[0].diagnostics.parent.settlement_ms>=result.command_audit[0].diagnostics.parent.observation_end_ms);
  const receipt=JSON.parse(await readFile(join(session.profile.receipt_home,'attempt.json'),'utf8'));
  const retained=JSON.parse(await readFile(receipt.command_audit_path,'utf8'));
  assert.deepEqual(retained.command_audit,result.command_audit);
  let artifactBytes;
  await persistCodexCommandAudits({runs:{saveArtifact:async(_runId,_label,bytes)=>{artifactBytes=bytes;return {artifact:'neutral-audit',sha256:digest(bytes),bytes:bytes.length};}}},'neutral-run','neutral-audit',[{identity:{thread_id:'diagnostic-thread',turn_id:'diagnostic-turn'},result}]);
  assert.deepEqual(JSON.parse(artifactBytes).records[0].command_audit[0].diagnostics,retained.command_audit[0].diagnostics);
});

const tokenTotals = (input, output = 10) => ({ inputTokens: input, cachedInputTokens: Math.floor(input / 2), outputTokens: output, reasoningOutputTokens: output / 2 });
const tokenUpdate = (total, last = tokenTotals(100), threadId = 'usage-thread', turnId = 'usage-1') => ({ method: 'thread/tokenUsage/updated', params: { threadId, turnId, tokenUsage: { last, ...(total === undefined ? {} : { total }) } } });
async function usageSessionFixture(t, factory, scriptedTurns, { strictSession = false, rawObservation, rawNotifications = [],
  rawAfterAck = [], ordinaryAfterAck = [], turnStatuses = [], turnErrors = [], onEventHook } = {}) {
  let turns = 0;
  const observed = [];
  const threadArguments = [];
  const makeClient = (cwd, launch = {}) => {
    const client = lifecycleClient(cwd, strictSession ? 'synthetic-model' : 'usage-model', strictSession ? 'low' : 'high');
    const originalCall = client.call.bind(client);
    client.call = async (method, args) => {
      if (method === 'thread/start') { threadArguments.push(args); return { model: strictSession ? 'synthetic-model' : 'usage-model', modelProvider: 'openai', sandbox: { type: 'readOnly' }, thread: { id: 'usage-thread' }, instructionSources: [] }; }
      if (method === 'turn/start') {
        const id = `usage-${++turns}`;
        if (launch.rawObservation?.supported) for (const event of rawNotifications[turns - 1] ?? []) await launch.onEvent(event);
        client.events.push(...scriptedTurns[turns - 1]);
        client.events.push({ method: 'item/completed', params: { threadId: 'usage-thread', turnId: id, item: { type: 'agentMessage', phase: 'final_answer', text: 'done' } } });
        return { turn: { id } };
      }
      return originalCall(method, args);
    };
    client.waitFor = async () => {
      if (launch.rawObservation?.supported) for (const event of rawAfterAck[turns - 1] ?? []) await launch.onEvent(event);
      for (const event of ordinaryAfterAck[turns - 1] ?? []) { client.events.push(event); await launch.onEvent?.(event); }
      if (turnErrors[turns - 1]) throw turnErrors[turns - 1];
      return { method: 'turn/completed', params: { threadId: 'usage-thread', turn: { id: `usage-${turns}`, status: turnStatuses[turns - 1] ?? 'completed' } } };
    };
    return client;
  };
  if (strictSession) {
    const session = await lifecycleSessionFixture(t, (_binary, options) => makeClient(options.cwd), { hostExecutionOnly: true, onEvent: event => observed.push(event) });
    return { session, observed };
  }
  const root = await mkdtemp(join(tmpdir(), 'codex-turn-usage-'));
  let session;
  t.after(async () => { await session?.close(); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const binary = join(root, 'binary'), home = join(root, 'home');
  await writeFile(binary, 'fixture'); await mkdir(home);
  session = await factory({ parent: root, binary, expectedBinaryHash: digest('fixture'), cwd: root,
    model: 'usage-model', effort: 'high', access: 'read_only', maxTurns: scriptedTurns.length, env: { CODEX_HOME: home },
    rawObservation, clientFactory: (_binary, launch) => makeClient(root, launch), onEvent: async event => { observed.push(event); await onEventHook?.(event); },
    skillPolicy: { implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] } });
  return { session, observed, threadArguments };
}

for (const [label, factory] of [['normal', createCodexSession], ['managed', createManagedNativeSession]]) {
  const rawItem = (type, id, extra = {}) => ({ method: 'rawResponseItem/completed', params: {
    threadId: 'usage-thread', turnId: 'usage-1', item: { type, id, ...extra } } });
  const summaryOf = f => f.observed.filter(event => event.method === 'workflow/rawObservation' && event.status === 'turn_summary');
  test(`${label} native catalog observation carries only static references and descriptor counts through exact duplicate call correlation`,async t=>{
    const input='/* ALL_TOOLS tools.web__run */ const text="tools.exec_command"; // secret_source_identifier',
      descriptors=JSON.stringify([{name:'secret_descriptor_name',description:'secret_descriptor_description'},{name:'other_name',description:''}]);
    const call=rawItem('function_call','function-item',{call_id:'shared-call',name:'exec',arguments:input,
      input_observation:{status:'known',lexical_references:['tools.secret_forged']}}),
      output=rawItem('function_call_output',null,{call_id:'shared-call',output:descriptors,output_observation:{status:'known',descriptor_count:999}});
    const f=await usageSessionFixture(t,factory,[[tokenUpdate(tokenTotals(200,20))]],{rawObservation:{supported:true},
      rawNotifications:[[call,call,rawItem('custom_tool_call','custom-item',{call_id:'shared-call',name:'exec',input:'const secret_custom_identifier="xALL_TOOLS";'})]],
      rawAfterAck:[[output,output,rawItem('custom_tool_call_output',null,{call_id:'shared-call',output:'Script completed\n'+descriptors})]]});
    const result=await f.session.turn('catalog fixture'),event=summaryOf(f)[0],summary=JSON.parse(event.diagnostic),shapes=summary.tool_shapes;
    assert.equal(result.usage.input_tokens,200);assert.equal(shapes.call_count,2);assert.equal(shapes.output_count,2);assert.equal(shapes.calls.length,2);
    assert.equal(shapes.detail_complete,true);assert.equal(shapes.inspection_limit_bytes,65536);
    assert.equal(shapes.observation_basis,'whole_string_lexical_references;strict_tool_descriptor_array');
    const declared=shapes.calls.find(item=>item.type==='function_call'),custom=shapes.calls.find(item=>item.type==='custom_tool_call');
    assert.equal(declared.call_id,'shared-call');assert.deepEqual(declared.input_observation,{status:'known',lexical_references:['ALL_TOOLS','tools.web__run','tools.exec_command']});
    assert.deepEqual(declared.output_observation,{status:'known',structural_kind:'tool_descriptor_array',descriptor_count:2});
    assert.equal(declared.input_bytes,Buffer.byteLength(input));assert.equal(declared.output_bytes,Buffer.byteLength(descriptors));
    assert.deepEqual(custom.input_observation,{status:'known',lexical_references:[]});assert.deepEqual(custom.output_observation,{status:'unknown'});
    assert(Buffer.byteLength(event.diagnostic)<=4000);
    const receipt=await readFile(join(f.session.profile.receipt_home,'attempt.json'),'utf8');
    assert.deepEqual(JSON.parse(receipt).raw_observation_summary.tool_shapes,shapes);
    for(const value of [receipt,JSON.stringify(f.observed)]){assert(!value.includes('secret_'));assert(!value.includes('descriptor_description'));assert(!value.includes('Script completed'));}
  });
  test(`${label} native lexical observations never move to another turn or become proof of tool execution`,async t=>{
    const output=rawItem('custom_tool_call_output',null,{call_id:'shared-call',output:JSON.stringify([{name:'secret_descriptor_name',description:'secret_description'}])});output.params.turnId='usage-2';
    const f=await usageSessionFixture(t,factory,[[tokenUpdate(tokenTotals(200,20))],[tokenUpdate(tokenTotals(300,30),tokenTotals(100),'usage-thread','usage-2')]],
      {rawObservation:{supported:true},rawNotifications:[[rawItem('custom_tool_call','call-first',{call_id:'shared-call',name:'exec',input:'"ALL_TOOLS tools.web__run tools.exec_command"'})],[output]]});
    await f.session.turn('first');await f.session.continueTurn('second');const summaries=summaryOf(f).map(event=>JSON.parse(event.diagnostic));
    assert.deepEqual(summaries[0].tool_shapes.calls[0].input_observation.lexical_references,['ALL_TOOLS','tools.web__run','tools.exec_command']);
    assert.equal(summaries[0].item_type_counts.web_search_call,undefined);assert.equal(summaries[0].ordinary_tools.find(item=>item.type==='webSearch').completed_count,0);
    const next=summaries[1].tool_shapes.calls[0];assert.equal(next.call_seen,false);assert.equal(next.input_observation,undefined);assert.equal(next.name,null);
    assert.deepEqual(next.output_observation,{status:'known',structural_kind:'tool_descriptor_array',descriptor_count:1});
    assert(!JSON.stringify(f.observed).includes('secret_'));
  });
  test(`${label} nine native custom shapes correlate exact outputs alongside three MCP and web completions without retaining code or output`, async t => {
    const input = 'secret-code-输入', output = 'secret-discovery-output'.repeat(1000);
    const ordinary = ['mcpToolCall', 'webSearch'].flatMap(type => Array.from({ length: 3 }, (_, index) => ({ method: 'item/completed', params: {
      threadId: 'usage-thread', turnId: 'usage-1', item: { type, id: `${type}-${index}` } } })));
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))]], { rawObservation: { supported: true },
      rawNotifications: [Array.from({ length: 9 }, (_, index) => rawItem('custom_tool_call', `native-${index}`, { call_id: `call-${index}`, name: 'exec', input }))],
      rawAfterAck: [Array.from({ length: 9 }, (_, index) => rawItem('custom_tool_call_output', null, { call_id: `call-${index}`, output }))],
      ordinaryAfterAck: [ordinary] });
    const result = await f.session.turn('shape fixture'), summaryEvent = summaryOf(f)[0], summary = JSON.parse(summaryEvent.diagnostic), shapes = summary.tool_shapes;
    assert.equal(shapes.call_count, 9); assert.equal(shapes.output_count, 9); assert(shapes.calls.length > 0 && shapes.calls.length <= 9);
    assert.equal(shapes.known_input_bytes, 9 * Buffer.byteLength(input)); assert.equal(shapes.known_output_bytes, 9 * Buffer.byteLength(output));
    assert.equal(shapes.unknown_input_count, 0); assert.equal(shapes.unknown_output_count, 0);
    assert.equal(shapes.identity_complete, true); assert.equal(shapes.detail_complete, shapes.calls.length === 9);
    assert.equal(shapes.unreported_call_count, 9 - shapes.calls.length);
    for (const call of shapes.calls) {
      assert.equal(call.name, 'exec'); assert.equal(call.name_source, 'call'); assert.equal(call.output_seen, true);
      assert.equal(call.output_kind, 'string'); assert(call.last_ms >= call.first_ms);
    }
    for (const type of ['mcpToolCall', 'webSearch']) {
      const observed = summary.ordinary_tools.find(item => item.type === type);
      assert.equal(observed.completed_count, 3); assert(Number.isSafeInteger(observed.first_ms)); assert(observed.last_ms >= observed.first_ms);
      assert.equal(result.item_types.filter(item => item === type).length, 3);
    }
    assert.equal(result.usage.input_tokens, 200); assert.equal(summaryOf(f).length, 1);
    assert(Buffer.byteLength(summaryEvent.diagnostic) <= 4000);
    const receipt = await readFile(join(f.session.profile.receipt_home, 'attempt.json'), 'utf8');
    assert.deepEqual(JSON.parse(receipt).raw_observation_summary.tool_shapes, shapes);
    // Exercise the actual existing journal metadata validator/authorization and
    // event retention without creating a business Run or retaining a payload.
    const attempt = { id: 'attempt', status: 'running', lease_hash: digest('lease') };
    const state = { control_hash: digest('control'), nodes: { work: { active_attempt_id: 'attempt', attempts: [attempt] } } };
    const journal = new WorkflowRuntime({runRoot:join(f.session.profile.receipt_home,'offline-journal')});
    const pins={root:{provenance:{kind:'fixture'}}},record={state,pins,sequence:0,events:[]};
    const mutate=async (_run,_kind,update)=>{await update(state,pins,record);return {sequence:1};};
    journal.runs={read:async()=>record,mutate,mutateNativeJournal:mutate};
    await journal.recordExecutorEvent('offline-shape', { node_id: 'work', attempt_id: 'attempt', lease_token: 'lease', control_token: 'control',
      event: { kind: 'codex_event', metadata: summaryEvent } });
    for (const retained of [receipt, JSON.stringify(f.observed), JSON.stringify(attempt.executor_events)]) {
      assert(!retained.includes(input)); assert(!retained.includes('secret-discovery-output'));
    }
  });
  test(`${label} exact call correlation deduplicates nullable items and safely reports constructor names and unknown optional fields`, async t => {
    const call = rawItem('custom_tool_call', null, { call_id: 'custom', name: '__proto__', input: 'é' });
    const output = rawItem('custom_tool_call_output', null, { call_id: 'custom', output: [{ type: 'input_text', text: 'secret-body' }] });
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))]], { rawObservation: { supported: true },
      rawNotifications: [[call, call, rawItem('function_call', 'function', { call_id: 'function', name: 'constructor' }),
        rawItem('function_call', 'unknown-call', { call_id: 'unknown', name: 'Bearer secret-name' })]],
      rawAfterAck: [[output, output, rawItem('function_call_output', 'unknown-output', { call_id: 'unknown', output: { secret: 'secret-body' } }),
        rawItem('function_call_output', 'unattributed-output', { output: 'secret-body', name: 'must_not_guess_a_call' })]] });
    await f.session.turn('unknown fixture');
    const shapes = JSON.parse(summaryOf(f)[0].diagnostic).tool_shapes;
    assert.equal(shapes.call_count, 3); assert.equal(shapes.output_count, 2);
    assert.equal(shapes.known_input_bytes, 2); assert.equal(shapes.unknown_input_count, 2); assert.equal(shapes.unknown_output_count, 1);
    const custom = shapes.calls.find(item => item.call_id === 'custom');
    assert.equal(custom.name, '__proto__'); assert.equal(custom.output_kind, 'content_items');
    assert.equal(custom.output_bytes, Buffer.byteLength(JSON.stringify([{ type: 'input_text', text: 'secret-body' }])));
    assert.equal(shapes.calls.find(item => item.call_id === 'function').name, 'constructor');
    assert.equal(shapes.calls.find(item => item.call_id === 'unknown').name, null);
    assert.equal(shapes.unattributed_notifications, 1); assert(!JSON.stringify(f.observed).includes('secret-'));
  });
  test(`${label} native shape identity and journal detail saturation stay explicitly incomplete without limiting a valid task`, async t => {
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))]], { rawObservation: { supported: true },
      rawAfterAck: [Array.from({ length: 129 }, (_, index) => rawItem('custom_tool_call', `item-${index}`, {
        call_id: `${index}-` + 'x'.repeat(250), name: 'x'.repeat(128), input: 'secret-body' }))] });
    assert.equal((await f.session.turn('saturation')).usage.input_tokens, 200);
    const event = summaryOf(f)[0], summary = JSON.parse(event.diagnostic), shapes = summary.tool_shapes;
    assert.equal(shapes.call_count, 128); assert.equal(shapes.identity_complete, false); assert.equal(shapes.unretained_notifications, 1);
    assert.equal(shapes.detail_complete, false); assert.equal(shapes.unreported_call_count, 128 - shapes.calls.length);
    assert.equal(summary.identity_census_complete, true); assert(Buffer.byteLength(event.diagnostic) <= 4000);
    assert.equal(shapes.known_input_bytes, 128 * Buffer.byteLength('secret-body'));
    assert(!JSON.stringify(f.observed).includes('secret-body'));
  });
  test(`${label} native shape correlation never borrows a name or input from another owned turn`, async t => {
    const output = rawItem('custom_tool_call_output', null, { call_id: 'same-call', output: 'secret-output' });
    output.params.turnId = 'usage-2';
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))],
      [tokenUpdate(tokenTotals(300, 30), tokenTotals(100), 'usage-thread', 'usage-2')]], { rawObservation: { supported: true },
      rawNotifications: [[rawItem('custom_tool_call', 'first-item', { call_id: 'same-call', name: 'exec', input: 'secret-code' })], [output]] });
    await f.session.turn('first'); await f.session.continueTurn('correction');
    const summaries = summaryOf(f).map(event => JSON.parse(event.diagnostic));
    assert.equal(summaries[0].tool_shapes.calls[0].name, 'exec');
    const next = summaries[1].tool_shapes.calls[0];
    assert.equal(next.name, null); assert.equal(next.name_source, null); assert.equal(next.input_bytes, null); assert.equal(next.call_seen, false);
    assert.equal(next.output_seen, true); assert.equal(next.output_bytes, Buffer.byteLength('secret-output'));
    assert(!JSON.stringify(f.observed).includes('secret-'));
  });
  test(`${label} raw census retains fixed non-search type counts once per turn with exact deduplication and no inferred native names or bodies`, async t => {
    const secret = 'secret-census-body', response = { method: 'rawResponse/completed', params: {
      threadId: 'usage-thread', turnId: 'usage-1', responseId: 'response-one', metadata: secret } };
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20)),
      { method: 'item/completed', params: { threadId: 'usage-thread', turnId: 'usage-1', item: { type: 'dynamicToolCall' } } }]], {
      rawObservation: { supported: true }, rawNotifications: [[rawItem('function_call', 'function-one', { name: secret, arguments: secret }),
        rawItem('function_call', 'function-one'), rawItem('reasoning', 'reason-one', { text: secret }), response]],
      rawAfterAck: [[rawItem('local_shell_call', 'shell-one', { output: secret }), response,
        rawItem('web_search_call', 'web-one', { query: secret }), rawItem('message', null, { content: secret })]] });
    const result = await f.session.turn('census');
    assert.equal(result.usage.input_tokens, 200);
    assert.equal(result.item_types.filter(type => type === 'dynamicToolCall').length, 1);
    assert.equal(summaryOf(f).length, 1);
    const summary = JSON.parse(summaryOf(f)[0].diagnostic);
    assert.deepEqual(summary.item_type_counts, { function_call: 1, reasoning: 1, local_shell_call: 1, web_search_call: 1 });
    assert.equal(summary.response_completion_count, 1); assert.equal(summary.unattributed_item_notifications, 1);
    assert.equal(summary.unobserved_item_notifications, 0);
    assert(Number.isSafeInteger(summary.first_observation_ms) && summary.last_observation_ms >= summary.first_observation_ms);
    assert.equal(summaryOf(f)[0].thread_id, 'usage-thread'); assert.equal(summaryOf(f)[0].turn_id, 'usage-1');
    const receipt = await readFile(join(f.session.profile.receipt_home, 'attempt.json'), 'utf8');
    assert.deepEqual(JSON.parse(receipt).raw_observation_summary, { thread_id: 'usage-thread', turn_id: 'usage-1', ...summary });
    for (const retained of [receipt, JSON.stringify(f.observed), JSON.stringify(result)]) assert(!retained.includes(secret));
  });
  test(`${label} failed turn retains valid raw census without replacing its original failure or replaying an observer`, async t => {
    const original = Object.assign(new Error('original wait failure'), { code: 'FIXTURE_WAIT_FAILURE' });
    const f = await usageSessionFixture(t, factory, [[]], { rawObservation: { supported: true },
      rawNotifications: [[rawItem('function_call', 'valid-call', { call_id: 'failed-call', name: 'exec', arguments: 'secret-failed-turn' })]], turnErrors: [original] });
    await assert.rejects(f.session.turn('failure'), error => error === original);
    assert.equal(summaryOf(f).length, 1);
    assert.deepEqual(JSON.parse(summaryOf(f)[0].diagnostic).item_type_counts, { function_call: 1 });
    const receipt = JSON.parse(await readFile(join(f.session.profile.receipt_home, 'attempt.json'), 'utf8'));
    assert.equal(receipt.error_code, 'FIXTURE_WAIT_FAILURE'); assert.equal(receipt.status, 'failed');
    assert.equal(receipt.raw_observation_summary.tool_shapes.calls[0].input_bytes, Buffer.byteLength('secret-failed-turn'));
    assert(!JSON.stringify(receipt).includes('secret-failed-turn'));
  });
  test(`${label} failed raw summary observer preserves both errors and runs its callback once`, async t => {
    const original = new Error('original'), observer = new Error('observer'); let callbacks = 0;
    const f = await usageSessionFixture(t, factory, [[]], { rawObservation: { supported: true }, turnErrors: [original],
      onEventHook: event => { if (event.status === 'turn_summary') { callbacks++; throw observer; } } });
    await assert.rejects(f.session.turn('failure'), error => error instanceof AggregateError
      && error.errors[0] === original && error.errors[1] === observer);
    assert.equal(callbacks, 1);
  });
  for (const [name, rejected, code] of [
    ['malformed supported item', rawItem('tool_search_call', 'bad-search', { execution: 'secret-invalid-execution' }), 'CODEX_RAW_NOTIFICATION_INVALID'],
    ['conflicting exact identity', rawItem('function_call', 'valid-reason'), 'CODEX_RAW_ITEM_CONFLICT'],
    ['wrong turn', { method: 'rawResponse/completed', params: { threadId: 'usage-thread', turnId: 'wrong-turn', responseId: 'response' } }, 'CODEX_RAW_IDENTITY'],
  ]) test(`${label} ${name} fails visibly and failed census includes only validated items`, async t => {
    const f = await usageSessionFixture(t, factory, [[]], { rawObservation: { supported: true },
      rawNotifications: [[rawItem('reasoning', 'valid-reason')]], rawAfterAck: [[rejected]] });
    await assert.rejects(f.session.turn('reject'), { code });
    assert.equal(summaryOf(f).length, 1);
    assert.deepEqual(JSON.parse(summaryOf(f)[0].diagnostic).item_type_counts, { reasoning: 1 });
    assert(!JSON.stringify(f.observed).includes('secret-invalid-execution'));
  });
  test(`${label} exact identity census saturation is explicitly incomplete and preserves valid execution and usage`, async t => {
    const response = { method: 'rawResponse/completed', params: { threadId: 'usage-thread', turnId: 'usage-1', responseId: 'unretained-response' } };
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))]], { rawObservation: { supported: true },
      rawAfterAck: [[...Array.from({ length: 4097 }, (_, index) => rawItem('function_call', `call-${index}`)),
        rawItem('function_call', 'call-0'), rawItem('function_call', 'call-4096'), response, response]] });
    const result = await f.session.turn('bounded census');
    const summary = JSON.parse(summaryOf(f)[0].diagnostic);
    assert.equal(result.output, 'done'); assert.equal(result.usage.input_tokens, 200);
    assert.equal(summary.item_type_counts.function_call, 4096);
    assert.equal(summary.identity_census_complete, false); assert.equal(summary.identity_limit, 4096);
    assert.equal(summary.unretained_item_notifications, 2); assert.equal(summary.unretained_response_notifications, 2);
    assert.equal(summary.response_completion_count, 0, 'Unretained notifications cannot be promoted to unique counts');
    assert(summaryOf(f)[0].diagnostic.length < 4096);
  });
  test(`${label} qualifies optional raw observation and binds compact tool search to the exact continuing turn without charging raw usage`, async t => {
    const item = turnId => ({ method: 'rawResponseItem/completed', params: { threadId: 'usage-thread', turnId,
      item: { type: 'tool_search_call', id: `search-${turnId}`, execution: 'server', status: 'completed',
        arguments: { query: 'secret-search' }, output: 'secret-search' } } });
    const response = { method: 'rawResponse/completed', params: { threadId: 'usage-thread', turnId: 'usage-1', responseId: 'response-1',
      usage: { ...tokenTotals(9999, 100), totalTokens: 10099 }, usageMetadata: { metadata: 'secret-search' } } };
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))],
      [tokenUpdate(tokenTotals(300, 30), tokenTotals(100), 'usage-thread', 'usage-2')]], {
      rawObservation: { supported: true, diagnostic: 'schema-qualified fixture' },
      rawNotifications: [[item('usage-1'), response], [item('usage-2')]] });
    const first = await f.session.turn('first'), next = await f.session.continueTurn('correction');
    assert.equal(f.threadArguments.length, 1);
    assert.equal(f.threadArguments[0].experimentalRawEvents, true);
    assert.deepEqual(f.observed.filter(event => event.method === 'workflow/toolSearch'), ['usage-1', 'usage-2'].map(turn_id => ({
      method: 'workflow/toolSearch', thread_id: 'usage-thread', turn_id, item_type: 'tool_search_call',
      item_id: `search-${turn_id}`, status: 'completed', diagnostic: 'execution=server' })));
    assert(!JSON.stringify(f.observed).includes('secret-search'));
    assert.equal(first.usage.input_tokens, 200); assert.equal(next.usage.input_tokens, 100);
    assert(f.observed.some(event => event.method === 'workflow/rawObservation' && event.status === 'supported'));
    assert.deepEqual(summaryOf(f).map(event => JSON.parse(event.diagnostic).item_type_counts), [{ tool_search_call: 1 }, { tool_search_call: 1 }]);
    assert.deepEqual(summaryOf(f).map(event => event.turn_id), ['usage-1', 'usage-2']);
  });
  test(`${label} unsupported optional raw capability leaves ordinary thread arguments and usage unchanged`, async t => {
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))]], {
      rawObservation: { supported: false, diagnostic: 'declared request field unavailable' } });
    assert.equal((await f.session.turn('ordinary')).usage.input_tokens, 200);
    assert.equal(Object.hasOwn(f.threadArguments[0], 'experimentalRawEvents'), false);
    assert(f.observed.some(event => event.method === 'workflow/rawObservation' && event.status === 'unsupported'));
    assert.equal(f.observed.filter(event => event.method === 'workflow/toolSearch').length, 0);
    assert.deepEqual(JSON.parse(summaryOf(f)[0].diagnostic), { supported: false });
  });
  test(`${label} unknown raw types and nullable search IDs preserve healthy execution with bounded unobserved diagnostics`, async t => {
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))]], {
      rawObservation: { supported: true }, rawNotifications: [[
        { method: 'rawResponseItem/completed', params: { threadId: 'usage-thread', turnId: 'usage-1',
          item: { type: 'future-secret-type', content: 'secret-body', id: { secret: true } } } },
        { method: 'rawResponseItem/completed', params: { threadId: 'usage-thread', turnId: 'usage-1',
          item: { type: 'tool_search_call', id: null, execution: 'server', arguments: 'secret-body' } } },
      ]] });
    assert.equal((await f.session.turn('ordinary')).usage.input_tokens, 200);
    assert.equal(f.observed.filter(event => event.method === 'workflow/toolSearch').length, 0);
    for (const status of ['unobserved_item', 'unattributed_item']) assert(f.observed.some(event => event.method === 'workflow/rawObservation'
      && event.status === status && event.thread_id === 'usage-thread' && event.turn_id === 'usage-1'));
    assert(!JSON.stringify(f.observed).includes('secret'));
  });
  test(`${label} pre-ack raw queue overflow fails visibly without journaling search evidence or retaining bodies`, async t => {
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))]], {
      rawObservation: { supported: true }, rawNotifications: [Array.from({ length: 257 }, (_, index) => ({
        method: 'rawResponseItem/completed', params: { threadId: 'usage-thread', turnId: 'usage-1',
          item: { type: 'tool_search_call', id: `search-${index}`, execution: 'server', status: 'completed',
            arguments: { query: 'secret-overflow-body' }, content: 'secret-overflow-body' } } }))] });
    await assert.rejects(f.session.turn('overflow fixture'), { code: 'CODEX_RAW_PENDING_LIMIT' });
    assert.equal(f.observed.filter(event => event.method === 'workflow/toolSearch').length, 0);
    for (const retained of [f.observed, f.session.client.events]) assert(!JSON.stringify(retained).includes('secret-overflow-body'));
    assert.equal(summaryOf(f).length, 0, 'No turn identity was acknowledged; queued observations remain unattributed');
  });
  for (const [threadId, turnId] of [['other-thread', 'usage-1'], ['usage-thread', 'other-turn']])
    test(`${label} refuses raw observation for wrong identity ${threadId}/${turnId}`, async t => {
      const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))]], {
        rawObservation: { supported: true }, rawNotifications: [[{ method: 'rawResponseItem/completed', params: {
          threadId, turnId, item: { type: 'tool_search_call', id: 'search', execution: 'server', arguments: {} } } }]] });
      await assert.rejects(f.session.turn('identity fixture'), { code: 'CODEX_RAW_IDENTITY' });
      assert.equal(f.observed.filter(event => event.method === 'workflow/toolSearch').length, 0);
    });
}

for (const [label, factory] of [['normal', createCodexSession], ['managed', createManagedNativeSession]]) {
  test(`${label} turn meters all responses and identical last values without double-counting duplicate notifications`, async t => {
    const first = tokenUpdate(tokenTotals(100));
    const second = tokenUpdate(tokenTotals(200, 20));
    const f = await usageSessionFixture(t, factory, [[first, structuredClone(first),
      { method: 'item/completed', params: { threadId: 'usage-thread', turnId: 'usage-1', item: { type: 'dynamicToolCall' } } },
      tokenUpdate(tokenTotals(9999), tokenTotals(9999), 'another-thread'), second,
      { method: 'item/completed', params: { threadId: 'usage-thread', turnId: 'usage-1', item: { type: 'dynamicToolCall' } } }, structuredClone(second)]]);
    const result = await f.session.turn('meter fixture');
    assert.equal(result.usage.available, true);
    assert.equal(result.usage.input_tokens, 200);
    assert.equal(result.usage.output_tokens, 20);
    assert.equal(result.usage.reasoning_output_tokens, 10);
    assert.equal(result.usage.cached_input_tokens, 100);
    assert(f.observed.some(event => event.method === 'workflow/turnUsage' && event.usage_basis === 'thread_total_delta'
      && event.usage_baseline_input_tokens === 0 && event.usage_total_input_tokens === 200));
  });
  test(`${label} correction subtracts the same thread's prior turn total`, async t => {
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))],
      [tokenUpdate(tokenTotals(300, 30), tokenTotals(100), 'usage-thread', 'usage-2'), tokenUpdate(tokenTotals(400, 40), tokenTotals(100), 'usage-thread', 'usage-2')]]);
    const first = await f.session.turn('first');
    const correction = await f.session.continueTurn('correction');
    assert.equal(first.usage.input_tokens, 200);
    assert.equal(correction.usage.input_tokens, 200);
    assert.equal(correction.usage.output_tokens, 20);
    assert.equal(correction.usage.reasoning_output_tokens, 10);
  });
  for (const [name, updates, reason] of [
    ['missing total', [tokenUpdate(undefined)], 'total_missing'],
    ['partially missing total', [tokenUpdate(tokenTotals(100)), tokenUpdate(undefined)], 'total_missing'],
    ['malformed total', [tokenUpdate({ ...tokenTotals(100), inputTokens: '100' })], 'total_invalid'],
    ['total reset', [tokenUpdate(tokenTotals(200, 20)), tokenUpdate(tokenTotals(100))], 'total_decreased'],
    ['same-thread other turn', [tokenUpdate(tokenTotals(100), tokenTotals(100), 'usage-thread', 'other-turn'), tokenUpdate(tokenTotals(200, 20))], 'turn_scope_conflict'],
  ]) test(`${label} reports ${name} as unknown whole-turn metering`, async t => {
    const f = await usageSessionFixture(t, factory, [updates]);
    const result = await f.session.turn('unknown fixture');
    assert.equal(result.usage.available, false);
    assert.equal(result.usage.input_tokens, undefined, 'Last response must never masquerade as whole-turn usage');
    assert(f.observed.some(event => event.method === 'workflow/turnUsage' && event.usage_available === false && event.usage_unavailable_reason === reason));
  });
  test(`${label} cannot meter a correction without an exact preceding thread total`, async t => {
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(undefined)], [tokenUpdate(tokenTotals(400, 40), tokenTotals(100), 'usage-thread', 'usage-2')]]);
    await f.session.turn('unknown first');
    const result = await f.session.continueTurn('correction');
    assert.equal(result.usage.available, false);
    assert(f.observed.some(event => event.method === 'workflow/turnUsage' && event.usage_unavailable_reason === 'baseline_missing'));
  });
  test(`${label} binds a correction baseline to the exact preceding owned turn`, async t => {
    const f = await usageSessionFixture(t, factory, [[tokenUpdate(tokenTotals(200, 20))], [tokenUpdate(tokenTotals(400, 40), tokenTotals(100), 'usage-thread', 'usage-2')]]);
    await f.session.turn('first');
    f.session.client.events.push(tokenUpdate(tokenTotals(300, 30), tokenTotals(100), 'usage-thread', 'unowned-turn'));
    const result = await f.session.continueTurn('correction');
    assert.equal(result.usage.available, false);
    assert(f.observed.some(event => event.method === 'workflow/turnUsage' && event.turn_id === 'usage-2' && event.usage_unavailable_reason === 'baseline_missing'));
  });
}

test('Strict session uses the same whole-turn total delta', async t => {
  const f = await usageSessionFixture(t, null, [[tokenUpdate(tokenTotals(100)), tokenUpdate(tokenTotals(200, 20))]], { strictSession: true });
  t.after(() => f.session.close());
  const result = await f.session.turn('strict usage fixture');
  assert.equal(result.usage.input_tokens, 200);
  assert.equal(result.usage.reasoning_output_tokens, 10);
});

for(const [label,factory] of [['normal',createCodexSession],['managed',createManagedNativeSession]])
test(`${label} completed model preserves audit before bounded pending-command close fails`,async t=>{
  const root=await mkdtemp(join(tmpdir(),'completed-pending-command-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const binary=join(root,'binary'),home=join(root,'home');await writeFile(binary,'fixture');await mkdir(home);
  const observed=[],owners=[];
  const session=await factory({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'usage-model',effort:'high',
    access:'read_only',env:{CODEX_HOME:home},commandShutdownGraceMs:10,
    skillPolicy:{implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    clientFactory:(_binary,launch)=>{
      let rejectCommand,closed=false;
      const client=lifecycleClient(root,'usage-model','high');owners.push(client);
      const original=client.call.bind(client);
      client.close=async()=>{if(closed)return;closed=true;if(rejectCommand)rejectCommand(Object.assign(new Error('exact owned shutdown'),{code:'OWNED_STOP'}));};
      client.call=async(method,args)=>{
        if(method==='command/exec'){
          const spec=JSON.parse(await readFile(args.command.at(-1),'utf8'));await writeFile(spec.output_path,'captured tail');
          return new Promise((_,reject)=>{rejectCommand=reject;});
        }
        if(method==='thread/start')return {model:'usage-model',modelProvider:'openai',sandbox:{type:'readOnly'},thread:{id:'exact-thread'},instructionSources:[]};
        if(method==='turn/start'){
          await ownedToolCall(launch,{threadId:'exact-thread',tool:'run_workspace_command',arguments:{cmd:'fixture',yield_time_ms:0},callId:'exact-command-call'});
          client.events.push({method:'item/completed',params:{threadId:'exact-thread',turnId:'exact-turn',item:{type:'commandExecution',status:'completed',exitCode:7,command:'fixture-done',aggregatedOutput:'normal tail'}}},
            {method:'item/completed',params:{threadId:'exact-thread',turnId:'exact-turn',item:{type:'agentMessage',phase:'final_answer',text:'{"done":true}'}}});
          return {turn:{id:'exact-turn'}};
        }
        return original(method,args);
      };
      client.waitFor=async()=>({method:'turn/completed',params:{threadId:'exact-thread',turn:{id:'exact-turn',status:'completed'}}});
      return client;
    },onEvent:event=>observed.push(event)});
  const result=await session.turn('complete fixture');assert.equal(result.output,'{"done":true}');
  const receiptPath=join(session.profile.receipt_home,'attempt.json');
  const receipt=JSON.parse(await readFile(receiptPath,'utf8'));assert.equal(receipt.status,'completed');assert.equal(receipt.pending_command_ids.length,1);
  const audit=JSON.parse(await readFile(receipt.command_audit_path,'utf8'));
  assert.equal(audit.command_audit[0].exit_code,7);assert.equal(audit.command_audit[0].output,'normal tail');
  await assert.rejects(session.close(),{code:'CODEX_COMMAND_SHUTDOWN_FORCED'});
  const failed=JSON.parse(await readFile(receiptPath,'utf8'));assert.equal(failed.close_phase,'failed');assert.equal(failed.closed_at,undefined);
  assert(observed.some(event=>event.method==='workflow/command'&&event.phase==='close_forced'&&event.pending_process_ids[0]===receipt.pending_command_ids[0]));
  const toolEvent=observed.find(event=>event.method==='item/tool/call'&&event.call_id.startsWith('owned-mcp-')&&event.tool_name==='run_workspace_command'&&/^[a-f0-9]{64}$/.test(event.arguments_sha256));
  assert(toolEvent);
  assert(observed.some(event=>event.method==='workflow/command'&&event.call_id===toolEvent.call_id&&event.process_id===receipt.pending_command_ids[0]&&event.tool==='run_workspace_command'));
  assert(observed.some(event=>event.method==='workflow/sessionShutdown'&&event.phase==='failed'));
  await session.close();
});

test('Strict completed-turn client close has a finite confirmation bound',async t=>{
  let released=false;
  const session=await lifecycleSessionFixture(t,(_binary,options)=>lifecycleClient(options.cwd,'synthetic-model','low',
    {close:()=>released?Promise.resolve():new Promise(()=>{})}),{hostExecutionOnly:true,clientShutdownTimeoutMs:10});
  await assert.rejects(session.close(),{code:'CODEX_SESSION_SHUTDOWN_TIMEOUT'});
  released=true;await session.close();
});

test('Strict close notification rejection cannot skip owned cleanup or discard recovery evidence',async t=>{
  let closes=0,cleaned=0,rejectEvent=true;
  const session=await lifecycleSessionFixture(t,(_binary,options)=>lifecycleClient(options.cwd,'synthetic-model','low',{close:()=>{closes++;}}),
    {hostExecutionOnly:true,cleanupCodexProfileImpl:async()=>{cleaned++;},onEvent:event=>{
      if(rejectEvent&&event.method==='workflow/sessionShutdown')throw Object.assign(new Error('authority rotated'),{code:'RUN_AUTHORITY'});
    }});
  await assert.rejects(session.close());assert.equal(closes,1);assert.equal(cleaned,0);
  rejectEvent=false;await session.close();assert.equal(cleaned,1);
});

test('normal and managed nodes use ephemeral sessions with user Codex configuration, native items and exact attempt receipts', async t => {
  const root = await mkdtemp(join(tmpdir(), 'normal-codex-'));
  const ownedSessions=[];
  t.after(async()=>{
    const settled=await Promise.allSettled(ownedSessions.map(session=>session.close()));
    await rm(root,{recursive:true,force:true});
    const errors=settled.filter(item=>item.status==='rejected').map(item=>item.reason);
    if(errors.length)throw new AggregateError(errors,'Fixture session cleanup failed');
  });
  const binary = join(root, 'binary'), userHome = join(root, 'user-codex'), cwd = join(root, 'workspace');
  await writeFile(binary, 'fixture'); await mkdir(userHome); await mkdir(cwd);
  const skill = join(root, 'skill', 'SKILL.md'); await mkdir(join(root, 'skill'));
  const skillText = '---\nname: relevant\n---\nRelevant instructions'; await writeFile(skill, skillText);
  for (const factory of [createCodexSession, createManagedNativeSession]) {
    const ambient = factory === createManagedNativeSession;
    let launch, closed = 0; const metadata = [];
    const client = {
      events: [], initialized() {}, async close() { closed++; },
      async call(method, params) {
        if (method === 'initialize') return {};
        if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
        if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
        if (method === 'skills/list') return { data: [{ cwd, errors: [], skills: [
          { name: 'relevant', path: skill, enabled: true },
          { name: 'unrelated', path: join(root, 'unrelated', 'SKILL.md'), enabled: true },
        ] }] };
        if (method === 'thread/start') {
          assert.equal(params.cwd, cwd); assert.equal(params.model, 'fixture-model');
          assert.equal(Object.hasOwn(params.config,'tool_output_token_limit'),false);
          const catalog=JSON.parse(await readFile(params.config.model_catalog_json,'utf8'));
          assert.equal(catalog.models[0].tool_mode,'code_mode_only');
          assert.deepEqual(catalog.models[0].input_modalities,['text','image']);
          assert.equal(catalog.models[0].base_instructions,'Unchanged normal instructions');
          assert.equal(params.modelProvider, 'openai');
          assert.equal(params.sandbox, 'workspace-write'); assert.equal(params.approvalPolicy, undefined);
          assert.equal(params.baseInstructions, undefined); assert.equal(params.environments, undefined);
          assert.deepEqual(params.config.skills.config, [
            { path: skill, enabled: false }, { path: join(root, 'unrelated', 'SKILL.md'), enabled: false },
          ]); assert.equal(params.ephemeral, true);
          assert.deepEqual(params.dynamicTools,[]);
          return { model: 'fixture-model', modelProvider: 'openai', sandbox: { type: 'workspaceWrite' },
            thread: { id: 'thread-1' }, instructionSources: [{ kind: 'project' }] };
        }
        if (method === 'turn/start') {
          assert.equal(params.effort, 'high');
          assert.deepEqual(params.input[0], { type: 'text', text: 'Do the node' });
          assert.equal(params.input[1].type, 'skill'); assert.equal(params.input[1].name, 'relevant');
          assert.notEqual(params.input[1].path, skill);
          assert.equal(await readFile(params.input[1].path, 'utf8'), skillText);
          assert.equal(await readFile(join(resolve(params.input[1].path, '..'), 'references', 'detail.txt'), 'utf8'), 'PINNED_REFERENCE');
          this.events.push({ method: 'item/completed', params: { threadId: 'thread-1', turnId: 'turn-1', item: { type: 'agentMessage', phase: 'commentary', text: 'Working' } } });
          this.events.push({ method: 'item/completed', params: { threadId: 'thread-1', turnId: 'other-turn', item: { type: 'agentMessage', phase: 'final_answer', text: 'wrong turn' } } });
          this.events.push({ method: 'item/completed', params: { threadId: 'thread-1', turnId: 'turn-1', item: { type: 'commandExecution',id:'native-command-item',processId:'native-process',durationMs:42, status: 'completed', exitCode: 0, command: 'pwd', cwd, aggregatedOutput: cwd } } });
          this.events.push({ method: 'item/completed', params: { threadId: 'thread-1', turnId: 'turn-1', item: { type: 'agentMessage', phase: 'final_answer', text: '{"ok":true}' } } });
          return { turn: { id: 'turn-1' } };
        }
        assert.fail(`Unexpected call ${method}`);
      },
      async waitFor() { return { method: 'turn/completed', params: { threadId: 'thread-1', turn: { id: 'turn-1', status: 'completed' } } }; },
    };
    const session = await factory({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
      cwd, model: 'fixture-model', effort: 'high', access: 'bounded_write', allowedPaths:['.'], env: { CODEX_HOME: userHome, PATH: 'fixture' },
      hostAuth: {}, skillPolicy: { implicit: 'deny', ambient_allow: ambient ? [skill] : [], shadowed_skill_paths: [] },
      owner: { run_id: 'run-1', node_id: 'node-1', attempt_id: 'attempt-1' },
      allowedSkills: [{ source_path: skill, source_hash: digest(skillText), name: 'relevant',
        files: { 'SKILL.md': skillText, 'references/detail.txt': 'PINNED_REFERENCE' } }],
      toolBroker: { tools: () => [{ name: 'read_workflow_resource' }], call() { assert.fail('No tool call expected'); }, revoke() {}, quiesce: async () => ({ quiescent: true }) },
      clientFactory: (_binary, options) => { launch = options; return client; }, onEvent: event => metadata.push(event) });
    ownedSessions.push(session);
    assert.equal(launch.home, userHome); assert.deepEqual(launch.overrides, []);
    assert.equal(launch.env.CODEX_HOME, userHome);
    if (ambient) await writeFile(skill, 'Changed source after Run pinning');
    else await rm(skill);
    const result = await session.turn('Do the node', { explicit_sources: ambient ? [] : [skill] });
    assert.equal(result.output, '{"ok":true}'); assert.deepEqual(result.item_types, ['agentMessage', 'commandExecution', 'agentMessage']);
    assert.equal(result.command_audit[0].command, 'pwd'); assert.equal(result.audit.instruction_source_count, 1);
    assert.equal(result.command_audit[0].item_id,'native-command-item');assert.equal(result.command_audit[0].process_id,'native-process');assert.equal(result.command_audit[0].duration_ms,42);
    const completedReceipt=JSON.parse(await readFile(join(session.profile.receipt_home,'attempt.json'),'utf8'));
    assert.equal(completedReceipt.status,'completed');assert.equal(completedReceipt.closed_at,undefined);
    assert.deepEqual(completedReceipt.tool_output_delivery,{source:'model_metadata',mode:'tokens',limit:10000,max_result_bytes:10000});
    assert.equal(completedReceipt.tool_interface.execution_tool_mode,'code_mode_only');
    assert.equal(completedReceipt.tool_interface.javascript_aggregation,true);
    const interfaceEvent=metadata.find(event=>event.method==='workflow/toolInterface');
    assert(interfaceEvent,'Tool qualification must survive removal of the ephemeral profile');
    const interfaceEvidence=JSON.parse(interfaceEvent.diagnostic);
    assert.equal(interfaceEvidence.execution_tool_mode,'code_mode_only');
    assert.equal(interfaceEvidence.broker_transport,'native_mcp');
    assert.equal(interfaceEvidence.javascript_aggregation,true);
    assert.equal(interfaceEvidence.source_model_metadata_sha256,completedReceipt.source_model_metadata_sha256);
    assert.equal(interfaceEvidence.tool_catalog_sha256,completedReceipt.tool_catalog_sha256);
    assert.deepEqual(interfaceEvidence.output_delivery,completedReceipt.tool_output_delivery);
    assert(!interfaceEvent.diagnostic.includes('CODEX_WORKFLOW_TOOL_ENDPOINT'));
    const savedAuditBytes=await readFile(completedReceipt.command_audit_path);
    assert.equal(digest(savedAuditBytes),completedReceipt.command_audit_sha256);
    const savedAudit=JSON.parse(savedAuditBytes);
    assert.deepEqual(savedAudit.command_audit,result.command_audit);
    assert.deepEqual(savedAudit.pending_command_ids,[]);
    await session.close(); assert.equal(closed, 2);
    assert(launch.overrides.some(value=>value.startsWith('model_catalog_json=')));
    const receipt = JSON.parse(await readFile(join(session.profile.receipt_home, 'attempt.json'), 'utf8'));
    assert.deepEqual(receipt.owner, { run_id: 'run-1', node_id: 'node-1', attempt_id: 'attempt-1' });
    assert.equal(receipt.user_codex_home, userHome); assert.deepEqual(receipt.thread_ids, ['thread-1']);
    assert.equal(receipt.ephemeral, true);
    assert.deepEqual(receipt.turn_ids, ['turn-1']); assert.equal(typeof receipt.closed_at, 'string');
    if (ambient) assert.equal(await readFile(skill, 'utf8'), 'Changed source after Run pinning');
    assert.equal((await stat(userHome)).isDirectory(), true);
  }
});

test('Main selection uses the owned authenticated discovery client once and its failure closes that client',async t=>{
 const root=await mkdtemp(join(tmpdir(),'main-discovery-selection-'));t.after(()=>rm(root,{recursive:true,force:true}));
 const binary=join(root,'binary'),home=join(root,'home');await writeFile(binary,'fixture');await mkdir(home);
 for(const rejectSelection of [false,true]){
  let launches=0,closes=0,selections=0,discovery;
  const failure=Object.assign(new Error('Exact parent identity mismatch'),{code:'MAIN_MODEL_SESSION_IDENTITY'});
  const options={parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,access:'read_only',env:{CODEX_HOME:home},
   skillPolicy:{implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
   clientFactory:()=>{launches++;discovery=lifecycleClient(root,'resolved-main','high',{close:()=>closes++});return discovery;},
   resolveModelSelection:async client=>{
    selections++;assert.equal(client,discovery);assert.deepEqual(await client.call('account/read'),{account:{type:'chatgpt'},requiresOpenaiAuth:true});
    if(rejectSelection)throw failure;return {model:'resolved-main',effort:'high'};
   }};
  if(rejectSelection)await assert.rejects(createCodexSession(options),error=>error===failure);
  else {const session=await createCodexSession(options);
   const receipt=JSON.parse(await readFile(join(session.profile.receipt_home,'attempt.json')));
   assert.equal(receipt.model,'resolved-main');assert.equal(receipt.effort,'high');await session.close();}
  assert.equal(launches,1);assert.equal(selections,1);assert.equal(closes,1);
 }
});

for(const [label,discoveryConfig,executionMutation,expected,launchCount] of [
 ['enabled collision',{mcp_servers:{[OWNED_MCP_NAMESPACE]:{enabled:true}}},null,'CODEX_MCP_NAMESPACE_COLLISION',1],
 ['disabled collision',{mcp_servers:{[OWNED_MCP_NAMESPACE]:{enabled:false}}},null,'CODEX_MCP_NAMESPACE_COLLISION',1],
 ['missing discovery config',undefined,null,'CODEX_MCP_CONFIG',1],
 ['invalid discovery dictionary',{mcp_servers:[]},null,'CODEX_MCP_CONFIG',1],
 ['missing execution binding',{},config=>delete config.mcp_servers[OWNED_MCP_NAMESPACE],'CODEX_MCP_BINDING',2],
 ['disabled execution binding',{},config=>{config.mcp_servers[OWNED_MCP_NAMESPACE].enabled=false;},'CODEX_MCP_BINDING',2],
 ['substituted execution command',{},config=>{config.mcp_servers[OWNED_MCP_NAMESPACE].command='substituted';},'CODEX_MCP_BINDING',2],
 ['substituted private endpoint',{},config=>{config.mcp_servers[OWNED_MCP_NAMESPACE].env.CODEX_WORKFLOW_TOOL_ENDPOINT='substituted';},'CODEX_MCP_BINDING',2],
 ['missing execution parallel policy',{},config=>delete config.mcp_servers[OWNED_MCP_NAMESPACE].supports_parallel_tool_calls,'CODEX_MCP_BINDING',2],
 ['substituted execution approval policy',{},config=>{config.mcp_servers[OWNED_MCP_NAMESPACE].default_tools_approval_mode='prompt';},'CODEX_MCP_BINDING',2],
 ['missing direct namespace',{},config=>{config.features.code_mode.direct_only_tool_namespaces.pop();},'CODEX_MCP_DIRECT_BINDING',2],
 ['substituted direct namespace',{},config=>{config.features.code_mode.direct_only_tool_namespaces=['foreign'];},'CODEX_MCP_DIRECT_BINDING',2],
])test(`normal owned namespace rejects ${label} before any model submission with injected metadata and budget readers`,async t=>{
 const root=await mkdtemp(join(tmpdir(),'owned-binding-refusal-'));t.after(()=>rm(root,{recursive:true,force:true}));
 const binary=join(root,'binary'),home=join(root,'home');await writeFile(binary,'fixture');await mkdir(home);
 let launches=0,threadStarts=0,turnStarts=0,budgetReads=0,closes=0,privateEndpoint;
 const session=await createCodexSession({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'refusal-model',effort:'high',access:'read_only',env:{CODEX_HOME:home},
  toolOutputConfigurationReader:async()=>{budgetReads++;return {};},skillPolicy:{implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
  configurationFixtureReader:(launch,args)=>{
   assert.deepEqual(args,{cwd:root,includeLayers:false});
   if(!launch.overrides.length)return structuredClone(discoveryConfig);
   const config=nativeConfigurationFixture(launch),ordinary=structuredClone(config.mcp_servers.ordinary);executionMutation?.(config);
   assert.deepEqual(config.mcp_servers.ordinary,ordinary);return config;
  },
  clientFactory:(_binary,launch)=>{
   const endpointBinding=launch.overrides.find(value=>value.includes('.env.CODEX_WORKFLOW_TOOL_ENDPOINT='));if(endpointBinding)privateEndpoint=JSON.parse(endpointBinding.slice(endpointBinding.indexOf('=')+1));
   launches++;const client=lifecycleClient(root,'refusal-model','high',{close:()=>closes++}),call=client.call.bind(client);
   client.call=async(method,args)=>{if(method==='thread/start'){threadStarts++;assert.fail('Configuration refusal must precede thread creation');}if(method==='turn/start'){turnStarts++;assert.fail('Configuration refusal must precede model submission');}return call(method,args);};return client;
  }});
 try{await assert.rejects(session.turn('Neutral refusal fixture'),{code:expected});assert.equal(launches,launchCount);assert.equal(threadStarts,0);assert.equal(turnStarts,0);assert.equal(budgetReads,0);
  assert.equal(closes,launchCount,'Prelaunch refusal must close discovery/execution ownership immediately');
  await assert.rejects(session.turn('Cannot bypass failed preparation'),{code:'CODEX_SESSION_CLOSED'});
  const receipt=JSON.parse(await readFile(join(session.profile.receipt_home,'attempt.json')));assert.equal(receipt.status,'failed');assert.equal(receipt.error_code,expected);assert.equal(typeof receipt.closed_at,'string');
  if(privateEndpoint)await assert.rejects(fetch(privateEndpoint,{method:'POST',body:JSON.stringify({method:'tools/list'})}));
 }
 finally{if(closes<launchCount)await session.close();}assert.equal(closes,launchCount);
});

test('owned binding refusal retains original cause and visible shutdown errors then allows explicit cleanup retry',async t=>{
 const root=await mkdtemp(join(tmpdir(),'owned-binding-cleanup-error-'));t.after(()=>rm(root,{recursive:true,force:true}));
 const binary=join(root,'binary'),home=join(root,'home');await writeFile(binary,'fixture');await mkdir(home);
 let rejectClose=true,launches=0;
 const closeError=Object.assign(new Error('Fixture execution shutdown unconfirmed'),{code:'FIXTURE_SHUTDOWN_UNCONFIRMED'});
 const session=await createCodexSession({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'refusal-model',effort:'high',access:'read_only',env:{CODEX_HOME:home},
  skillPolicy:{implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
  configurationFixtureReader:launch=>{const config=nativeConfigurationFixture(launch);if(launch.overrides.length)delete config.mcp_servers[OWNED_MCP_NAMESPACE];return config;},
  clientFactory:()=>{const index=++launches;return lifecycleClient(root,'refusal-model','high',{close:()=>{if(index===2&&rejectClose)throw closeError;}});}});
 await assert.rejects(session.turn('Neutral cleanup refusal'),error=>error instanceof AggregateError&&error.errors.some(item=>item.code==='CODEX_MCP_BINDING')&&error.errors.includes(closeError));
 await assert.rejects(session.turn('Still fenced'),{code:'CODEX_SESSION_CLOSED'});assert.equal(launches,2);
 const failed=JSON.parse(await readFile(join(session.profile.receipt_home,'attempt.json')));assert.equal(failed.close_phase,'failed');assert.equal(failed.closed_at,undefined);
 rejectClose=false;await session.close();const closed=JSON.parse(await readFile(join(session.profile.receipt_home,'attempt.json')));assert.equal(closed.close_phase,'closed');
});

test('normal metadata and namespace discovery share one fresh config read before execution rereads it',async t=>{
 const root=await mkdtemp(join(tmpdir(),'owned-config-reuse-'));t.after(()=>rm(root,{recursive:true,force:true}));
 const binary=join(root,'binary'),home=join(root,'home');await writeFile(binary,'fixture');await mkdir(home);
 await writeFile(join(home,'models_cache.json'),JSON.stringify({models:[await testMetadata({model:'reuse-model'})]}));
 const reads=[],marker=Error('Qualified thread/start reached');let launches=0;
 const options=nativeConfigurationClientOptions({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'reuse-model',effort:'high',access:'read_only',env:{CODEX_HOME:home},dynamicToolFormat:'untagged_function',
  skillPolicy:{implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
  configurationFixtureReader:(launch,args)=>{reads.push(launch.overrides.length?2:1);assert.deepEqual(args,{cwd:root,includeLayers:false});return nativeConfigurationFixture(launch);},
  clientFactory:()=>{launches++;const client=lifecycleClient(root,'reuse-model','high'),call=client.call.bind(client);client.call=async(method,args)=>{if(method==='thread/start')throw marker;return call(method,args);};return client;}});
 const session=await createCodexSessionImpl(options);
 try{await assert.rejects(session.turn('Neutral reuse fixture'),error=>error===marker);assert.deepEqual(reads,[1,2]);assert.equal(launches,2);}finally{await session.close();}
});

test('normal execution client config is read after reopening and drives lossless command delivery',async t=>{
  const root=await mkdtemp(join(tmpdir(),'execution-budget-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const binary=join(root,'binary'),home=join(root,'home');await writeFile(binary,'fixture');await mkdir(home);
  let launches=0,reads=[],deliveries=[];const text='中文\\\n\t😀'.repeat(200)+'END';
  const session=await createCodexSession({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'budget-model',effort:'high',
    access:'read_only',env:{CODEX_HOME:home},toolOutputConfigurationReader:undefined,
    configurationFixtureReader:launch=>{const processIndex=launch.overrides.length?2:1;reads.push(processIndex);return {...nativeConfigurationFixture(launch),tool_output_token_limit:processIndex===1?4096:512};},
    skillPolicy:{implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    clientFactory:(_binary,launch)=>{
      const processIndex=++launches,client=lifecycleClient(root,'budget-model','high'),original=client.call.bind(client);
      client.call=async(method,args)=>{
        if(method==='thread/start'){
          assert.equal(Object.hasOwn(args.config,'tool_output_token_limit'),false);
          return {model:'budget-model',modelProvider:'openai',sandbox:{type:'readOnly'},thread:{id:'budget-thread'},instructionSources:[]};
        }
        if(method==='command/exec'){
          const spec=JSON.parse(await readFile(args.command.at(-1),'utf8'));await writeFile(spec.output_path,text);
          return {exitCode:0,stdout:JSON.stringify({schema_version:1,exit_code:0,output_bytes:Buffer.byteLength(text)}),stderr:''};
        }
        if(method==='turn/start'){
          let result=await ownedToolCall(launch,{threadId:'budget-thread',tool:'run_workspace_command',arguments:{cmd:'fixture'},callId:'first'}),joined='',round=0;
          while(true){assert(Buffer.byteLength(JSON.stringify(result))<=512);deliveries.push(result);const value=JSON.parse(result.contentItems[0].text);joined+=value.output;
            if(!value.has_more)break;assert(round++<200);result=await ownedToolCall(launch,{threadId:'budget-thread',tool:'continue_workspace_command',arguments:{session_id:value.session_id},callId:'read-'+round});}
          assert.equal(joined,text);client.events.push({method:'item/completed',params:{threadId:'budget-thread',turnId:'budget-turn',item:{type:'agentMessage',phase:'final_answer',text:'{"done":true}'}}});
          return {turn:{id:'budget-turn'}};
        }
        return original(method,args);
      };
      client.waitFor=async()=>({method:'turn/completed',params:{threadId:'budget-thread',turn:{id:'budget-turn',status:'completed'}}});return client;
    }});
  try{assert.equal((await session.turn('Neutral budget fixture')).output,'{"done":true}');
    const receipt=JSON.parse(await readFile(join(session.profile.receipt_home,'attempt.json')));
    assert.deepEqual(reads,[1,2]);assert(deliveries.length>1);assert.equal(receipt.tool_output_delivery.limit,512);assert.equal(receipt.tool_output_delivery.source,'user_config');
  }finally{await session.close();}
});

test('known owned MCP bootstrap failure closes the session before any model turn',async t=>{
  const root=await mkdtemp(join(tmpdir(),'mcp-prelaunch-failure-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const binary=join(root,'binary'),home=join(root,'home');await writeFile(binary,'fixture');await mkdir(home);
  let turnStarts=0,closedClients=0;
  const session=await createCodexSession({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'budget-model',effort:'high',
    access:'read_only',env:{CODEX_HOME:home},skillPolicy:{implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    clientFactory:(_binary,launch)=>{
      const client=lifecycleClient(root,'budget-model','high'),original=client.call.bind(client);
      client.close=async()=>{closedClients++;};
      client.call=async(method,args)=>{
        if(method==='thread/start'){
          const binding=launch.overrides.find(value=>/\.env\.CODEX_WORKFLOW_TOOL_ENDPOINT=/.test(value));
          const response=await fetch(JSON.parse(binding.slice(binding.indexOf('=')+1)),{method:'POST',body:JSON.stringify({method:'tools/call',params:{name:'unregistered',arguments:{}}})});
          assert.equal(response.status,500);
          return {model:'budget-model',modelProvider:'openai',sandbox:{type:'readOnly'},thread:{id:'failed-bootstrap'}};
        }
        if(method==='turn/start'){turnStarts++;assert.fail('A failed transport must not consume a model turn');}
        return original(method,args);
      };return client;
    }});
  const failure=await session.turn('Neutral prelaunch fixture').catch(error=>error);
  assert(failure instanceof AggregateError);
  assert(failure.errors.every(error=>error.code==='CODEX_TOOL_DENIED'));
  assert.equal(turnStarts,0);assert.equal(closedClients,2);
  const receipt=JSON.parse(await readFile(join(session.profile.receipt_home,'attempt.json')));
  assert.deepEqual(receipt.turn_ids,[]);assert.equal(receipt.close_phase,'failed');
  await session.close();
});

test('normal session exposes shutdown failure and permits an exact owned close retry', async t => {
  const root = await mkdtemp(join(tmpdir(), 'normal-close-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), userHome = join(root, 'user-home');
  await writeFile(binary, 'fixture'); await mkdir(userHome);
  let closes = 0;
  const client = { events: [], initialized() {},
    async close() { if (++closes === 1) throw Object.assign(new Error('owned child still active'), { code: 'CHILD_ACTIVE' }); },
    async call(method) {
      if (method === 'initialize') return {};
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
      assert.fail(`Unexpected call ${method}`);
    } };
  const session = await createCodexSession({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
    cwd: root, model: 'fixture-model', effort: 'high', access: 'read_only', env: { CODEX_HOME: userHome }, clientFactory: () => client });
  await assert.rejects(session.close(), { code: 'CHILD_ACTIVE' });
  const firstReceipt = JSON.parse(await readFile(join(session.profile.receipt_home, 'attempt.json'), 'utf8'));
  assert.equal(firstReceipt.closed_at, undefined);
  await session.close();
  const finalReceipt = JSON.parse(await readFile(join(session.profile.receipt_home, 'attempt.json'), 'utf8'));
  assert.equal(closes, 2); assert.equal(typeof finalReceipt.closed_at, 'string');
  assert.equal((await stat(userHome)).isDirectory(), true);
});

for(const fault of ['notification','receipt'])test(`normal cleanup survives ${fault} failure and an explicit close retry recovers`,async t=>{
  const root=await mkdtemp(join(tmpdir(),'normal-close-observation-fault-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const binary=join(root,'binary'),home=join(root,'home');await writeFile(binary,'fixture');await mkdir(home);
  let closes=0,failNotification=fault==='notification';
  const client=lifecycleClient(root,'fixture-model','high',{close:()=>{closes++;}});
  const session=await createCodexSession({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'fixture-model',effort:'high',
    access:'read_only',env:{CODEX_HOME:home},clientFactory:()=>client,
    onEvent:event=>{if(failNotification&&['workflow/sessionShutdown','workflow/command'].includes(event.method))throw Object.assign(new Error('old authority cannot journal'),{code:'RUN_AUTHORITY'});}});
  const receiptPath=join(session.profile.receipt_home,'attempt.json');
  if(fault==='receipt'){await rm(receiptPath);await mkdir(receiptPath);}
  await assert.rejects(session.close());
  assert.equal(closes,1,'an observation error must not skip exact owned cleanup');
  if(fault==='receipt')await rm(receiptPath,{recursive:true});
  failNotification=false;
  await session.close();
  const recovered=JSON.parse(await readFile(receiptPath,'utf8'));assert.equal(recovered.close_phase,'closed');assert.equal(typeof recovered.closed_at,'string');
});

test('normal correction continues the same thread with short input and the exact output schema', async t => {
  const root = await mkdtemp(join(tmpdir(), 'normal-continuation-')); t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), home = join(root, 'home'), cwd = join(root, 'workspace');
  await writeFile(binary, 'fixture'); await mkdir(home); await mkdir(cwd);
  const schema = { type: 'object', properties: { answer: { type: 'string' } }, required: ['answer'], additionalProperties: false };
  let threadStarts = 0, turns = 0, launch;
  const client = { events: [], initialized() {}, async close() {},
    async call(method, args) {
      if (method === 'initialize') return {};
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
      if (method === 'skills/list') return { data: [{ cwd, errors: [], skills: [] }] };
      if (method === 'thread/start') {
        assert.equal(args.ephemeral, true);
        const binding=launch.overrides.find(value=>/\.env\.CODEX_WORKFLOW_TOOL_ENDPOINT=/.test(value));
        assert(binding,'Direct tool schemas must come from the owned MCP catalog');
        const response=await fetch(JSON.parse(binding.slice(binding.indexOf('=')+1)),{method:'POST',
          headers:{'content-type':'application/json'},body:JSON.stringify({method:'tools/list'})});
        assert.equal(response.status,200);
        const catalog=await response.json(),command=catalog.tools.find(tool=>tool.name==='run_workspace_command');
        assert(command);assert.equal(command.inputSchema.type,'object');
        assert.deepEqual(command.inputSchema.properties.cmd,{type:'string'});
        assert.equal(command.inputSchema.additionalProperties,false);
        assert.deepEqual(args.dynamicTools,[]);
        threadStarts++; return { model: 'fixture-model', modelProvider: 'openai', sandbox: { type: 'readOnly' }, thread: { id: 'same-thread' }, instructionSources: [] };
      }
      if (method === 'turn/start') {
        turns++; assert.equal(args.threadId, 'same-thread'); assert.deepEqual(args.outputSchema, schema);
        assert.deepEqual(args.input[0], { type: 'text', text: turns === 1 ? 'Original node task' : 'Correct locations[12]' });
        assert.equal(args.input.length,1);
        assert.doesNotMatch(args.input[0].text,/owned_command_declarations/);
        const id = `turn-${turns}`;
        this.events.push({ method: 'item/completed', params: { threadId: 'same-thread', turnId: id,
          item: { type: 'agentMessage', phase: 'final_answer', text: JSON.stringify({ answer: id }) } } });
        return { turn: { id } };
      }
      assert.fail(`Unexpected call ${method}`);
    },
    async waitFor() { return { method: 'turn/completed', params: { threadId: 'same-thread', turn: { id: `turn-${turns}`, status: 'completed' } } }; },
  };
  const session = await createCodexSession({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
    cwd, model: 'fixture-model', effort: 'high', access: 'read_only', maxTurns: 2,
    env: { CODEX_HOME: home }, clientFactory: (_binary,options) => { launch=options;return client; },
    skillPolicy: { implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] } });
  assert.equal((await session.turn('Original node task', { output_schema: schema })).thread_id, 'same-thread');
  assert.equal((await session.continueTurn('Correct locations[12]', { output_schema: schema })).output, '{"answer":"turn-2"}');
  assert.equal(threadStarts, 1); assert.equal(turns, 2);
  await assert.rejects(session.continueTurn('Third correction', { output_schema: schema }), { code: 'CODEX_SESSION_BUSY' });
  await session.close();
  const receipt = JSON.parse(await readFile(join(session.profile.receipt_home, 'attempt.json'), 'utf8'));
  assert.deepEqual(receipt.thread_ids, ['same-thread']); assert.deepEqual(receipt.turn_ids, ['turn-1', 'turn-2']);
  assert.equal(receipt.ephemeral, true);
});

test('environment API-key mode selects an env-key provider without changing shared account login', async t => {
  const root = await mkdtemp(join(tmpdir(), 'normal-api-key-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), userHome = join(root, 'user-home');
  await writeFile(binary, 'fixture'); await mkdir(userHome);
  const calls = []; let launch;
  const client = { events: [], initialized() {}, async close() {},
    async call(method, params) {
      calls.push(method);
      if (method === 'initialize') return {};
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
      if (method === 'skills/list') return { data: [{ cwd: root, errors: [], skills: [] }] };
      if (method === 'thread/start') {
        assert.equal(params.modelProvider, 'workflow_environment_api_key');
        return { model: 'fixture-model', modelProvider: params.modelProvider, sandbox: { type: 'workspaceWrite' }, thread: { id: 'thread-key' } };
      }
      if (method === 'turn/start') {
        this.events.push({ method: 'item/completed', params: { threadId: 'thread-key', turnId: 'turn-key', item: { type: 'agentMessage', phase: 'final_answer', text: 'done' } } });
        return { turn: { id: 'turn-key' } };
      }
      assert.fail(`Unexpected call ${method}`);
    },
    async waitFor() { return { params: { turn: { id: 'turn-key', status: 'completed' } } }; } };
  const session = await createCodexSession({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
    cwd: root, model: 'fixture-model', effort: 'high', access: 'bounded_write', allowedPaths:['.'], env: { CODEX_HOME: userHome, TASK_API_KEY: 'example-fixture-secret-never-log' },
    authentication: { mode: 'environment_api_key', api_key_env: 'TASK_API_KEY' },
    skillPolicy: { implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] },
    clientFactory: (_binary, options) => { launch = options; return client; } });
  assert.equal(launch.home, userHome); assert(launch.overrides.some(value => value.includes('env_key="TASK_API_KEY"')));
  assert.equal(launch.overrides.some(value => value.includes('fixture-secret')), false);
  assert.deepEqual(await session.login({ apiKeyEnv: 'TASK_API_KEY' }), { authenticated: true, type: 'environment_api_key' });
  const result = await session.turn('Use configured API provider'); assert.equal(result.output, 'done');
  assert.equal(calls.includes('account/login/start'), false); assert.equal(calls.includes('account/read'), false);
  await session.close(); assert.equal((await stat(userHome)).isDirectory(), true);
});

test('implicit allow retains enabled Skills except shadowed sources', async t => {
  const root = await mkdtemp(join(tmpdir(), 'normal-skills-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), userHome = join(root, 'user-home');
  await writeFile(binary, 'fixture'); await mkdir(userHome);
  const paths = ['related', 'other', 'shadowed'].map(name => join(root, name, 'SKILL.md'));
  const marker = new Error('thread/start observed');
  const client = { events: [], initialized() {}, async close() {},
    async call(method, params) {
      if (method === 'initialize') return {};
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
      if (method === 'skills/list') return { data: [{ cwd: root, errors: [], skills: paths.map((path, index) => ({ name: `skill-${index}`, path, enabled: true })) }] };
      if (method === 'thread/start') {
        assert.equal(params.sandbox, 'read-only'); assert.equal(params.approvalPolicy, undefined);
        assert.deepEqual(params.config.skills.config, paths.map((path, index) => ({ path, enabled: index !== 2 })));
        throw marker;
      }
      assert.fail(`Unexpected call ${method}`);
    } };
  const session = await createCodexSession({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
    cwd: root, model: 'fixture-model', effort: 'high', access: 'read_only', env: { CODEX_HOME: userHome },
    skillPolicy: { implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [paths[2]] }, clientFactory: () => client });
  await assert.rejects(session.turn('Read relevant task context'), error => error === marker);
  await session.close();
});

test('normal session fails before a model turn if App Server substitutes its authorized sandbox', async t => {
  await assert.rejects(createCodexSession({ access: undefined }), { code: 'CODEX_ACCESS_MODE' });
  const root = await mkdtemp(join(tmpdir(), 'normal-sandbox-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), userHome = join(root, 'user-home');
  await writeFile(binary, 'fixture'); await mkdir(userHome);
  let turnStarted = false;
  const client = { events: [], initialized() {}, async close() {},
    async call(method, params) {
      if (method === 'initialize') return {};
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
      if (method === 'skills/list') return { data: [{ cwd: root, errors: [], skills: [] }] };
      if (method === 'thread/start') {
        assert.equal(params.sandbox, 'workspace-write'); assert.equal(params.approvalPolicy, undefined);
        return { model: 'fixture-model', modelProvider: 'openai', sandbox: { type: 'readOnly' }, thread: { id: 'wrong-sandbox' } };
      }
      if (method === 'turn/start') turnStarted = true;
      assert.fail(`Unexpected call ${method}`);
    } };
  const session = await createCodexSession({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
    cwd: root, model: 'fixture-model', effort: 'high', access: 'bounded_write', allowedPaths:['.'], env: { CODEX_HOME: userHome },
    skillPolicy: { implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] }, clientFactory: () => client });
  await assert.rejects(session.turn('Write within the assigned workspace'), { code: 'CODEX_SANDBOX_UNCONTROLLED' });
  assert.equal(turnStarted, false);
  await session.close();
});

test('isolated Workflow profile keeps host dynamic-tool transport enabled without ambient code mode', () => {
  const settings = profileSettings({ home: 'C:/fixture', model: 'fixture-model' });
  assert.equal(settings['features.code_mode_host'], true);
  assert.equal(settings['features.code_mode'], false);
  assert.equal(settings['features.shell_tool'], false);
});

async function fixture(t, { profile = true, modelMetadata = true } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'strict-execution-')); const binary = join(root, 'fixture-binary'); await writeFile(binary, 'Synthetic never-executed binary');
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const options = { parent: root, binary, expectedBinaryHash: digest(await readFile(binary)), model: 'synthetic-model', effort: 'low',
    processIdentityImpl: async pid => ({ pid, executable: process.execPath, started: 'deterministic-fixture-parent' }),
    ...(modelMetadata ? { modelMetadata: { slug: 'synthetic-model', supported_reasoning_levels: [{ effort: 'low' }] } } : {}) };
  if (!profile) {
    const home = join(root, 'catalog-fixture'); await mkdir(join(home, 'skills'), { recursive: true });
    return { root, options, profile: { home } };
  }
  return { root, options, profile: await buildCodexProfile(options) };
}

test('Strict profile records deterministic parent evidence and refuses unavailable ownership before creating a profile', async t => {
  const f = await fixture(t);
  const owner = JSON.parse(await readFile(join(f.profile.home, 'owner.json'), 'utf8'));
  assert.deepEqual(owner.parent_identity, await f.options.processIdentityImpl(process.pid));
  await cleanupCodexProfile(f.profile);
  let observedPid;
  await assert.rejects(buildCodexProfile({ ...f.options, processIdentityImpl: async pid => {
    observedPid = pid;
    throw Object.assign(new Error('unqualified platform'), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });
  } }), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });
  assert.equal(observedPid, process.pid);
  assert.deepEqual(await readdir(f.root), ['fixture-binary']);
});

test('real platform process ownership returns stable OS evidence or explicitly refuses unsupported inspection', async () => {
  if (!['win32', 'linux'].includes(process.platform)) {
    await assert.rejects(processIdentity(process.pid), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });
    return;
  }
  const first = await processIdentity(process.pid), second = await processIdentity(process.pid);
  assert.deepEqual(first, second);
  assert.equal(first.pid, process.pid);
  assert.equal(first.executable, resolve(process.execPath));
  assert(first.started.length > 0);
});

test('unqualified platform ownership inspection refuses profile creation before effects', async t => {
  const f = await fixture(t, { profile: false });
  // Exercise the production refusal branch even on a qualified test host.
  const script = `Object.defineProperty(process, 'platform', { value: 'darwin' });
    const assert = (await import('node:assert/strict')).default;
    const { processIdentity } = await import(process.argv[1]);
    const { buildCodexProfile } = await import(process.argv[2]);
    const options = JSON.parse(process.argv[3]);
    await assert.rejects(processIdentity(process.pid), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });
    await assert.rejects(buildCodexProfile(options), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });`;
  await promisify(execFile)(process.execPath, ['--input-type=module', '--eval', script,
    new URL('../lib/execution/codex-process-ownership.mjs', import.meta.url).href,
    new URL('../lib/execution/codex-profile-builder.mjs', import.meta.url).href,
    JSON.stringify(f.options)], { windowsHide: true, timeout: 10000 });
  assert.deepEqual((await readdir(f.root)).sort(), ['catalog-fixture', 'fixture-binary']);
});
const strict = { mode: 'strict', implicit: 'deny', shadowed_skill_paths: [], ambient_allow: [] };
const skillText = '---\nname: allowed\ndescription: Synthetic fixture\n---\nALLOWED_SENTINEL';
function metadataClient(cwd, skills) {
  return { async call(method, args) {
    if (method === 'skills/list') return { data: [{ cwd, errors: [], skills: structuredClone(skills) }] };
    assert.equal(method, 'skills/config/write'); const found = skills.find(skill => skillPathKey(skill.path) === skillPathKey(args.path)); assert(found); found.enabled = args.enabled; return {};
  } };
}

test('Strict profile rejects changed binary and owner token and strips inherited overrides', async t => {
  const f = await fixture(t); const env = isolatedEnvironment({ PATH: 'fixture-path', USERPROFILE: 'fixture-user', CODEX_HOME: 'shared', CODEX_CONFIG: 'untrusted', OPENAI_API_KEY: 'example-sensitive', SOL_CONTROL_DISABLED: '1' }, f.profile.home);
  assert.equal(env.CODEX_HOME, f.profile.home); assert.equal(env.CODEX_CONFIG, undefined); assert.equal(env.OPENAI_API_KEY, undefined); assert.equal(env.PATH, 'fixture-path');
  await writeFile(f.options.binary, 'Changed binary'); await assert.rejects(buildCodexProfile(f.options), { code: 'CODEX_BINARY_CHANGED' });
  await assert.rejects(cleanupCodexProfile({ ...f.profile, owner_token: 'wrong' }), { code: 'PROFILE_OWNER' });
  await cleanupCodexProfile(f.profile);
});

test('isolated profile pins only the authenticated observed model window',async t=>{
  const f=await fixture(t,{modelMetadata:false});
  await writeFile(join(f.profile.home,'models_cache.json'),JSON.stringify({models:[
    {slug:'synthetic-model',context_window:272000,max_context_window:872000,base_instructions:'private cache text'},
    {slug:'other-model',context_window:42000},
  ]}));
  await pinObservedModel(f.profile,{model:'synthetic-model',displayName:'Synthetic',description:'Fixture model',defaultReasoningEffort:'low',inputModalities:['text'],supportedReasoningEfforts:[{reasoningEffort:'low',description:'Fixture effort'}]});
  const pinned=JSON.parse(await readFile(join(f.profile.home,'models.json'),'utf8')).models[0];
  assert.equal(pinned.context_window,272000);
  assert.equal(pinned.max_context_window,872000);
  assert.equal(JSON.stringify(pinned).includes('private cache text'),false);
  await cleanupCodexProfile(f.profile);
});

const observedFixtureModel={model:'synthetic-model',displayName:'Synthetic',description:'Fixture model',defaultReasoningEffort:'low',inputModalities:['text'],supportedReasoningEfforts:[{reasoningEffort:'low',description:'Fixture effort'}]};

test('isolated catalog treats nullable maximum as absent without inventing a window',async t=>{
  const f=await fixture(t,{modelMetadata:false});
  await writeFile(join(f.profile.home,'models_cache.json'),JSON.stringify({models:[{slug:'synthetic-model',context_window:272000,max_context_window:null}]}));
  await pinObservedModel(f.profile,observedFixtureModel);
  const pinned=JSON.parse(await readFile(join(f.profile.home,'models.json'),'utf8')).models[0];
  assert.equal(pinned.context_window,272000);
  assert.equal(Object.hasOwn(pinned,'max_context_window'),false);
  await cleanupCodexProfile(f.profile);
});

for(const [name,models] of [
  ['missing model', [{slug:'other-model',context_window:272000}]],
  ['duplicate model', [{slug:'synthetic-model',context_window:272000},{slug:'synthetic-model',context_window:272000}]],
  ['missing window', [{slug:'synthetic-model'}]],
  ['null window', [{slug:'synthetic-model',context_window:null}]],
  ['invalid window', [{slug:'synthetic-model',context_window:'272000'}]],
  ['invalid maximum', [{slug:'synthetic-model',context_window:272000,max_context_window:32000}]],
]) test(`isolated catalog rejects ${name}`,async t=>{
  const f=await fixture(t,{modelMetadata:false});
  await writeFile(join(f.profile.home,'models_cache.json'),JSON.stringify({models}));
  await assert.rejects(pinObservedModel(f.profile,observedFixtureModel),{code:'CODEX_MODEL_CONTEXT'});
  await cleanupCodexProfile(f.profile);
});

test('Strict catalog enforcement is by path, explicit injection is separate, and policy changes invalidate launch', async t => {
  const f = await fixture(t, { profile: false }); const source = join(f.root, 'source', 'SKILL.md'); const cwd = join(f.root, 'workspace'); await mkdir(cwd);
  const policy = await createSkillPolicy({ home: f.profile.home, cwd, skillPolicy: strict, allowed: [{ source_path: source, source_hash: digest(skillText), name: 'allowed', files: { 'SKILL.md': skillText, 'references/example.txt': 'Owned resource' } }] });
  const input = policy.explicitInputs([source])[0];
  const disallowed = join(cwd, '.agents', 'skills', 'same-name', 'SKILL.md');
  const skills = [{ name: 'allowed', path: disallowed, scope: 'repo', enabled: true }, { name: 'allowed', path: input.path, scope: 'user', enabled: true }];
  const client = metadataClient(cwd, skills); const audit = await policy.apply(client); assert.deepEqual(audit.disabled_skills, [disallowed]);
  assert.equal(policy.read({ path: input.path }).contentItems[0].text, skillText);
  assert.throws(() => policy.read({ path: disallowed }), { code: 'SKILL_READ_DENIED' });
  assert.throws(() => policy.explicitInputs([disallowed]), { code: 'SKILL_INJECTION_DENIED' });
  skills.push({ name: 'new', path: join(cwd, 'new', 'SKILL.md'), scope: 'repo', enabled: true });
  await assert.rejects(policy.verify(client), { code: 'SKILL_ISOLATION_FAILED' }); skills.pop();
  await chmod(input.path, 0o600); await writeFile(input.path, 'Changed owned snapshot'); await assert.rejects(policy.verify(client), { code: 'SKILL_PIN_CHANGED' });
});

test('unqualified administrative scope, shadowed source and unpinned ambient grant fail closed', async t => {
  const f = await fixture(t, { profile: false }); const source = join(f.root, 'SKILL.md');
  await assert.rejects(createSkillPolicy({ home: f.profile.home, cwd: f.root, skillPolicy: { ...strict, shadowed_skill_paths: [source] }, allowed: [{ source_path: source, source_hash: digest(skillText), name: 'allowed', files: { 'SKILL.md': skillText } }] }), { code: 'SKILL_SHADOWED' });
  await assert.rejects(createSkillPolicy({ home: f.profile.home, cwd: f.root, skillPolicy: { ...strict, ambient_allow: [source] } }), { code: 'SKILL_ALLOW_UNPINNED' });
  const policy = await createSkillPolicy({ home: f.profile.home, cwd: f.root, skillPolicy: strict });
  await assert.rejects(policy.apply(metadataClient(f.root, [{ name: 'admin', path: source, scope: 'admin', enabled: true }])), { code: 'SKILL_SCOPE_UNQUALIFIED' });
  assert.deepEqual(policy.tools(), []);
});

test('Host-only policy does not mutate the Skill catalog and rejects Skill injection', async t => {
  const f = await fixture(t, { profile: false });
  const policy = await createSkillPolicy({ home: f.profile.home, cwd: f.root, skillPolicy: strict, hostExecutionOnly: true });
  const client = { call() { assert.fail('Host-only policy must not call the Skill catalog'); } };
  assert.equal((await policy.apply(client)).catalog_mode, 'disabled_by_profile');
  await policy.verify(client);
  assert.deepEqual(policy.tools(), []);
  assert.deepEqual(policy.explicitInputs([]), []);
  assert.throws(() => policy.explicitInputs([join(f.root, 'SKILL.md')]), { code: 'SKILL_INJECTION_DENIED' });
  assert.throws(() => policy.read({ path: join(f.root, 'SKILL.md') }), { code: 'SKILL_READ_DENIED' });
  await assert.rejects(createSkillPolicy({ home: f.profile.home, cwd: f.root, skillPolicy: { ...strict, ambient_allow: [join(f.root, 'SKILL.md')] }, hostExecutionOnly: true }), { code: 'SKILL_ISOLATION_FAILED' });
});

function lifecycleClient(cwd, model, effort, hooks = {}) {
  return {
    pid: hooks.pid ?? 100, events: [], initialized() {},
    async close() { await hooks.close?.(); },
    async call(method, args = {}) {
      if (method === 'initialize') { await hooks.initialize?.(); return {}; }
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'model/list') return { data: [{ model, displayName: model, description: 'fixture', defaultReasoningEffort: effort, inputModalities:['text'],
        contextWindow:272000,supportedReasoningEfforts: [{ reasoningEffort: effort, description: 'fixture' }] }] };
      if (method === 'skills/list') return { data: [{ cwd: args.cwds?.[0] ?? cwd, errors: [], skills: [] }] };
      if (method === 'skills/config/write') return {};
      assert.fail(`Unexpected lifecycle client call: ${method}`);
    },
  };
}

async function lifecycleSessionFixture(t, clientFactory, extraOptions = {}) {
  const f = await fixture(t, { profile: false }); const cwd = join(f.root, 'workspace'); await mkdir(cwd);
  const options = { ...f.options, cwd, modelMetadata: undefined, skillPolicy: strict, allowedSkills: [],
    clientFactory, recordProfileChildImpl: async () => {}, cleanupCodexProfileImpl: async () => {}, ...extraOptions };
  return createStrictSession(options);
}

test('Host-only session reaches a source-free thread without any Skill RPC', async t => {
  const marker = new Error('thread/start intercepted');
  let skillCalls = 0;
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low');
    const originalCall = client.call.bind(client);
    client.call = async (method, args) => {
      if (method.startsWith('skills/')) skillCalls++;
      if (method === 'thread/start') { assert.deepEqual(args.dynamicTools, []); assert.equal(args.ephemeral,true); throw marker; }
      return originalCall(method, args);
    };
    return client;
  }, { hostExecutionOnly: true });
  await assert.rejects(session.turn('fixture'), error => error === marker);
  assert.equal(skillCalls, 0);
});

test('Strict close prevents an internal replacement launch after the current client starts closing', async t => {
  const closeEntered = deferred(); const releaseClose = deferred(); const clients = [];
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low', clients.length === 0 ? {
      close: async () => { closeEntered.resolve(); await releaseClose.promise; },
    } : {}); clients.push(client); return client;
  });
  const turn = session.turn('fixture'); await closeEntered.promise;
  const closing = session.close(); releaseClose.resolve();
  await assert.rejects(turn, { code: 'CODEX_SESSION_CLOSED' }); await closing;
  assert.equal(clients.length, 1, 'closing the first client must fence creation of a replacement client');
});

test('Strict close owns a replacement client that was registered before initialization completed', async t => {
  const initializeEntered = deferred(); const releaseInitialize = deferred(); const clients = []; const closeCalls = [];
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const index = clients.length;
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low', {
      pid: 100 + index,
      initialize: index === 1 ? async () => { initializeEntered.resolve(); await releaseInitialize.promise; } : undefined,
      close: async () => { closeCalls[index] = (closeCalls[index] ?? 0) + 1; },
    }); clients.push(client); return client;
  });
  const turn = session.turn('fixture'); await initializeEntered.promise;
  const closing = session.close(); await closing; releaseInitialize.resolve();
  await assert.rejects(turn, { code: 'CODEX_SESSION_CLOSED' });
  assert.equal(clients.length, 2, 'closing during replacement initialization must not create another client');
  assert.equal(closeCalls[1], 1, 'close must target the registered replacement client, not reuse the prior client state');
});

test('Strict session forwards the host-owned output schema to turn/start', async t => {
  const schema = { type: 'object', properties: { decision: { type: 'string' } }, required: ['decision'], additionalProperties: false };
  const marker = new Error('turn/start intercepted');
  let observed;
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low');
    const originalCall = client.call.bind(client);
    client.call = async (method, args) => {
      if (method === 'thread/start') return { instructionSources: [], model: 'synthetic-model', thread: { id: 'fixture-thread' } };
      if (method === 'turn/start') { observed = args; throw marker; }
      return originalCall(method, args);
    };
    return client;
  });
  await assert.rejects(session.turn('fixture', { output_schema: schema }), error => error === marker);
  assert.deepEqual(observed.outputSchema, schema);
});

test('Strict session preserves the app-server image response shape at its tool boundary', async t => {
  const marker = new Error('image response inspected'), response = { success: true,
    contentItems: [{ type: 'inputImage', imageUrl: 'data:image/png;base64,aW1hZ2U=' }] };
  const toolBroker = { tools: () => [{ name: 'view_workspace_image', description: 'fixture', inputSchema: { type: 'object' } }],
    call: async (name, args, callId) => {
      assert.equal(name, 'view_workspace_image'); assert.deepEqual(args, { path: 'card.png' }); assert.equal(callId, 'image-call');
      return response;
    }, revoke() {}, quiesce: async () => ({ quiescent: true, error: null }) };
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low');
    const originalCall = client.call.bind(client);
    client.call = async (method, args) => {
      if (method === 'thread/start') { assert(args.dynamicTools.some(tool => tool.name === 'view_workspace_image'));
        return { instructionSources: [], model: 'synthetic-model', thread: { id: 'image-thread' } }; }
      if (method === 'turn/start') {
        assert.strictEqual(await options.onToolCall({ threadId: 'image-thread', tool: 'view_workspace_image',
          arguments: { path: 'card.png' }, callId: 'image-call' }), response);
        throw marker;
      }
      return originalCall(method, args);
    };
    return client;
  }, { hostExecutionOnly: true, toolBroker });
  await assert.rejects(session.turn('fixture'), error => error === marker);
});

test('Host-owned correction may use two fresh threads in one node profile, never a third', async t => {
  let started = 0;
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low');
    const originalCall = client.call.bind(client);
    client.call = async (method, args) => {
      if (method === 'thread/start') {
        started++; return { instructionSources: [], model: 'synthetic-model', thread: { id: `thread-${started}` } };
      }
      if (method === 'turn/start') {
        const id = `turn-${started}`;
        client.events.push({ method: 'item/completed', params: { threadId: args.threadId, turnId: id, item: { type: 'agentMessage', text: '{"decision":"candidate_ready"}' } } });
        client.events.push({ method: 'turn/completed', params: { threadId: args.threadId, turn: { id, status: 'completed' } } });
        return { turn: { id } };
      }
      return originalCall(method, args);
    };
    client.waitFor = async matches => client.events.find(matches);
    return client;
  }, { hostExecutionOnly: true, maxTurns: 2 });
  assert.equal((await session.turn('first')).thread_id, 'thread-1');
  assert.equal((await session.turn('correction')).thread_id, 'thread-2');
  await assert.rejects(session.turn('third'), { code: 'CODEX_SESSION_BUSY' });
  await session.close();
});
