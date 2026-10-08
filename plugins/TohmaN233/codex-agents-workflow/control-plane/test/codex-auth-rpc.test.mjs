import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';
import { createCodexClient } from '../lib/execution/codex-app-server-client.mjs';

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
