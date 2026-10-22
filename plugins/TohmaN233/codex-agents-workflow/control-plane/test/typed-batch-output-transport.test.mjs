import test from 'node:test';
import assert from 'node:assert/strict';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {validateData} from '../lib/workflow-data-schema.mjs';
import {CODEX_NORMAL_PREFIX_SETUP_SCHEMA as ready} from '../lib/execution/codex-session.mjs';
import {createTypedBatchOutputTransport} from '../lib/execution/typed-batch-output-transport.mjs';
import {prepareCodexCommonBatch} from '../lib/execution/codex-common-batch-session.mjs';
import {textAmendmentSchema} from '../lib/execution/native-text-amendment.mjs';

const schema={type:'object',properties:{markdown:{type:'string'}},required:['markdown'],additionalProperties:false};
const raw=value=>JSON.stringify({results:value});

const repair=textAmendmentSchema({fields:['markdown'],max_edits:8,max_replacement_bytes:8192});
test('Host-owned range content retains one common API schema and no mechanical model fields',()=>{
  const repair=textAmendmentSchema({fields:['markdown'],max_edits:8,max_replacement_bytes:8192,addressing:'host_ranges'});
  const transport=createTypedBatchOutputTransport(schema,{repair_schema:repair});
  assert.deepEqual(transport.prepare_setup('Shared.',ready).output_schema,transport.prepare('Correction.',repair).output_schema);
  const payload={replacements:[['改过的内容 😀','另一行']]};
  assert.deepEqual(JSON.parse(transport.decode(JSON.stringify({results:[],repairs:[payload]}),repair)),payload);
  assert(!JSON.stringify(repair).includes('start_line'));assert(!JSON.stringify(repair).includes('end_line'));
});
test('full result and scoped repair preserve one typed API contract and exclude each other',()=>{
  const transport=createTypedBatchOutputTransport(schema,{repair_schema:repair});
  const source=transport.prepare_setup('Common.',ready),full=transport.prepare('Write.',schema),patch=transport.prepare('Correct.',repair);
  assert.deepEqual(source.output_schema,full.output_schema);assert.deepEqual(full.output_schema,patch.output_schema);
  assert.equal(source.schema_sha256,patch.schema_sha256);
  assert.equal(transport.decode_setup('{"results":[],"repairs":[]}',ready),'{"ready":true}');
  assert.equal(transport.decode('{"results":[{"markdown":"draft"}],"repairs":[]}',schema),'{"markdown":"draft"}');
  const edit={amendments:[{field:'markdown',start_line:41,end_line:41,replacement:'Use start.\n'}]};
  assert.deepEqual(JSON.parse(transport.decode(JSON.stringify({results:[],repairs:[edit]}),repair)),edit);
  for(const [rawOutput,phase] of [[{results:[{markdown:'draft'}],repairs:[edit]},repair],
    [{results:[],repairs:[edit]},schema],[{results:[{markdown:'draft'}],repairs:[]},repair]])
    assert.throws(()=>transport.decode(JSON.stringify(rawOutput),phase),{code:'TYPED_BATCH_OUTPUT_PHASE'});
  assert.throws(()=>transport.decode_setup(JSON.stringify({results:[],repairs:[edit]}),ready),{code:'TYPED_BATCH_OUTPUT_PHASE'});
  assert.throws(()=>transport.prepare('Different repair.',{...repair,description:'different'}),{code:'TYPED_BATCH_OUTPUT_SCHEMA'});
});

test('source and child preserve the exact typed strict API schema and hash',()=>{
  const transport=createTypedBatchOutputTransport(schema);
  const source=transport.prepare_setup('Common knowledge.',ready),child=transport.prepare('One item.',schema);
  const expected={type:'object',properties:{results:{type:'array',minItems:0,maxItems:1,items:schema}},required:['results'],additionalProperties:false};
  assert.deepEqual(source.output_schema,expected);assert.deepEqual(child.output_schema,expected);
  assert.equal(source.schema_sha256,child.schema_sha256);
  assert.equal(source.schema_sha256,transport.api_schema_sha256);
  assert.equal(transport.api_schema_sha256,digest(canonicalJSON(expected)));
  assert.deepEqual(transport.api_schema,expected);
  transport.api_schema.properties.results.items.properties.markdown.type='number';
  assert.deepEqual(transport.api_schema,expected);
  assert.deepEqual(transport.setup_schema,ready);
  child.output_schema.properties.results.items.properties.markdown.type='number';
  assert.deepEqual(transport.prepare('Again.',schema).output_schema,expected);
});

test('prepare preserves original text without duplicating semantic schema as prompt text',()=>{
  const text='Task\r\n中文 🐱 "quote" \\slash\n';
  const transport=createTypedBatchOutputTransport(schema),child=transport.prepare(text,schema),source=transport.prepare_setup(text,ready);
  assert.ok(child.text.startsWith(text+'\n\n'));assert.ok(source.text.startsWith(text+'\n\n'));
  assert.ok(!child.text.includes(canonicalJSON(schema)));assert.ok(!source.text.includes(canonicalJSON(schema)));
  assert.ok(source.text.includes('results=[]'));assert.ok(child.text.includes('results'));
  assert.ok(!child.text.includes('json_result'));assert.ok(!source.text.includes('json_result'));
});

test('Unicode Markdown and real newlines have one JSON layer and survive decode exactly',()=>{
  const markdown='# 标题 🐱\r\n\n```js\nconst text = "quote\\slash";\n```\r\n\tend\r';
  const value={markdown},transport=createTypedBatchOutputTransport(schema),encoded=raw([value]);
  assert.deepEqual(JSON.parse(encoded).results[0],value);
  assert.equal(typeof JSON.parse(encoded).results[0],'object');
  assert.equal(transport.decode(encoded,schema),JSON.stringify(value));
  assert.equal(JSON.parse(transport.decode(encoded,schema)).markdown,markdown);
  assert.equal(transport.decode_setup(raw([]),ready),'{"ready":true}');
});

test('source item output and empty child output fail the phase contract',()=>{
  const transport=createTypedBatchOutputTransport(schema);
  assert.throws(()=>transport.decode_setup(raw([{markdown:'wrong phase'}]),ready),{code:'TYPED_BATCH_OUTPUT_PHASE'});
  assert.throws(()=>transport.decode(raw([]),schema),{code:'TYPED_BATCH_OUTPUT_PHASE'});
});

test('different item or readiness schemas fail pin validation before prepare/decode',()=>{
  const transport=createTypedBatchOutputTransport(schema),other={...schema,description:'Different semantic contract'};
  for(const call of [()=>transport.prepare('Item.',other),()=>transport.decode(raw([{markdown:'x'}]),other),
    ()=>transport.prepare_setup('Setup.',schema),()=>transport.decode_setup(raw([]),schema)])
    assert.throws(call,{code:'TYPED_BATCH_OUTPUT_SCHEMA'});
});

test('malformed JSON and framing violations fail without string wrapping or fallback',()=>{
  const transport=createTypedBatchOutputTransport(schema);
  for(const invalid of ['{','```json\n{"results":[]}\n```'])assert.throws(()=>transport.decode(invalid,schema),{code:'TYPED_BATCH_OUTPUT_JSON'});
  for(const invalid of ['null','[]','{}','{"results":null}','{"results":{}}','{"results":[],"extra":true}',raw([{},{}])])
    assert.throws(()=>transport.decode(invalid,schema),{code:'DATA_INVALID'});
  assert.throws(()=>transport.decode({results:[]},schema),{code:'TYPED_BATCH_OUTPUT_TEXT'});
  assert.throws(()=>transport.decode(raw([JSON.stringify({markdown:'wrapped'})]),schema),{code:'DATA_INVALID'});
  assert.throws(()=>transport.decode('{"results":[{"markdown":1e999}]}',schema));
});

test('transport-valid semantic violations remain available for original Host correction',()=>{
  const transport=createTypedBatchOutputTransport(schema),decoded=transport.decode(raw([{markdown:42}]),schema);
  assert.equal(decoded,'{"markdown":42}');
  assert.throws(()=>validateData(JSON.parse(decoded),schema),{code:'DATA_INVALID'});
});

test('invalid text, missing item schema and unsupported DSL fail before preparation',()=>{
  assert.throws(()=>createTypedBatchOutputTransport(undefined),{code:'DATA_SCHEMA'});
  assert.throws(()=>createTypedBatchOutputTransport({oneOf:[]}),{code:'DATA_SCHEMA_KEYWORD'});
  assert.throws(()=>createTypedBatchOutputTransport({type:'object',properties:{x:{type:'string'}},required:['x']}),{code:'AGENT_OUTPUT_SCHEMA'});
  const transport=createTypedBatchOutputTransport(schema);
  for(const text of ['',null,42])assert.throws(()=>transport.prepare(text,schema),{code:'TYPED_BATCH_OUTPUT_TEXT'});
});

test('live common batch requires explicit item schema before acquiring source ownership',async()=>{
  let owned=false;
  await assert.rejects(prepareCodexCommonBatch({onPrefixOwned(){owned=true;}},'Common.'),{code:'CODEX_BATCH_OUTPUT_SCHEMA'});
  assert.equal(owned,false);
  const factory=prepareCodexCommonBatch.usageCapability.responseTransport.create_for_schema;
  assert.equal(typeof factory,'function');
  assert.equal(factory(schema).api_schema_sha256,createTypedBatchOutputTransport(schema).api_schema_sha256);
});
