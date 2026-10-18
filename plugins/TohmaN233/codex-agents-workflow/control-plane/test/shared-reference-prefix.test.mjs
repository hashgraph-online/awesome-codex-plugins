import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {prepareHostMainContext} from '../lib/execution/node-input-materials.mjs';

const text='A complete shared writing rule and its example.\n'.repeat(250);
const bytes=Buffer.from(text),path='references/writing.md';
const resources=[{path,bytes,size:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')}];
const envelope={node_id:'writer',prompt_template:'Write the assigned explanation.',inputs:{common_task:{request:'Preserve all facts.'}},
 resources:[path],context_projection:{references:[path]}};
async function fixture(operation){
 const root=await mkdtemp(join(tmpdir(),'caw-shared-reference-'));
 try{await operation(root);}finally{assert.equal(dirname(root),resolve(tmpdir()));await rm(root,{recursive:true});}
}
test('shared preparation warms the complete medium-size reference before branch-specific inputs',()=>fixture(async directory=>{
 const prepared=await prepareHostMainContext({directory,envelope,resources});
 const manifest=JSON.parse(await readFile(prepared.preparation_path,'utf8'));
 assert.equal(manifest.resources[0].delivery,'inline');
 assert.equal(JSON.parse(prepared.prompt.split('\nResources:\n')[1])[0].content,text);
}));
test('a reference beyond 16 KiB retains complete file delivery',()=>fixture(async directory=>{
 const largeText=text+'complete extra rule\n'.repeat(400),largeBytes=Buffer.from(largeText);
 assert(largeBytes.length>16384);
 const larger=[{path,bytes:largeBytes,size:largeBytes.length,sha256:createHash('sha256').update(largeBytes).digest('hex')}];
 const prepared=await prepareHostMainContext({directory,envelope,resources:larger});
 const manifest=JSON.parse(await readFile(prepared.preparation_path,'utf8'));
 assert.equal(manifest.resources[0].delivery,'file');
 assert.equal(await readFile(manifest.resources[0].local_path,'utf8'),largeText);
}));
test('shared reference admission spills a complete document when the full prompt cannot fit',()=>fixture(async directory=>{
 const prepared=await prepareHostMainContext({directory,envelope,resources,maxPromptChars:4000});
 const manifest=JSON.parse(await readFile(prepared.preparation_path,'utf8'));
 assert.equal(manifest.resources[0].delivery,'file');
 assert(prepared.prompt.length<=4000);
 assert.equal(await readFile(manifest.resources[0].local_path,'utf8'),text);
}));
