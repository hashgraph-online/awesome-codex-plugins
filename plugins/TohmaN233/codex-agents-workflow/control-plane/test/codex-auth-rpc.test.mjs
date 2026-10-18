import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';
import { createCodexClient, scrubCodexRawNotification } from '../lib/execution/codex-app-server-client.mjs';

function fixture(options = {}) {
  const child = new EventEmitter();
  child.stdin = new PassThrough(); child.stdout = new PassThrough(); child.stderr = new PassThrough();
  child.kill = () => { child.emit('exit', 0, null); child.emit('close'); };
  const sent = []; child.stdin.on('data', bytes => sent.push(JSON.parse(bytes.toString())));
  const events = [];
  const client = createCodexClient('/fixture', { home: '/fixture', cwd: '/fixture', ...options,
    onEvent: event => events.push(event), spawnImpl: () => child });
  return { client, child, sent, events };
}

test('one stdout chunk may contain more than 256 ordered small notifications during durable backpressure',async()=>{
 let release;const gate=new Promise(resolve=>{release=resolve;}),seen=[];
 const f=fixture({onEventBatch:async messages=>{await gate;seen.push(...messages);}});
 const done=f.client.waitFor(event=>event.method==='item/completed'&&event.params.item.id==='item-349',{timeout:1000});void done.catch(()=>{});
 try{
  const lines=Array.from({length:350},(_,index)=>JSON.stringify({method:'item/completed',params:{item:{id:'item-'+index,type:'reasoning'}}}));
  f.child.stdout.write(lines.join('\n')+'\n');
  assert(f.client.notificationStats().peak_queued>256,'readline can emit the rest of an already-read chunk after stdout.pause');
  release();await done;
  assert.equal(seen.length,350);assert.deepEqual(seen.map(event=>event.params.item.id),Array.from({length:350},(_,index)=>'item-'+index));
 }finally{release();await f.client.close();}
});

test('an exited server with genuinely open stdio still fails with bounded transport facts',async()=>{
 const f=fixture();f.child.stdin.on('finish',()=>f.child.emit('exit',0,null));
 try{await assert.rejects(f.client.close({timeout:2500}),error=>{
  assert.equal(error.code,'CODEX_APP_SERVER_PIPE_HELD');assert.equal(error.details.exit_seen,true);
  assert.equal(error.details.transport_closed,false);assert.equal(error.details.notification_queue,0);
  assert.equal(error.details.stdout_buffered_bytes,0);assert.match(error.message,/transport=/);return true;
 });}finally{f.child.emit('close');}
});

test('notification backpressure retains its existing byte ceiling',async()=>{
 const f=fixture(),rejected=f.client.waitFor(()=>false,{timeout:1000});void rejected.catch(()=>{});
 f.child.stdout.write(JSON.stringify({method:'item/completed',params:{payload:'x'.repeat(8*1024*1024)}})+'\n');
 await assert.rejects(rejected,error=>error.code==='CODEX_NOTIFICATION_QUEUE_LIMIT'&&/byte bound/.test(error.message));
 await f.client.close();
});

test('qualified raw notifications are scrubbed before retained events, callbacks and waiter predicates', async () => {
  const f = fixture({ rawObservation: { supported: true } }), matched = [];
  const wait = f.client.waitFor(event => { matched.push(event); return event.method === 'rawResponse/completed'; }, { timeout: 1000 });
  const secret = 'secret-query-arguments-content-credential';
  f.child.stdout.write(JSON.stringify({ method: 'rawResponseItem/completed', passthrough: secret, params: {
    threadId: 'thread-raw', turnId: 'turn-raw', extra: secret, item: { type: 'tool_search_call', id: 'search-raw',
      call_id: 'call-raw', execution: 'server', status: 'completed', arguments: { query: secret },
      internal_chat_message_metadata_passthrough: { secret }, content: secret, output: secret } } }) + '\n');
  f.child.stdout.write(JSON.stringify({ method: 'rawResponseItem/completed', params: {
    threadId: 'thread-raw', turnId: 'turn-raw', item: { type: 'message', id: 'message-raw', content: [{ text: secret }] } } }) + '\n');
  f.child.stdout.write(JSON.stringify({ method: 'rawResponse/completed', params: {
    threadId: 'thread-raw', turnId: 'turn-raw', responseId: 'response-raw', usageMetadata: { amount: secret, metadata: { secret } },
    usage: { inputTokens: 100, cachedInputTokens: 20, outputTokens: 10, reasoningOutputTokens: 5, totalTokens: 110, secret } } }) + '\n');
  await wait;
  assert.deepEqual(f.client.events[0], { method: 'rawResponseItem/completed', params: {
    threadId: 'thread-raw', turnId: 'turn-raw', item: { type: 'tool_search_call', id: 'search-raw',
      call_id: 'call-raw', execution: 'server', status: 'completed' } } });
  assert.deepEqual(f.client.events[1].params.item, { type: 'message', id: 'message-raw' });
  for (const retained of [f.client.events, f.events, matched]) assert(!JSON.stringify(retained).includes(secret));
  assert.equal(f.client.events[2].params.usage.totalTokens, 110);
  assert.equal(f.client.events[2].params.usageMetadata, undefined);
  await f.client.close();
});

test('malformed qualified raw notifications fail visibly without retaining rejected values', async () => {
  for (const item of [{ type: 'tool_search_call', id: 'search', execution: 'secret-execution' },
    { type: 'tool_search_call', id: 'x'.repeat(257), execution: 'server' },
    { type: 17, id: 'search' },
    { type: 'tool_search_call', id: 'search', execution: 'server', status: 'secret-status' }]) {
    const f = fixture({ rawObservation: { supported: true } });
    const wait = f.client.waitFor(() => false);
    f.child.stdout.write(JSON.stringify({ method: 'rawResponseItem/completed', params: { threadId: 'thread', turnId: 'turn', item } }) + '\n');
    await assert.rejects(wait, error => error.code === 'CODEX_RAW_NOTIFICATION_INVALID' && !error.message.includes('secret-'));
    assert.deepEqual(f.client.events, []); assert.deepEqual(f.events, []);
    await f.client.close();
  }
});

test('declared native tool shapes retain only bounded names, exact call identity and UTF8 sizes at RPC ingress', async () => {
  const f = fixture({ rawObservation: { supported: true } }), matched = [];
  const secret = 'secret-code-query-output-凭据';
  const content = [{ type: 'input_text', text: secret }, { type: 'input_image', image_url: `data:image/png;base64,${secret}`, detail: 'original' },
    { type: 'input_audio', audio_url: secret }, { type: 'encrypted_content', encrypted_content: secret }];
  const items = [
    { type: 'custom_tool_call', id: 'custom-item', call_id: 'custom-call', name: 'exec', input: secret, namespace: secret },
    { type: 'custom_tool_call_output', id: null, call_id: 'custom-call', output: secret, name: null, metadata: secret },
    { type: 'function_call', id: 'function-item', call_id: 'function-call', name: '__proto__', arguments: secret },
    { type: 'function_call_output', id: 'function-output', call_id: 'function-call', output: content },
  ];
  const wait = f.client.waitFor(event => { matched.push(event); return event.method === 'rawResponse/completed'; }, { timeout: 1000 });
  for (const item of items) f.child.stdout.write(JSON.stringify({ method: 'rawResponseItem/completed', params: {
    threadId: 'owned-thread', turnId: 'owned-turn', item } }) + '\n');
  f.child.stdout.write(JSON.stringify({ method: 'rawResponse/completed', params: { threadId: 'owned-thread', turnId: 'owned-turn', responseId: 'response' } }) + '\n');
  await wait;
  const observed = f.client.events.slice(0, 4).map(event => event.params.item);
  assert.deepEqual(observed[0], { type: 'custom_tool_call', id: 'custom-item', call_id: 'custom-call', name: 'exec',
    input_bytes: Buffer.byteLength(secret), output_bytes: null, output_kind: null, input_observation: { status: 'known', lexical_references: [] } });
  assert.equal(observed[1].name, null); assert.equal(observed[1].output_bytes, Buffer.byteLength(secret)); assert.equal(observed[1].output_kind, 'string');
  assert.equal(observed[2].name, '__proto__'); assert.equal(observed[2].input_bytes, Buffer.byteLength(secret));
  assert.equal(observed[3].output_bytes, Buffer.byteLength(JSON.stringify(content))); assert.equal(observed[3].output_kind, 'content_items');
  for (const event of f.client.events.slice(0, 4)) assert.deepEqual(scrubCodexRawNotification(event), event, 'Revalidation preserves only provenance-backed derived fields');
  for (const retained of [f.client.events, f.events, matched]) assert(!JSON.stringify(retained).includes(secret));
  assert(!JSON.stringify(f.client.events).includes('sha256'));
  await f.client.close();
});

test('absent or unrecognized optional raw shape fields remain unknown and forged byte fields are discarded', async () => {
  const f = fixture({ rawObservation: { supported: true } });
  const items = [
    { type: 'function_call', call_id: 'call', name: 'Bearer secret-credential', arguments: { secret: true }, input_bytes: 99999 },
    { type: 'custom_tool_call', call_id: 'call-custom', name: 'x'.repeat(129), input_bytes: 99999 },
    { type: 'function_call_output', output: [{ type: 'input_text', text: 'secret-output', metadata: 'secret-extra' }], output_bytes: 99999 },
    { type: 'custom_tool_call_output', call_id: 'call-custom', output: [{ type: '__proto__', text: 'secret-output' }] },
    { type: 'custom_tool_call_output', call_id: 'call-custom', output: [{ type: { toString: 'secret-type' }, text: 'secret-output' }] },
    { type: 'function_call_output', id: 'last-output', output: { text: 'secret-output' } },
  ];
  for (const item of items) f.child.stdout.write(JSON.stringify({ method: 'rawResponseItem/completed', params: { threadId: 'thread', turnId: 'turn', item } }) + '\n');
  await f.client.waitFor(event => event.params?.item?.id === 'last-output', { timeout: 1000 });
  assert.equal(f.client.events.length, 6);
  for (const event of f.client.events) {
    assert.equal(event.params.item.name, null); assert.equal(event.params.item.input_bytes, null);
    assert.equal(event.params.item.output_bytes, null); assert.equal(event.params.item.output_kind, null);
  }
  assert(!JSON.stringify(f.client.events).includes('secret-'));
  await f.client.close();
});

test('malformed present raw native call identities fail through the original lifecycle without retaining bodies', async () => {
  for (const call_id of ['bad identity secret', 'x'.repeat(257), { secret: true }]) {
    const f = fixture({ rawObservation: { supported: true } }), wait = f.client.waitFor(() => false);
    f.child.stdout.write(JSON.stringify({ method: 'rawResponseItem/completed', params: { threadId: 'thread', turnId: 'turn',
      item: { type: 'custom_tool_call', call_id, name: 'exec', input: 'secret-code' } } }) + '\n');
    await assert.rejects(wait, { code: 'CODEX_RAW_NOTIFICATION_INVALID' });
    assert.deepEqual(f.client.events, []); assert.deepEqual(f.events, []);
    await f.client.close();
  }
});

test('unknown non-search raw types discard arbitrary bodies and nullable search IDs remain explicitly unattributed metadata', async () => {
  const f = fixture({ rawObservation: { supported: true } });
  const events = [
    { type: 'future-secret-type', id: { secret: 'secret-body' }, content: 'secret-body' },
    { type: 'tool_search_call', id: null, call_id: null, execution: 'server', status: null, arguments: 'secret-body' },
  ];
  for (const item of events) f.child.stdout.write(JSON.stringify({ method: 'rawResponseItem/completed',
    params: { threadId: 'thread', turnId: 'turn', item } }) + '\n');
  await f.client.waitFor(event => event.params?.item?.type === 'tool_search_call', { timeout: 1000 });
  assert.deepEqual(f.client.events.map(event => event.params.item), [{ type: 'other' }, { type: 'tool_search_call', execution: 'server' }]);
  for (const retained of [f.client.events, f.events]) assert(!JSON.stringify(retained).includes('secret'));
  await f.client.close();
});

test('unqualified unsolicited raw bodies are excluded while ordinary execution events continue', async () => {
  const f = fixture({ rawObservation: { supported: false } });
  f.child.stdout.write(JSON.stringify({ method: 'rawResponseItem/completed', params: { secret: 'must-not-be-retained' } }) + '\n');
  f.child.stdout.write(JSON.stringify({ method: 'turn/completed', params: { turn: { id: 'ordinary' } } }) + '\n');
  assert.equal((await f.client.waitFor(event => event.method === 'turn/completed', { timeout: 1000 })).params.turn.id, 'ordinary');
  assert.equal(f.client.events.length, 1); assert.equal(f.events.length, 1);
  await f.client.close();
});

test('credential-only RPC cannot create model threads or start login flows', async () => {
  const f = fixture({ credentialOnly: true });
  for (const method of ['thread/list', 'thread/start', 'turn/start', 'account/login/start', 'skills/list']) {
    assert.throws(() => f.client.call(method, {}), /outside qualified/);
  }
  assert.deepEqual(f.sent, []);
  const result = f.client.call('getAuthStatus', { includeToken: true, refreshToken: true });
  f.child.stdout.write(JSON.stringify({ id: f.sent[0].id, result: { authMethod: 'chatgpt', authToken: 'example-fixture-secret' } }) + '\n');
  assert.equal((await result).authToken, 'example-fixture-secret');
  assert.deepEqual(f.events, []); assert.deepEqual(f.client.events, []);
  await f.client.close();
});

test('native observer can list child identities while catalog-only clients remain limited',async()=>{
  const f=fixture(),params={parentThreadId:'parent',sourceKinds:['subAgentThreadSpawn'],useStateDbOnly:true};
  const result=f.client.call('thread/list',params);
  assert.deepEqual(f.sent[0].params,params);
  f.child.stdout.write(JSON.stringify({id:f.sent[0].id,result:{data:[],nextCursor:null}})+'\n');
  assert.deepEqual(await result,{data:[],nextCursor:null});await f.client.close();
  const catalog=fixture({catalogOnly:true});assert.throws(()=>catalog.client.call('thread/list',params),/outside qualified/);
  assert.deepEqual(catalog.sent,[]);await catalog.client.close();
});

test('token refresh responses stay off worker tools and event logs; raw RPC errors are redacted', async () => {
  let refreshed = false; let toolCalled = false;
  const f = fixture({ onAuthRefresh: async params => { assert.equal(params.previousAccountId, 'fixture-account'); refreshed = true; return { accessToken: 'example-fixture-secret', chatgptAccountId: 'fixture-account' }; }, onToolCall: () => { toolCalled = true; } });
  f.child.stdout.write(JSON.stringify({ id: 10, method: 'account/chatgptAuthTokens/refresh', params: { previousAccountId: 'fixture-account' } }) + '\n');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(refreshed, true); assert.equal(toolCalled, false);
  assert.equal(f.sent[0].result.accessToken, 'example-fixture-secret');
  assert.deepEqual(f.events, []); assert.deepEqual(f.client.events, []);
  const failed = f.client.call('account/read', {});
  f.child.stdout.write(JSON.stringify({ id: f.sent[1].id, error: { code: -1, message: 'example-fixture-secret', data: 'example-fixture-secret' } }) + '\n');
  await assert.rejects(failed, error => !error.message.includes('example-fixture-secret') && error.message.includes('code=-1'));
  await f.client.close();
  const other = fixture();
  assert.throws(() => other.client.call('account/login/start', { type: 'chatgptAuthTokens', accessToken: 'example-fixture-secret' }), /Unsupported authentication flow/);
  await other.client.close();
});

test('command RPC reports a safe Windows sandbox diagnostic without exposing the raw error',async()=>{
  const f=fixture({commandOnly:true});
  const failed=f.client.call('command/exec',{});
  const id=f.sent[0].id;
  f.child.stdout.write(JSON.stringify({id,error:{code:-32603,
    message:'windows sandbox: helper_unknown_error: setup refresh had errors private-sentinel',data:'example-fixture-secret'}})+'\n');
  await assert.rejects(failed,error=>error.code==='CODEX_RPC_ERROR'
    &&error.rpc_diagnostic==='windows_sandbox_setup_refresh'
    &&error.message.includes('diagnostic=windows_sandbox_setup_refresh')
    &&!error.message.includes('private-sentinel')&&!error.message.includes('example-fixture-secret'));
  await f.client.close();
});

test('zero event timeout keeps a background model turn alive until matching output arrives', async () => {
  const f = fixture();
  const waiting = f.client.waitFor(event => event.method === 'turn/completed', {
    timeout: 0,
    activity: event => event.method === 'item/agentMessage/delta',
  });
  await new Promise(resolve => setTimeout(resolve, 25));
  f.child.stdout.write(JSON.stringify({ method: 'turn/completed', params: { turn: { id: 'turn-1' } } }) + '\n');
  assert.equal((await waiting).params.turn.id, 'turn-1');
  assert.throws(() => f.client.waitFor(() => false, { timeout: -1 }), /nonnegative integer/);
  await f.client.close();
});

test('streaming deltas remain activity signals without filling the replay event log', async () => {
  const f=fixture(),waiting=f.client.waitFor(event=>event.method==='turn/completed',{timeout:1000,activity:event=>event.method==='item/agentMessage/delta'});
  for(let index=0;index<50;index++)f.child.stdout.write(JSON.stringify({method:'item/agentMessage/delta',params:{delta:'token'}})+'\n');
  f.child.stdout.write(JSON.stringify({method:'item/completed',params:{item:{type:'agentMessage',text:'done'}}})+'\n');
  f.child.stdout.write(JSON.stringify({method:'turn/completed',params:{turn:{id:'turn-stream'}}})+'\n');
  assert.equal((await waiting).params.turn.id,'turn-stream');
  assert.deepEqual(f.client.events.map(event=>event.method),['item/completed','turn/completed']);
  await f.client.close();
});

test('sqlite state startup failure is classified without exposing stderr by default', async () => {
  const f = fixture();
  const pending = f.client.call('initialize', {});
  f.child.stderr.write('Error: failed to initialize sqlite state runtime under C:\\fixture: private-sentinel\n');
  f.child.emit('exit', 1, null);
  await assert.rejects(pending, error => error.code === 'CODEX_STATE_RUNTIME_INIT' && !error.message.includes('private-sentinel'));
  f.child.emit('close');
});

test('independent dynamic tools execute concurrently while RPC responses and events continue', async () => {
  const entered = [], replies = [];
  const f = fixture({ onToolCall: params => {
    entered.push(params.tool);
    return new Promise(resolve => replies.push(resolve));
  } });
  for (const [id, tool] of [[101, 'one'], [102, 'two']])
    f.child.stdout.write(JSON.stringify({ id, method: 'item/tool/call', params: { tool } }) + '\n');
  await new Promise(resolve => setImmediate(resolve));
  try {
    assert.deepEqual(entered, ['one', 'two']);
    const rpc = f.client.call('config/read', {});
    const id = f.sent.at(-1).id;
    f.child.stdout.write(JSON.stringify({ id, result: { config: {} } }) + '\n');
    f.child.stdout.write(JSON.stringify({ method: 'turn/completed', params: { turn: { id: 'concurrent' } } }) + '\n');
    assert.deepEqual(await rpc, { config: {} });
    assert.equal((await f.client.waitFor(e => e.method === 'turn/completed', { timeout: 500 })).params.turn.id, 'concurrent');
    replies[1]({ success: true, contentItems: [{ type: 'inputText', text: 'two' }] });
    replies[0]({ success: true, contentItems: [{ type: 'inputText', text: 'one' }] });
    await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(f.sent.filter(x => [101,102].includes(x.id)).map(x => x.id), [102,101]);
  } finally {
    for (const resolve of replies) resolve({ success: true, contentItems: [] });
    await f.client.close();
  }
});

test('dynamic handler failure is observable and late handler completion never writes after shutdown', async () => {
  let rejectTool, resolveTool;
  const f = fixture({ onToolCall: params => new Promise((resolve, reject) => {
    if (params.tool === 'bad') rejectTool = reject;
    else resolveTool = resolve;
  }) });
  for (const [id, tool] of [[201,'bad'],[202,'slow']])
    f.child.stdout.write(JSON.stringify({ id, method: 'item/tool/call', params: { tool } }) + '\n');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(typeof resolveTool, 'function');
  const pending = f.client.call('config/read', {});
  const error = Object.assign(new Error('tool execution failed'), { code: 'FIXTURE_TOOL_FAILED' });
  rejectTool(error);
  await assert.rejects(pending, { code: 'FIXTURE_TOOL_FAILED' });
  assert.throws(() => f.client.call('config/read', {}), { code: 'FIXTURE_TOOL_FAILED' });
  await f.client.close();
  resolveTool({ success: true, contentItems: [] });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(f.sent.some(x => x.id === 202), false);
});

test('native ingress observes fixed lexical references and strict descriptor structure without retaining source or descriptor names',async()=>{
 const input='/* ALL_TOOLS */ const text = "tools.web__run"; // tools.exec_command and secret_input_identifier',
  output=JSON.stringify([{name:'secret_catalog_identifier',description:'secret_catalog_description'},{name:'__proto__',description:'secret_second_description'}]);
 const call={method:'rawResponseItem/completed',params:{threadId:'owned',turnId:'turn',item:{type:'custom_tool_call',call_id:'call',name:'exec',input,
  input_observation:{status:'known',lexical_references:['tools.secret_function']}}}},
  result={method:'rawResponseItem/completed',params:{threadId:'owned',turnId:'turn',item:{type:'custom_tool_call_output',call_id:'call',output,
  output_observation:{status:'known',descriptor_count:999}}}};
 const first=scrubCodexRawNotification(call),second=scrubCodexRawNotification(result);
 assert.deepEqual(first.params.item.input_observation,{status:'known',lexical_references:['ALL_TOOLS','tools.web__run','tools.exec_command']});
 assert.deepEqual(second.params.item.output_observation,{status:'known',structural_kind:'tool_descriptor_array',descriptor_count:2});
 assert.equal(first.params.item.input_bytes,Buffer.byteLength(input));assert.equal(second.params.item.output_bytes,Buffer.byteLength(output));
 assert.deepEqual(scrubCodexRawNotification(first),first);assert.deepEqual(scrubCodexRawNotification(second),second);
 assert.throws(()=>first.params.item.input_observation.lexical_references.push('tools.secret_function'),TypeError);
 first.params.item.input_observation={status:'known',lexical_references:['tools.secret_function']};
 assert.deepEqual(scrubCodexRawNotification(first).params.item.input_observation,{status:'known',lexical_references:['ALL_TOOLS','tools.web__run','tools.exec_command']});
 const serialized=JSON.stringify([scrubCodexRawNotification(first),second]);assert(!serialized.includes('secret_'));assert(!serialized.includes('sha256'));
 const cloned=scrubCodexRawNotification({...first,params:{...first.params,item:{...first.params.item}}});
 assert.deepEqual(cloned.params.item.input_observation,{status:'unknown'},'Serialized/copied fields cannot recreate private ingress provenance');
});

test('native descriptor observation stays unknown for prefixed arbitrary unsupported and incomplete outputs',()=>{
 const descriptors=JSON.stringify([{name:'safe_name',description:'secret_description'}]);
 const outputs=['Script completed\n'+descriptors,'{"name":"safe_name","description":"secret_description"}','[]','["secret"]',
  '[{"name":"safe_name","description":"secret_description","query":"secret_query"}]',
  '[{"name":"bad name","description":"secret"}]','[{"name":"'+'x'.repeat(129)+'","description":"secret"}]',
  '[{"name":"safe_name","description":42}]',descriptors.slice(0,-1),[{name:'safe_name',description:'secret'}],
  [{type:'input_text',text:descriptors},{type:'input_text',text:descriptors}],
  [{type:'input_text',text:descriptors,metadata:'secret_metadata'}],{secret:'secret_body'}];
 for(const output of outputs){
  const safe=scrubCodexRawNotification({method:'rawResponseItem/completed',params:{threadId:'owned',turnId:'turn',item:{type:'function_call_output',call_id:'call',output}}});
  assert.deepEqual(safe.params.item.output_observation,{status:'unknown'});assert(!JSON.stringify(safe).includes('secret'));
 }
 const safe=scrubCodexRawNotification({method:'rawResponseItem/completed',params:{threadId:'owned',turnId:'turn',item:{type:'function_call_output',call_id:'call',
  output:[{type:'input_text',text:descriptors}]}}});
 assert.deepEqual(safe.params.item.output_observation,{status:'known',structural_kind:'tool_descriptor_array',descriptor_count:1});
 assert.equal(safe.params.item.output_kind,'content_items');assert(!JSON.stringify(safe).includes('safe_name'));
});

test('native observation inspects complete bounded UTF8 strings and discards forged optional observation fields',()=>{
 const event=item=>({method:'rawResponseItem/completed',params:{threadId:'owned',turnId:'turn',item}});
 for(const [input,status]of [['é'.repeat(32768),'known'],['é'.repeat(32769),'oversize'],['ALL_TOOLS'+'x'.repeat(65536),'oversize']]){
  const safe=scrubCodexRawNotification(event({type:'function_call',call_id:'call',name:'exec',arguments:input,input_observation:{status:'known',lexical_references:['tools.web__run']}}));
  assert.equal(safe.params.item.input_observation.status,status);assert.equal(safe.params.item.input_bytes,Buffer.byteLength(input));
  if(status==='oversize')assert.deepEqual(safe.params.item.input_observation,{status:'oversize'});
 }
 const unknown=scrubCodexRawNotification(event({type:'custom_tool_call',call_id:'call',name:'exec',input:{secret:'tools.web__run'},input_observation:{status:'known',lexical_references:['ALL_TOOLS']}}));
 assert.deepEqual(unknown.params.item.input_observation,{status:'unknown'});
 const falseMatch=scrubCodexRawNotification(event({type:'custom_tool_call',call_id:'call',input:'xALL_TOOLS tools.web__run_extra tools.exec_command_more'}));
 assert.deepEqual(falseMatch.params.item.input_observation,{status:'known',lexical_references:[]});
 const output=JSON.stringify([{name:'tool',description:'x'.repeat(65536)}]);
 const oversize=scrubCodexRawNotification(event({type:'function_call_output',call_id:'call',output,output_observation:{status:'known',descriptor_count:1}}));
 assert.deepEqual(oversize.params.item.output_observation,{status:'oversize'});assert.equal(oversize.params.item.output_bytes,Buffer.byteLength(output));
});

test('actual RPC ingress observer and waiter retain only structural catalog count and lexical labels',async()=>{
 const f=fixture({rawObservation:{supported:true}}),matched=[];
 const wait=f.client.waitFor(event=>{matched.push(event);return event.params?.item?.type==='custom_tool_call_output';},{timeout:1000});
 const input='ALL_TOOLS.filter(t => t.description.includes("secret_research_query"));',output=JSON.stringify([{name:'secret_native_name',description:'secret_native_description'}]);
 for(const item of [{type:'custom_tool_call',call_id:'call',input},{type:'custom_tool_call_output',call_id:'call',output}])
  f.child.stdout.write(JSON.stringify({method:'rawResponseItem/completed',params:{threadId:'owned',turnId:'turn',item}})+'\n');
 await wait;
 for(const retained of [f.client.events,f.events,matched]){const text=JSON.stringify(retained);assert(!text.includes('secret_'));assert(!text.includes('filter'));assert(!text.includes('sha256'));}
 assert.equal(f.client.events[1].params.item.output_observation.descriptor_count,1);await f.client.close();
});
