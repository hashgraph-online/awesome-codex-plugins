import test from 'node:test';
import assert from 'node:assert/strict';
import {analyzeSkillDependencies} from '../lib/skill-import/dependency-reader.mjs';
import {reconcileImportObservations} from '../lib/skill-import/import-reconciliation.mjs';

const snapshot=text=>({files:{'source/SKILL.md':Buffer.from(text)},metadata:{},inventory:[],problems:[]});
for(const fence of ['```markdown','````md','~~~markdown'])test(`${fence} output links remain observations without Skill startup dependencies`,()=>{
  const close=fence.match(/^(`+|~+)/)[0];
  const s=snapshot(`${fence}\n[Output](GUIDE-OUTPUT.md)\n[Online](https://example.com/output)\n${close}\nRead [rules](references/required.md) before drafting.\n`);
  const scan=analyzeSkillDependencies(s);
  assert.equal(scan.references.filter(item=>item.kind==='artifact_template').length,2);
  assert(scan.unresolved.some(item=>item.target==='references/required.md'));
  assert(!scan.unresolved.some(item=>['GUIDE-OUTPUT.md','https://example.com/output'].includes(item.target)));
  const workflow={nodes:[],import_status:{unresolved:[{code:'UNRESOLVED_LOCAL_REFERENCE',path:'source/SKILL.md',line:2,target:'GUIDE-OUTPUT.md',origin:'observed'}]}};
  const result=reconcileImportObservations({workflow,proposal:{},resources:s.files,pack:{provenance:{},import_report:{}}});
  assert(result.evidence.some(item=>item.reason==='artifact_template_reference'&&item.resolution==='reconciled'));
  assert(result.unresolved.some(item=>item.code==='UNRESOLVED_LOCAL_REFERENCE'),'Required prose dependency is preserved');
});

test('a shorter inner fence never ends an outer Markdown template',()=>{
  const scan=analyzeSkillDependencies(snapshot('````markdown\n```js\nconst sample=1;\n```\n[Artifact](CUSTOM.md)\n````\n[Required](CUSTOM.md)\n'));
  assert.equal(scan.references.find(item=>item.line===5).kind,'artifact_template');
  assert(scan.unresolved.some(item=>item.line===7&&item.target==='CUSTOM.md'));
});

test('ordinary resource examples and explicitly declared missing dependencies still block',()=>{
  const s=snapshot('```text\n[Resource](references/required.md)\n```\n');
  assert(analyzeSkillDependencies(s).unresolved.some(item=>item.target==='references/required.md'));
  const declared={code:'UNRESOLVED_LOCAL_REFERENCE',path:'source/SKILL.md',line:2,target:'CUSTOM.md',origin:'declared'};
  const resources=snapshot('```markdown\n[Artifact](CUSTOM.md)\n```\n').files;
  const result=reconcileImportObservations({workflow:{nodes:[],import_status:{unresolved:[declared]}},proposal:{},resources,pack:{provenance:{},import_report:{}}});
  assert(result.unresolved.some(item=>item.origin==='declared'));
});
