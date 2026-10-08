import test from 'node:test';
import assert from 'node:assert/strict';
import { createRunRefresh, currentMainPending, loadRunPanelSnapshot, loadRunSnapshot } from '../web-src/run-refresh.mjs';
function deferred() { let resolve, reject; const promise = new Promise((a,b) => { resolve=a; reject=b; }); return {promise, resolve, reject}; }
function snapshot(sequence) { return { state: { sequence }, next: {sequence}, events: [sequence], live: {sequence} }; }
test('later refresh publishes one complete snapshot and discards a late older generation', async () => {
  const control = createRunRefresh(), first = deferred(), second = deferred(), published = [];
  const a = control.refresh(() => first.promise, value => published.push(value));
  const b = control.refresh(() => second.promise, value => published.push(value));
  assert.equal(published.length, 0);
  second.resolve(snapshot(11)); assert.equal(await b, true);
  first.resolve(snapshot(10)); assert.equal(await a, false);
  assert.deepEqual(published, [snapshot(11)]);
  assert.equal(await control.refresh(async () => snapshot(9), value => published.push(value)), false);
  assert.deepEqual(published, [snapshot(11)]);
});
test('selection invalidation rejects in-flight snapshots and current errors remain visible', async () => {
  const control = createRunRefresh(), old = deferred(), published = [];
  const a = control.refresh(() => old.promise, value => published.push(value));
  control.invalidate(); old.resolve(snapshot(20)); assert.equal(await a, false);
  assert.deepEqual(published, []);
  await assert.rejects(control.refresh(async () => { throw new Error('current failure'); }, () => {}), /current failure/);
});

test('an old Run action completing after disposal cannot start or publish another refresh', async () => {
  const control = createRunRefresh(); control.dispose();
  let loaded = false;
  assert.equal(await control.refresh(async () => { loaded = true; return snapshot(99); }, () => assert.fail('published disposed Run')), false);
  assert.equal(loaded, false);
});


test('event polling advances only the published cursor and resets on authority change', async () => {
  const refresh = createRunRefresh(); const calls = []; let published; let head = 2;
  const api = async (_op, args) => {
    calls.push(args.after_sequence);
    return { state: { sequence: head }, next: { sequence: head }, events: [1,2,3].filter(n => n <= head && n > args.after_sequence).map(sequence => ({ sequence })) };
  };
  const poll = authority => refresh.refresh(previous => loadRunSnapshot(api, 'run', authority, previous), value => { published = value; });
  await poll('first'); head = 3; await poll('first');
  assert.deepEqual(calls, [0,2]);
  assert.deepEqual(published.events.map(e => e.sequence), [1,2,3]);
  await poll('rotated'); assert.deepEqual(calls, [0,2,0]);
  const gate = deferred();
  const stale = refresh.refresh(async previous => { await gate.promise; return loadRunSnapshot(api, 'run', 'rotated', previous); }, () => assert.fail('stale published'));
  await poll('rotated'); gate.resolve(); await stale;
  await poll('rotated'); assert.equal(calls.at(-1), 3);
});

test('a Run without a pending Main action still publishes its first snapshot', async () => {
  const refresh = createRunRefresh(); let published;
  const calls=[];
  const api=async (operation,args) => {
    calls.push(operation);
    if(operation==='run_snapshot')return {state:{sequence:1,status:'running'},next:{approvals:[]},events:[{sequence:1}]};
    if(operation==='current_main_pending'){assert.deepEqual(args,{run_id:'run-1'});return null;}
    assert.fail(`Unexpected operation: ${operation}`);
  };
  assert.equal(await refresh.refresh(previous=>loadRunPanelSnapshot(api,'run-1',undefined,previous),value=>{published=value;}),true);
  assert.equal(published.state.status,'running');
  assert.equal(published.bridgeProposal,null);
  assert.deepEqual(calls,['run_snapshot','current_main_pending']);
});

test('Main pending views keep valid acceptance and control gates visible', async () => {
  const final={kind:'final_acceptance',run_id:'run-1',node_id:'final',proposal:{accepted:true}};
  const control={kind:'control_wait',outcome:{status:'blocked',stop_reason:'approval',approvals:[{id:'approval-1'}]}};
  const active={kind:'host_main',run_id:'run-1',status:'running'};
  const detached={run_id:'run-1',pid:1234,phase:'running',at:'2026-09-26T00:00:00.000Z'};
  for(const value of [final,control,active,detached]){
    const expected=value===detached?{...detached,kind:'host_main',status:'running'}:value;
    assert.deepEqual(currentMainPending(value,'run-1'),expected);
    const api=async operation=>operation==='run_snapshot'
      ?{state:{sequence:1},next:{},events:[]}:value;
    const refresh=createRunRefresh();let published;
    assert.equal(await refresh.refresh(previous=>loadRunPanelSnapshot(api,'run-1',undefined,previous,
      async()=>({status:'running'})),snapshot=>{published=snapshot;}),true);
    assert.deepEqual(published.bridgeProposal,expected);
    assert.deepEqual(published.live,{status:'running'});
  }
  assert.equal(currentMainPending(null,'run-1'),null);
});

test('malformed or unknown Main pending responses fail visibly before snapshot publication', async () => {
  for(const value of [undefined,[],{}, {kind:'unknown',run_id:'run-1'},
    {kind:'final_acceptance',run_id:'run-1',node_id:'final'},
    {kind:'control_wait',outcome:null},
    {kind:'host_main',run_id:'another-run',status:'running'},
    {run_id:'run-1',phase:'running',pid:1234}])
    assert.throws(()=>currentMainPending(value,'run-1'),error=>error.detail?.code==='CURRENT_MAIN_PENDING_INVALID');
  const refresh=createRunRefresh();let published=false;
  const api=async operation=>operation==='run_snapshot'
    ?{state:{sequence:1},next:{},events:[]}:{kind:'unknown',run_id:'run-1'};
  await assert.rejects(refresh.refresh(previous=>loadRunPanelSnapshot(api,'run-1',undefined,previous),()=>{published=true;}),
    error=>error.detail?.code==='CURRENT_MAIN_PENDING_INVALID');
  assert.equal(published,false);
});
