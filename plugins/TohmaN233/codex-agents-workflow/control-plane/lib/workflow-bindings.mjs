import { posix } from 'node:path';
import { canonicalJSON } from './workflow-revisions.mjs';
import { requireValue } from './workflow-paths.mjs';

export function pointerParts(pointer) {
  requireValue(typeof pointer === 'string' && (pointer === '' || pointer.startsWith('/')) && !/~(?![01])/.test(pointer), 'INVALID_POINTER', 'Bindings must use JSON Pointer syntax');
  return pointer === '' ? [] : pointer.slice(1).split('/').map(part => part.replaceAll('~1', '/').replaceAll('~0', '~'));
}

export function readPointer(root, pointer) {
  let value = root;
  for (const part of pointerParts(pointer)) {
    if (value === null || typeof value !== 'object' || !Object.hasOwn(value, part)) return { found: false };
    value = value[part];
  }
  return { found: true, value };
}

export function bindingPointers(binding) {
  if (typeof binding === 'string') return [binding];
  requireValue(binding && typeof binding === 'object' && !Array.isArray(binding), 'BINDING_SCHEMA', 'A binding must be a JSON Pointer or a bounded selector');
  const keys = Object.keys(binding);
  requireValue(keys.every(key => ['path', 'coalesce', 'default', 'flat_map', 'pluck', 'zip', 'count_field', 'group', 'every_true'].includes(key)), 'BINDING_SCHEMA', 'Binding selectors contain only path, coalesce, flat_map, pluck, zip, count_field, group, every_true and default');
  if(Object.hasOwn(binding,'flat_map'))requireValue(typeof binding.path==='string'&&!Object.hasOwn(binding,'coalesce')&&typeof binding.flat_map==='string'&&/^[A-Za-z][A-Za-z0-9_]*$/.test(binding.flat_map),'BINDING_SCHEMA','flat_map needs one array path and a named array field');
  if(Object.hasOwn(binding,'pluck'))requireValue(typeof binding.path==='string'&&!Object.hasOwn(binding,'coalesce')&&!Object.hasOwn(binding,'flat_map')&&typeof binding.pluck==='string'&&/^[A-Za-z][A-Za-z0-9_]*$/.test(binding.pluck),'BINDING_SCHEMA','pluck needs one array path and a named field');
  if(Object.hasOwn(binding,'every_true'))requireValue(typeof binding.path==='string'&&!Object.hasOwn(binding,'coalesce')&&!Object.hasOwn(binding,'flat_map')&&!Object.hasOwn(binding,'pluck')&&typeof binding.every_true==='string'&&/^[A-Za-z][A-Za-z0-9_]*$/.test(binding.every_true),'BINDING_SCHEMA','every_true needs one array path and a boolean field');
  if(Object.hasOwn(binding,'zip'))requireValue(typeof binding.path==='string'&&typeof binding.zip==='string'&&binding.zip.startsWith('/')&&!Object.hasOwn(binding,'coalesce')&&!Object.hasOwn(binding,'flat_map')&&!Object.hasOwn(binding,'pluck')&&!Object.hasOwn(binding,'every_true')&&(!Object.hasOwn(binding,'count_field')||typeof binding.count_field==='string'&&/^[A-Za-z][A-Za-z0-9_]*$/.test(binding.count_field))&&(!Object.hasOwn(binding,'group')||Number.isInteger(binding.group)&&binding.group>=1&&binding.group<=32),'BINDING_SCHEMA','zip needs two array paths, optional count field and positive group size');
  else requireValue(!Object.hasOwn(binding,'count_field')&&!Object.hasOwn(binding,'group'),'BINDING_SCHEMA','count_field and group are only valid with zip');
  const pointers = Object.hasOwn(binding, 'path') ? [binding.path] : binding.coalesce;
  requireValue((Object.hasOwn(binding, 'path') ? 1 : 0) + (Object.hasOwn(binding, 'coalesce') ? 1 : 0) === 1,
    'BINDING_SCHEMA', 'A binding selector needs exactly one path or coalesce list');
  requireValue(Array.isArray(pointers) && pointers.length >= 1 && pointers.length <= 32, 'BINDING_SCHEMA', 'A coalesce binding needs 1 to 32 JSON Pointers');
  for (const pointer of pointers) pointerParts(pointer);
  if (Object.hasOwn(binding, 'default')) canonicalJSON(binding.default);
  return binding.zip?[...pointers,binding.zip]:pointers;
}

export function resolveBindings(bindings, context) {
  const output = Object.create(null);
  for (const [name, binding] of Object.entries(bindings ?? {})) {
    const pointers = bindingPointers(binding);
    const result = pointers.map(pointer => ({ pointer, ...readPointer(context, pointer) })).find(item => item.found && item.value !== undefined);
    if (result) {
      if(typeof binding==='object'&&Object.hasOwn(binding,'flat_map')){
        requireValue(Array.isArray(result.value)&&result.value.every(item=>item&&typeof item==='object'&&!Array.isArray(item)&&Array.isArray(item[binding.flat_map])),
          'BINDING_FLAT_MAP','flat_map needs an array of records with the declared array field',{binding:name,field:binding.flat_map});
        output[name]=result.value.flatMap(item=>structuredClone(item[binding.flat_map]));
      } else if(typeof binding==='object'&&Object.hasOwn(binding,'pluck')){
        requireValue(Array.isArray(result.value)&&result.value.every(item=>item&&typeof item==='object'&&!Array.isArray(item)&&Object.hasOwn(item,binding.pluck)),
          'BINDING_PLUCK','pluck needs an array of records with the declared field',{binding:name,field:binding.pluck});
        output[name]=result.value.map(item=>structuredClone(item[binding.pluck]));
      } else if(typeof binding==='object'&&Object.hasOwn(binding,'every_true')){
        requireValue(Array.isArray(result.value)&&result.value.length>0&&result.value.every(item=>item&&typeof item==='object'&&!Array.isArray(item)&&typeof item[binding.every_true]==='boolean'),
          'BINDING_EVERY_TRUE','every_true needs a nonempty array of records with the declared boolean field',{binding:name,field:binding.every_true});
        output[name]=result.value.every(item=>item[binding.every_true]);
      } else if(typeof binding==='object'&&Object.hasOwn(binding,'zip')){
        const paired=readPointer(context,binding.zip);
        const group=binding.group??1;
        requireValue(paired.found&&Array.isArray(result.value)&&Array.isArray(paired.value)&&result.value.length>0&&Math.ceil(result.value.length/group)===paired.value.length,
          'BINDING_ZIP','zip needs two nonempty arrays with matching grouped lengths',{binding:name});
        output[name]=paired.value.map((results,index)=>{
          const sources=result.value.slice(index*group,(index+1)*group);
          const source=group===1?sources[0]:sources;
          if(binding.count_field)requireValue(sources.every(item=>Array.isArray(item?.[binding.count_field]))&&Array.isArray(results)&&sources.reduce((sum,item)=>sum+item[binding.count_field].length,0)===results.length,
            'BINDING_ZIP','zip partition lengths must match the declared source count field',{binding:name,index,field:binding.count_field});
          return {source:structuredClone(source),results:structuredClone(results)};
        });
      } else output[name] = result.value;
    }
    else if (typeof binding === 'object' && Object.hasOwn(binding, 'default')) output[name] = structuredClone(binding.default);
    else requireValue(false, 'BINDING_MISSING', `Required binding ${name} is unavailable`, { binding: name, pointers });
  }
  return output;
}

export function pathBoundaries(values) {
  requireValue(Array.isArray(values), 'PATH_SCOPE', 'Path scope must be an array of bounded paths');
  return [...new Set(values.map(value => {
    requireValue(typeof value === 'string' && value.trim().length>0 && !/[*?\[\]{}!\x00-\x1f]/.test(value), 'PATH_SCOPE', 'Path boundaries cannot be empty or contain globs');
    const path = posix.normalize(value.trim().replaceAll('\\', '/'));
    requireValue(path && path !== '..' && !path.startsWith('../') && !path.startsWith('/') && !/^[a-z]:/i.test(path), 'PATH_SCOPE', 'Path scope must stay inside the workspace');
    return path.replace(/\/$/, '');
  }))].sort();
}

export function intersectBoundaries(parent, child, { caseInsensitive = process.platform === 'win32' } = {}) {
  const left = pathBoundaries(parent); const right = pathBoundaries(child);
  const key = value => caseInsensitive ? value.toLowerCase() : value;
  const within = (base, value) => base==='.' || key(base) === key(value) || key(value).startsWith(key(base) + '/');
  return pathBoundaries(left.flatMap(a => right.flatMap(b => within(a, b) ? [b] : within(b, a) ? [a] : [])));
}

const ARITY = { eq: 2, ne: 2, exists: 1, contains: 2, in: 2, gt: 2, gte: 2, lt: 2, lte: 2, not: 1 };
export function validateExpression(expression, { onPointer = () => {} } = {}, depth = 0) {
  requireValue(depth < 32 && expression && typeof expression === 'object' && !Array.isArray(expression), 'CONDITION_DSL', 'Invalid condition expression');
  if (Object.hasOwn(expression, 'path')) {
    requireValue(Object.keys(expression).length === 1, 'CONDITION_DSL', 'Path operand cannot contain other fields');
    pointerParts(expression.path); onPointer(expression.path); return;
  }
  if (Object.hasOwn(expression, 'value')) {
    requireValue(Object.keys(expression).length === 1, 'CONDITION_DSL', 'Literal operand cannot contain other fields');
    canonicalJSON(expression.value); return;
  }
  requireValue(Object.keys(expression).every(key => ['op', 'args'].includes(key)) && Array.isArray(expression.args), 'CONDITION_DSL', 'Expressions must contain an operator and argument array');
  const logical = ['and', 'or'].includes(expression.op);
  requireValue(logical ? expression.args.length >= 1 && expression.args.length <= 32 : Object.hasOwn(ARITY, expression.op) && expression.args.length === ARITY[expression.op], 'CONDITION_DSL', 'Unsupported operator or argument count');
  for (const child of expression.args) validateExpression(child, { onPointer }, depth + 1);
}

export function evaluateExpression(expression, context) {
  validateExpression(expression);
  function evaluate(node) {
    if (Object.hasOwn(node, 'path')) return readPointer(context, node.path);
    if (Object.hasOwn(node, 'value')) return { found: true, value: node.value };
    if (['and', 'or'].includes(node.op)) {
      for (const argument of node.args) {
        const item = evaluate(argument);
        requireValue(item.found && typeof item.value === 'boolean', 'CONDITION_TYPE', 'Logical operators require booleans');
        if (node.op === 'and' && !item.value) return { found: true, value: false };
        if (node.op === 'or' && item.value) return { found: true, value: true };
      }
      return { found: true, value: node.op === 'and' };
    }
    const values = node.args.map(evaluate);
    if (node.op === 'exists') return { found: true, value: values[0].found };
    requireValue(values.every(item => item.found), 'CONDITION_INPUT_MISSING', 'Condition operand is missing; use exists before comparing optional data');
    const [a, b] = values.map(item => item.value);
    let result;
    const equal = (x, y) => canonicalJSON(x) === canonicalJSON(y);
    switch (node.op) {
      case 'eq': result = equal(a, b); break;
      case 'ne': result = !equal(a, b); break;
      case 'contains':
        requireValue(Array.isArray(a) || (typeof a === 'string' && typeof b === 'string'), 'CONDITION_TYPE', 'contains requires an array or two strings');
        result = Array.isArray(a) ? a.some(value => equal(value, b)) : a.includes(b); break;
      case 'in': requireValue(Array.isArray(b), 'CONDITION_TYPE', 'in requires an array on the right'); result = b.some(value => equal(a, value)); break;
      case 'gt': case 'gte': case 'lt': case 'lte':
        requireValue(typeof a === 'number' && typeof b === 'number' && Number.isFinite(a) && Number.isFinite(b), 'CONDITION_TYPE', 'Numeric comparisons require finite numbers');
        result = { gt: a > b, gte: a >= b, lt: a < b, lte: a <= b }[node.op]; break;
      case 'not':
        requireValue(values.every(item => typeof item.value === 'boolean'), 'CONDITION_TYPE', 'Logical operators require booleans');
        result = !a; break;
      default: throw new Error('Unsupported validated operator');
    }
    return { found: true, value: result };
  }
  const result = evaluate(expression);
  requireValue(result.found && typeof result.value === 'boolean', 'CONDITION_TYPE', 'Condition must produce a boolean');
  return result.value;
}
