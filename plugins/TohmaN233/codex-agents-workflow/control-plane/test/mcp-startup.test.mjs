import test from 'node:test';
import assert from 'node:assert/strict';
import {cp,mkdtemp,mkdir,readFile,realpath,rm,writeFile,symlink,rename} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import readline from 'node:readline';
import {tmpdir} from './physical-tempdir.mjs';
import {fileURLToPath} from 'node:url';
import {resolve,dirname,join,toNamespacedPath} from 'node:path';
import {probe} from '../../scripts/check-mcp-startup.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');

async function fixture(t,{aliasHome=false,marketplace='codex-agents-workflow',otherMarketplace=false}={}) {
 const rootDir=await mkdtemp(join(tmpdir(),'workflow-mcp-startup-'));
 t.after(()=>rm(rootDir,{recursive:true,force:true}));
 let home=join(rootDir,'home');
 const version=JSON.parse(await readFile(join(root,'.codex-plugin','plugin.json'),'utf8')).version;
 const cached=join(home,'plugins','cache',marketplace,'codex-agents-workflow',version);
 const excluded=new Set(['node_modules','test','web-src','workflow-runs']);
 await mkdir(join(cached,'.codex-plugin'),{recursive:true});
 // Package the plugin tree as installation does, rather than maintaining a
 // second list of runtime directories that can silently omit new assets.
 await cp(root,cached,{recursive:true,filter:source=>!source.split(/[\\/]/).some(part=>excluded.has(part))});
 const installed=[{pluginId:'codex-agents-workflow@'+marketplace,installed:true,enabled:true,version}];
 if(otherMarketplace){
  const other=join(home,'plugins/cache/codex-agents-workflow/codex-agents-workflow',version);
  await cp(cached,other,{recursive:true});
  installed.push({pluginId:'codex-agents-workflow@codex-agents-workflow',installed:true,enabled:true,version});
 }
 if(aliasHome){const alias=join(rootDir,'home-alias');await symlink(home,alias,process.platform==='win32'?'junction':'dir');home=alias;}
 const cwd=join(home,'plugins','cache',marketplace,'codex-agents-workflow');
 // Preload the fake CLI before Node resolves its relative "plugin" entry point:
 // that entry-point resolution itself is unsupported under a Windows namespaced cwd.
 const registryCli=join(rootDir,'registry-cli.cjs');
 await writeFile(registryCli,`if(process.argv[2]==='list' && process.argv[3]==='--marketplace' && process.argv[5]==='--json'){const entries=${JSON.stringify(installed)};process.stdout.write(JSON.stringify({installed:entries.filter(p=>p.pluginId==='codex-agents-workflow@'+process.argv[4])}));process.exit(0);}\n`);
 return {home,cwd,cached,env:{...process.env,CODEX_HOME:home,HOME:home,USERPROFILE:home,CODEX_CLI_PATH:process.execPath,NODE_OPTIONS:`--require ${JSON.stringify(registryCli)}`}};
}

test('bootstrap retains a stable cwd so a live MCP process cannot lock the installed version', {timeout:15000},async t=>{
 let child,closed;
 t.after(async()=>{if(child){child.kill();await closed;}});
 const fx=await fixture(t);
 await writeFile(join(fx.cached,'control-plane/server.mjs'),`process.stdout.write(JSON.stringify({cwd:process.cwd()})+'\\n');process.stdin.resume();`);
 const manifest=JSON.parse(await readFile(join(root,'.mcp.json'),'utf8'));
 child=spawn(process.execPath,manifest.mcpServers['codex-agents-workflow'].args,{cwd:fx.cwd,env:fx.env,stdio:['pipe','pipe','pipe'],windowsHide:true});
 closed=once(child,'close');
 const lines=readline.createInterface({input:child.stdout});
 let stderr='';child.stderr.on('data',chunk=>{stderr+=chunk;});
 const first=await Promise.race([once(lines,'line').then(([line])=>JSON.parse(line)),closed.then(([code])=>{throw new Error(`Bootstrap exited ${code}: ${stderr}`);})]);
 assert.equal(first.cwd,fx.cwd);
 assert.equal(child.exitCode,null);
 const replacement=fx.cached+'-replacement';
 await rename(fx.cached,replacement);
 await rename(replacement,fx.cached);
 assert.equal(child.exitCode,null);
 lines.close();
});

test('packaged MCP initializes and exposes execution tools from ordinary and Windows extended paths',async t=>{
 const fx=await fixture(t);
 for(const cwd of [...new Set([fx.cwd,toNamespacedPath(fx.cwd)])])assert.equal((await probe(root,{cwd,env:fx.env})).status,'ready');
});

test('packaged MCP starts through a symlinked installation home',async t=>{
 const fx=await fixture(t,{aliasHome:true});
 assert.equal((await probe(root,{cwd:fx.cwd,env:fx.env})).status,'ready');
});

for(const otherMarketplace of [false,true])test('packaged MCP starts the launching marketplace, other source installed: '+otherMarketplace,async t=>{
 const fx=await fixture(t,{marketplace:'awesome-codex-plugins',otherMarketplace});
 assert.equal((await probe(root,{cwd:fx.cwd,env:fx.env})).status,'ready');
 const events=(await readFile(join(fx.home,'codex-agents-workflow/mcp-startup.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
 const event=events.find(e=>e.phase==='resolved');
 assert.equal(event.entry,await realpath(join(fx.cached,'control-plane/server.mjs')));
 assert.equal(event.marketplace,'awesome-codex-plugins');
});
