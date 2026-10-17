import test from 'node:test';
import assert from 'node:assert/strict';
import {consoleToken} from '../web-src/console-token.mjs';
test('authenticated console reload preserves its same-tab token after URL cleanup',()=>{
 const values=new Map(),storage={getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value)},history={replaceState(...args){this.url=args[2];}};
 assert.equal(consoleToken(new URL('http://localhost:4321/workflows#token=exact-value'),history,storage),'exact-value');
 assert.equal(history.url,'/workflows');
 assert.equal(consoleToken(new URL('http://localhost:4321/workflows'),history,storage),'exact-value');
 assert.equal(consoleToken(new URL('http://localhost:4322/workflows'),history,storage),'');
});
test('a newly supplied console credential replaces the old same-origin value',()=>{
 const values=new Map([['caw.console-token:http://localhost:4321','expired']]),storage={getItem:key=>values.get(key),setItem:(key,value)=>values.set(key,value)};
 assert.equal(consoleToken(new URL('http://localhost:4321/workflows#token=current'),{replaceState(){}},storage),'current');
 assert.equal(values.get('caw.console-token:http://localhost:4321'),'current');
});
