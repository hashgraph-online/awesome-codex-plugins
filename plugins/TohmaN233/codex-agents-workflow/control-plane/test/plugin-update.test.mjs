import test from 'node:test';
import assert from 'node:assert/strict';
import {comparePluginVersions,createPluginUpdateChecker,PLUGIN_VERSION_URL} from '../lib/plugin-update.mjs';
import {WorkbenchApi} from '../lib/workbench-api.mjs';
test('console compares patch versions and legacy two-part versions',()=>{
 assert.equal(comparePluginVersions('1.2','1.2.0'),0);assert.equal(comparePluginVersions('1.2.10','1.2.2'),1);
 assert.throws(()=>comparePluginVersions('broken','1.2.2'));
});
test('concurrent console checks share one request, then expire without polling',async()=>{
 let calls=0,time=0;const fetchImpl=async(url,options)=>{calls++;assert.equal(url,PLUGIN_VERSION_URL);assert(options.signal);return {ok:true,json:async()=>({version:'1.2.2'})};};
 const check=createPluginUpdateChecker({installedVersion:'1.2',fetchImpl,now:()=>time});
 const results=await Promise.all([check(),check(),check()]);assert.equal(calls,1);assert(results.every(item=>item.status==='update_available'));
 await check();assert.equal(calls,1);time=300001;await check();assert.equal(calls,2);
});
test('offline and malformed update metadata stay visible and never mean up-to-date',async()=>{
 for(const fetchImpl of [async()=>{throw new Error('offline');},async()=>({ok:false,status:404}),async()=>({ok:true,json:async()=>({version:'invalid'})})]){
  const api=new WorkbenchApi({configPath:'unused',defaultConfigPath:'unused',fetchImpl});
  const result=await api.request({path:'/api/plugin-update',method:'GET'});assert.equal(result.status,400);assert(result.body.error);assert.equal(result.body.status,undefined);
 }
});
test('console version endpoint does not read Run or Provider configuration',async()=>{
 const api=new WorkbenchApi({configPath:'does-not-exist',defaultConfigPath:'does-not-exist',fetchImpl:async()=>({ok:true,json:async()=>({version:'99.0.0'})})});
 const result=await api.request({path:'/api/plugin-update',method:'GET'});assert.equal(result.status,200);assert.equal(result.body.status,'update_available');
});
