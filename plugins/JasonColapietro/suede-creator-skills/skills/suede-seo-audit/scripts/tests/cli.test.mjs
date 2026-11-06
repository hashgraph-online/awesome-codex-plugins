import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const scripts = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const cli = path.join(scripts, 'seo-review.mjs');
const fixture = (name) => path.join(scripts, 'fixtures', name);
const run = (...args) => spawnSync(process.execPath, [cli,...args], { encoding: 'utf8', cwd: scripts });
test('installed CLI captures partial snapshots, merchant opt-in, drift and stored SERP groups', () => {
  const root = mkdtempSync(path.join(tmpdir(), 'seo-cli-'));
  try {
    const out = path.join(root,'baseline');
    let r = run('audit','--input',fixture('pages.json'),'--out',out);
    assert.equal(r.status,0,r.stderr);
    assert.equal(JSON.parse(readFileSync(path.join(out,'seo-audit.json'))).merchant,undefined);
    const before = path.join(out,'metadata-snapshot.json');
    assert.equal(JSON.parse(readFileSync(before)).coverage.complete,false);
    assert.notEqual(run('audit','--input',fixture('pages.json'),'--out',out).status,0);
    const merchant = path.join(root,'merchant');
    r=run('audit','--input',fixture('pages.json'),'--merchant','--out',merchant);
    assert.equal(r.status,0,r.stderr);
    assert.equal(JSON.parse(readFileSync(path.join(merchant,'seo-audit.json'))).merchant[0].offerCount,1);
    r=run('drift','--before',before,'--after',path.join(merchant,'metadata-snapshot.json'),'--out',path.join(root,'drift'));
    assert.equal(r.status,0,r.stderr);
    assert.deepEqual(JSON.parse(readFileSync(path.join(root,'drift','seo-drift.json'))).changes,[]);
    r=run('serp-clusters','--input',fixture('serp.json'),'--context','Synthetic fixture only','--depth','2','--threshold','0.5','--out',path.join(root,'clusters'));
    assert.equal(r.status,0,r.stderr);
    assert.equal(JSON.parse(readFileSync(path.join(root,'clusters','serp-clusters.json'))).clusters.length,2);
  } finally { rmSync(root,{recursive:true,force:true}); }
});
test('CLI rejects malformed, duplicate, foreign, over-budget inputs and unsafe source writes', () => {
  const root = mkdtempSync(path.join(tmpdir(),'seo-cli-bad-'));
  try {
    const input = path.join(root,'bad.json');
    const out=path.join(root,'output');
    const good=JSON.parse(readFileSync(fixture('pages.json')));
    for (const value of [{...good,pages:[]},{...good,pages:[good.pages[0],good.pages[0]]},{...good,pages:[{url:'https://foreign.test/',html:'x'}]},{...good,pages:[{...good.pages[0],html:'x'.repeat(2_000_001)}]}]) {
      writeFileSync(input,JSON.stringify(value));
      assert.notEqual(run('audit','--input',input,'--out',out).status,0);
      assert.equal(existsSync(out),false);
    }
    assert.notEqual(run('audit','--input',fixture('pages.json'),'--out',path.join(scripts,'must-not-create')).status,0);
    assert.equal(existsSync(path.join(scripts,'must-not-create')),false);
    assert.notEqual(run('audit','--input',fixture('pages.json'),'--merchant','--merchant','--out',out).status,0);
    assert.notEqual(run('serp-clusters','--input',fixture('serp.json'),'--out',out).status,0);
    writeFileSync(input,'{');
    assert.notEqual(run('drift','--before',input,'--after',input,'--out',out).status,0);
  } finally { rmSync(root,{recursive:true,force:true}); }
});
