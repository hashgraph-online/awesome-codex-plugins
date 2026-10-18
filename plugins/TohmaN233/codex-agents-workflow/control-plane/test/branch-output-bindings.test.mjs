import assert from 'node:assert/strict';
import {bindingContext} from '../lib/workflow-execution-envelope.mjs';
import {resolveBindings,readPointer} from '../lib/workflow-bindings.mjs';

const state={inputs:{task:'bounded fixture'},nodes:{plain:{status:'skipped',output:null},config:{status:'skipped',output:null},page:{status:'succeeded',output:{observed_valid:true}},explicit_null:{status:'succeeded',output:null}}};
const context=bindingContext(state);
assert.equal(readPointer(context,'/nodes/plain/output').found,false);
assert.deepEqual(resolveBindings({upstream:{coalesce:['/nodes/plain/output','/nodes/config/output','/nodes/page/output']}},context).upstream,{observed_valid:true});
assert.equal(resolveBindings({value:{coalesce:['/nodes/explicit_null/output','/nodes/page/output']}},context).value,null);
assert.equal(resolveBindings({value:{coalesce:['/nodes/plain/output'],default:null}},context).value,null);
assert.throws(()=>resolveBindings({value:'/nodes/plain/output'},context),{code:'BINDING_MISSING'});
assert.equal(state.nodes.plain.output,null,'binding projection must not rewrite journal placeholders');
console.log('branch output bindings: skipped branch unavailable; explicit semantic null preserved');
