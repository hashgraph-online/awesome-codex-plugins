import test from 'node:test';
import assert from 'node:assert/strict';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {prepareSharedPrefixOutputTransport as prepare,decodeSharedPrefixOutputTransport as decode,
  SHARED_PREFIX_OUTPUT_SCHEMA,SHARED_PREFIX_OUTPUT_SCHEMA_SHA256} from '../lib/execution/shared-prefix-output-transport.mjs';

const ready={type:'object',properties:{ready:{const:true}},required:['ready'],additionalProperties:false};
const result={type:'object',properties:{conclusion:{type:'string'}},required:['conclusion'],additionalProperties:false};
const wrap=json_result=>JSON.stringify({json_result});

test('source readiness and child result use identical strict API schema and hash',()=>{
  const source=prepare('Common knowledge only.',ready),child=prepare('Only this item.',result);
  assert.deepEqual(source.output_schema,child.output_schema);
  assert.deepEqual(source.output_schema,SHARED_PREFIX_OUTPUT_SCHEMA);
  assert.equal(source.schema_sha256,child.schema_sha256);
  assert.equal(source.schema_sha256,SHARED_PREFIX_OUTPUT_SCHEMA_SHA256);
  assert.equal(source.schema_sha256,digest(canonicalJSON(source.output_schema)));
  assert.equal(source.output_schema.type,'object');
  assert.deepEqual(source.output_schema.required,['json_result']);
  assert.equal(source.output_schema.additionalProperties,false);
  assert.equal(source.output_schema.properties.json_result.type,'string');
  source.output_schema.properties.json_result.type='number';
  assert.equal(prepare('Another item.',result).output_schema.properties.json_result.type,'string');
});

test('prepare preserves input and appends only the current semantic schema and wrapping contract',()=>{
  const text='Original task\r\nUnicode 🐱 and \\"quotes\\"\n';
  const prepared=prepare(text,result);
  assert.ok(prepared.text.startsWith(text+'\n\n'));
  assert.ok(prepared.text.includes(canonicalJSON(result)));
  assert.ok(prepared.text.includes('json_result'));
  assert.ok(!prepared.text.includes(canonicalJSON(ready)));
  assert.deepEqual(result,{type:'object',properties:{conclusion:{type:'string'}},required:['conclusion'],additionalProperties:false});
});

test('decode retains exact inner whitespace, nested content, Unicode, newlines and escapes',()=>{
  const value={conclusion:'嵌套 🐱\r\nline\nline\rtab\tquote"slash\\',nested:[{empty:[],n:null,ok:true}]};
  const schema={type:'object',properties:{conclusion:{type:'string'},nested:{type:'array',items:{type:'object'}}},required:['conclusion','nested'],additionalProperties:false};
  const inner=' \r\n'+JSON.stringify(value,null,2)+'\n';
  const decoded=decode(wrap(inner),schema);
  assert.equal(decoded,inner);
  assert.deepEqual(JSON.parse(decoded),value);
});

test('semantic object, array and scalar types keep the same API root',()=>{
  for(const [value,schema] of [[{ready:true},ready],[[1,2],{type:'array',items:{type:'integer'}}],['🐱\n',{type:'string'}],
    [42,{type:'integer'}],[1.25,{type:'number'}],[false,{type:'boolean'}],[null,{type:'null'}]]){
    assert.deepEqual(prepare('Current task.',schema).output_schema,SHARED_PREFIX_OUTPUT_SCHEMA);
    const inner=JSON.stringify(value);
    assert.equal(decode(wrap(inner),schema),inner);
  }
});

test('outer malformed JSON, wrong root, missing or extra fields and wrong field type fail',()=>{
  assert.throws(()=>decode('```json\n'+wrap('{"ready":true}')+'\n```',ready),{code:'SHARED_PREFIX_OUTPUT_OUTER_JSON'});
  assert.throws(()=>decode('{',ready),{code:'SHARED_PREFIX_OUTPUT_OUTER_JSON'});
  for(const raw of ['null','[]','"text"','{}','{"json_result":null}','{"json_result":{}}','{"json_result":"{\\"ready\\":true}","extra":true}']){
    assert.throws(()=>decode(raw,ready),{code:'DATA_INVALID'});
  }
  assert.throws(()=>decode({json_result:'{"ready":true}'},ready),{code:'SHARED_PREFIX_OUTPUT_TEXT'});
});

test('inner bad JSON and violations of the original semantic schema fail without fallback',()=>{
  for(const inner of ['', 'not JSON', '```json\n{"ready":true}\n```', '{"ready":true} trailing']){
    assert.throws(()=>decode(wrap(inner),ready),{code:'SHARED_PREFIX_OUTPUT_INNER_JSON'});
  }
  for(const inner of ['{"ready":false}','{"ready":true,"extra":1}','{}','[]']){
    assert.throws(()=>decode(wrap(inner),ready),{code:'DATA_INVALID'});
  }
  assert.throws(()=>decode(wrap('{"ready":true}'),result),{code:'DATA_INVALID'});
  assert.throws(()=>decode(wrap('{"conclusion":"ready"}'),ready),{code:'DATA_INVALID'});
});

test('invalid text or unsupported semantic schemas fail before preparing or decoding',()=>{
  for(const text of ['',null,42])assert.throws(()=>prepare(text,ready),{code:'SHARED_PREFIX_OUTPUT_TEXT'});
  assert.throws(()=>prepare('Task.',{oneOf:[]}),{code:'DATA_SCHEMA_KEYWORD'});
  assert.throws(()=>decode(wrap('{}'),{oneOf:[]}),{code:'DATA_SCHEMA_KEYWORD'});
});
