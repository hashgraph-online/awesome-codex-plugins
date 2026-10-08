import test from 'node:test';
import assert from 'node:assert/strict';
import {delimiter,join} from 'node:path';
import {newestVersion,discoverLocalCodex} from '../lib/execution/local-codex-catalog.mjs';
import {mkdtemp,mkdir,rm,symlink,writeFile,realpath} from 'node:fs/promises';
import {tmpdir} from './physical-tempdir.mjs';
import {digest} from '../lib/workflow-revisions.mjs';
import {pathClientCandidates,CLIENT_MANAGED_MODELS} from '../connectors/local-client-paths.mjs';
import {createCodexClient} from '../lib/execution/codex-app-server-client.mjs';
import {EventEmitter} from 'node:events';
import {PassThrough} from 'node:stream';
test('client discovery compares versions numerically and preserves explicit model uncertainty',()=>{
 assert.equal(newestVersion([{binary:'old',version:'0.99.0'},{binary:'new',version:'0.153.4'}]).binary,'new');
 assert.equal(CLIENT_MANAGED_MODELS.available,null);
 const root=process.platform==='win32'?'C:\\tools':'/tools';
 assert.equal(pathClientCandidates('grok',{PATH:root+delimiter+'relative'+delimiter+root}).length,1);
});
test('catalog-only App Server cannot start a model, login, or edit skills',async()=>{
 const child=new EventEmitter();child.stdin=new PassThrough();child.stdout=new PassThrough();child.stderr=new PassThrough();child.pid=123;child.kill=()=>child.emit('close',0);
 const client=createCodexClient('test',{home:'.',cwd:'.',catalogOnly:true,spawnImpl:()=>child});
 for(const method of ['thread/start','turn/start','account/login/start','skills/config/write'])assert.throws(()=>client.call(method,{}),/outside qualified/);
 child.emit('close',0);await client.close();
});

test('discovery resolves executable aliases to the real distribution and records the selected spelling',async t=>{
 const root=await mkdtemp(join(tmpdir(),'codex-discovery-link-'));
 t.after(()=>rm(root,{recursive:true,force:true}));
 const directory=join(root,'distribution'),aliasDirectory=join(root,'selected-bin'),name=process.platform==='win32'?'codex.exe':'codex';
 await mkdir(directory);const target=join(directory,name),alias=join(aliasDirectory,name);
 await writeFile(target,'actual selected distribution');await symlink(directory,aliasDirectory,process.platform==='win32'?'junction':'dir');
 const resolved=await realpath(target),execImpl=async(binary,args)=>{
   assert.equal(binary,resolved);assert.deepEqual(args,['--version']);return {stdout:'codex-cli 99.42.3\n'};
 };
 const found=await discoverLocalCodex({env:{PATH:''},extra:[alias],execImpl});
 assert.equal(found.binary,resolved);assert.equal(found.selected_path,alias);
 assert.equal(found.sha256,digest('actual selected distribution'));
});
