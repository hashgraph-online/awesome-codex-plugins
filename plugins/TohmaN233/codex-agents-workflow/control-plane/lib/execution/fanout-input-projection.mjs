import { isAbsolute, relative, resolve } from 'node:path';
import { canonicalJSON } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { intersectBoundaries, pathBoundaries } from '../workflow-bindings.mjs';

export function assignFanoutItems(items,fanout,count) {
  requireValue(Number.isSafeInteger(count)&&count>0&&Array.isArray(items)&&items.length>=count,
    'SUBAGENT_FANOUT_INPUT','Fan-out needs at least one runtime item per resolved sub-Agent');
  if(fanout.max_concurrency!==undefined)requireValue(Number.isSafeInteger(fanout.max_concurrency)&&
    fanout.max_concurrency>=1&&fanout.max_concurrency<=32,
  'SUBAGENT_FANOUT_CONCURRENCY','Fan-out concurrency must be between 1 and 32');
  requireValue(fanout.scheduling==='serial'||fanout.max_concurrency!==undefined||count<=32,
    'SUBAGENT_COUNT','Unbounded parallel fan-out may dispatch at most 32 concurrent sub-Agents');
  if(fanout.distribution==='one_per_item'){
    requireValue(count===items.length,'SUBAGENT_FANOUT_INPUT','One-per-item fan-out count must equal the runtime item count');
    return items.map(item=>[structuredClone(item)]);
  }
  requireValue(fanout.distribution==='partition','SUBAGENT_FANOUT','Fan-out supports one-per-item or partition distribution');
  if(fanout.batch_size!==undefined){
    requireValue(Number.isSafeInteger(fanout.batch_size)&&fanout.batch_size>=1&&fanout.batch_size<=32&&
      count===Math.ceil(items.length/fanout.batch_size),
    'SUBAGENT_FANOUT_INPUT','Batched fan-out count must cover the runtime items in 1–32 item batches');
    return Array.from({length:count},(_,index)=>structuredClone(items.slice(index*fanout.batch_size,(index+1)*fanout.batch_size)));
  }
  const assignments=Array.from({length:count},()=>[]);
  items.forEach((item,index)=>assignments[index%count].push(structuredClone(item)));
  return assignments;
}

export function assignedFanoutIndices(plan, fanout, dispatchIndex) {
  const count=plan.count, size=plan.items.length;
  requireValue(Number.isInteger(dispatchIndex)&&dispatchIndex>=0&&dispatchIndex<count,
    'SUBAGENT_FANOUT_INDEX','Dispatch index is outside the pinned fan-out plan');
  if(fanout.distribution==='one_per_item')return [dispatchIndex];
  if(fanout.batch_size!==undefined){
    const start=dispatchIndex*fanout.batch_size;
    return Array.from({length:Math.min(fanout.batch_size,size-start)},(_,offset)=>start+offset);
  }
  return Array.from({length:Math.ceil((size-dispatchIndex)/count)},(_,offset)=>dispatchIndex+offset*count);
}

export function activeFanoutAssignmentIndices(plan,fanout,inheritedItemIndices=[]){
  const all=Array.from({length:plan.count},(_,index)=>index);
  if(fanout?.result_mode!=='per_item')return all;
  const inherited=new Set(inheritedItemIndices);
  return all.filter(index=>assignedFanoutIndices(plan,fanout,index).some(itemIndex=>!inherited.has(itemIndex)));
}

function partition(value, allItems, assignedItems) {
  if (Array.isArray(value)) return canonicalJSON(value) === canonicalJSON(allItems)
    ? structuredClone(assignedItems) : value.map(item => partition(item, allItems, assignedItems));
  if (value && typeof value === 'object') return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [key, partition(item, allItems, assignedItems)]));
  return value;
}

// Bindings commonly carry structured node outputs as *_json strings. Partition
// their decoded value before compiling a child packet, while leaving unrelated
// shared background intact. The packet compiler serializes JSON bindings once.
export function projectFanoutInputs(inputs, allItems, assignedItems) {
  return Object.fromEntries(Object.entries(inputs ?? {}).map(([key, value]) => {
    if (key.endsWith('_json') && typeof value === 'string') {
      try { return [key, JSON.stringify(partition(JSON.parse(value), allItems, assignedItems))]; }
      catch { return [key, value]; }
    }
    return [key, partition(value, allItems, assignedItems)];
  }));
}

function workspaceBoundary(workspace, value) {
  requireValue(typeof value === 'string' && value.trim(), 'SUBAGENT_ITEM_WRITE_PATHS',
    'Every Host-owned item write path must be a nonempty string');
  const target=value.trim();
  if(!isAbsolute(target))return pathBoundaries([target])[0];
  requireValue(!/[*?\[\]{}!\x00-\x1f]/.test(target),'SUBAGENT_ITEM_WRITE_PATHS',
    'Host-owned item write paths cannot contain globs or control characters');
  const path=relative(resolve(workspace),resolve(target));
  requireValue(!isAbsolute(path)&&path!=='..'&&!path.startsWith('../')&&!path.startsWith('..\\'),
    'SUBAGENT_ITEM_WRITE_PATHS','Host-owned item write path leaves the node workspace',{workspace,target});
  return pathBoundaries([path||'.'])[0];
}

// A fan-out item may carry a Host-produced list of exact write destinations.
// The runtime resolves those values, intersects them with the Run/node grant,
// and gives each child its own broker scope. The Agent never returns or joins
// these paths, so retries cannot corrupt accepted sibling items by transcription.
export function assignedFanoutWritePaths({workspace,nodeAllowedPaths,assignedItems,fanout}) {
  if(!fanout?.write_paths_field)return pathBoundaries(nodeAllowedPaths);
  requireValue(Array.isArray(assignedItems)&&assignedItems.length>0,'SUBAGENT_ITEM_WRITE_PATHS',
    'Per-item write scope needs a nonempty Host assignment');
  const requested=[];
  for(const item of assignedItems){
    requireValue(item&&typeof item==='object'&&!Array.isArray(item)&&Array.isArray(item[fanout.write_paths_field])&&item[fanout.write_paths_field].length>0,
      'SUBAGENT_ITEM_WRITE_PATHS',`Every fan-out item must contain a nonempty ${fanout.write_paths_field} path list`);
    requested.push(...item[fanout.write_paths_field].map(value=>workspaceBoundary(workspace,value)));
  }
  const paths=pathBoundaries(requested);
  for(const path of paths)requireValue(intersectBoundaries(nodeAllowedPaths,[path]).length>0,
    'SUBAGENT_ITEM_WRITE_PATHS',`Fan-out item write path is outside the Run/node grant: ${path}`);
  const effective=intersectBoundaries(nodeAllowedPaths,paths);
  requireValue(effective.length>0,'SUBAGENT_ITEM_WRITE_PATHS','Per-item write scope has no Run/node intersection');
  return effective;
}
