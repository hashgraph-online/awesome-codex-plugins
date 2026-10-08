import { requireValue } from '../workflow-paths.mjs';
import { authoringSourcePath } from '../skill-import/authoring-source.mjs';

const key={type:'string',minLength:1,maxLength:128};
const source={type:'string',minLength:1,maxLength:260};
const until={type:'object',required:['output'],additionalProperties:false,properties:{activity:key,loop:key,output:key,op:{type:'string',enum:['eq','ne','gt','gte','lt','lte']},value:{description:'A typed JSON scalar compared with the named semantic output.'}}};
export const SEMANTIC_LOOP_SCHEMA=Object.freeze({type:'object',required:['key','entry_activity','exit_activity','activity_keys','max_rounds','until'],additionalProperties:false,properties:{
  key,entry_activity:key,exit_activity:key,activity_keys:{type:'array',minItems:2,maxItems:64,items:key},max_rounds:{type:'integer',minimum:1,maximum:Number.MAX_SAFE_INTEGER},until,
  feedback_inputs:{type:'array',maxItems:128,items:{type:'object',required:['name','from'],additionalProperties:false,properties:{name:key,from:source}}},
  item_scope:{type:'object',required:['items','verdicts','paths_field'],additionalProperties:false,properties:{items:source,verdicts:source,paths_field:key,dependencies_field:key}},
}});
export const LOOP_FIELDS=new Set(['round','status','feedback','all_accepted','review_items','repair_items']);
export function semanticLoopReference(value){
  if(typeof value!=='string'||!value.startsWith('loop:'))return null;
  const separator=value.indexOf('.',5);
  return {key:value.slice(5,separator),output:value.slice(separator+1)};
}
const finding=(code,message,keys,field)=>({kind:'semantic',code,message,semantic_keys:keys,affected_semantic_fields:[field],source_refs:[],blocked_by:[],minimal_change:message});

export function semanticLoopFindings(blueprint){
  const findings=[],activities=new Map((blueprint.activities??[]).map(item=>[item.key,item])),loops=new Map();
  const report=(code,message,item)=>findings.push(finding(code,message,[item.key,...(item.activity_keys??[])],`loops.${item.key}`));
  const output=reference=>{const split=typeof reference==='string'?reference.indexOf('.'):-1;return split>0?activities.get(reference.slice(0,split))?.outputs?.find(item=>item.name===reference.slice(split+1)):null;};
  for(const item of blueprint.loops??[]){
    if(loops.has(item.key))report('loop_duplicate',`Repair loop ${item.key} must have a unique semantic key`,item);
    if(activities.has(item.key))report('loop_key_collision',`Repair loop ${item.key} must not reuse an activity semantic key`,item);
    loops.set(item.key,item);
    if(!Number.isSafeInteger(item.max_rounds)||item.max_rounds<1)report('loop_bound',`Repair loop ${item.key} requires a finite positive safe-integer max_rounds`,item);
    const members=item.activity_keys??[];
    if(members.length<2||new Set(members).size!==members.length||members.some(key=>!activities.has(key))||!members.includes(item.entry_activity)||!members.includes(item.exit_activity))report('loop_members',`Repair loop ${item.key} requires distinct existing repair/review activities and entry/exit members`,item);
    const exit=activities.get(item.exit_activity);
    if(exit?.profile!=='review'||exit.tool||exit.task_continues)report('loop_independent_review',`Repair loop ${item.key} must end with a fresh read-only review Provider`,item);
    if(exit?.fail_on_false?.length)report('loop_acceptance_guard',`Repair loop ${item.key} review rejection is semantic feedback; remove fail_on_false from its exit review`,item);
    if(exit?.repeat_until)report('loop_review_retry',`Repair loop ${item.key} exit review cannot replace downstream semantic repair with repeat_until`,item);
    const condition=item.until;
    if(!condition||Boolean(condition.activity)===Boolean(condition.loop)||!['eq','ne','gt','gte','lt','lte'].includes(condition.op??'eq'))report('loop_until',`Repair loop ${item.key} until must reference one activity output or its Host loop ledger`,item);
    else if(condition.loop){if(condition.loop!==item.key||condition.output!=='all_accepted'||!item.item_scope)report('loop_until',`Repair loop ${item.key} ledger acceptance requires its own item_scope and all_accepted`,item);}
    else if(condition.activity!==item.exit_activity||!output(`${condition.activity}.${condition.output}`))report('loop_until',`Repair loop ${item.key} acceptance must consume its exit review output`,item);
    else {
      const declared=output(`${condition.activity}.${condition.output}`),value=Object.hasOwn(condition,'value')?condition.value:true;
      const kind=declared?.kind==='text'||declared?.kind==='enum'?'string':declared?.kind;
      if(!['boolean','string','number','integer'].includes(kind)||(kind==='integer'?!Number.isInteger(value):kind!==typeof value)||['gt','gte','lt','lte'].includes(condition.op)&&!['number','integer'].includes(kind))report('loop_until_type',`Repair loop ${item.key} acceptance comparison must match its exit output type`,item);
    }
    if(condition&&Object.hasOwn(condition,'value')&&(!['string','boolean','number'].includes(typeof condition.value)||typeof condition.value==='number'&&!Number.isFinite(condition.value)))report('loop_until_value',`Repair loop ${item.key} acceptance comparison must use a finite JSON scalar`,item);
    if(new Set((item.feedback_inputs??[]).map(input=>input.name)).size!==(item.feedback_inputs??[]).length)report('loop_feedback',`Repair loop ${item.key} feedback names must be unique`,item);
    for(const input of item.feedback_inputs??[])if(!output(input.from)||!members.includes(input.from.split('.')[0]))report('loop_feedback',`Repair loop ${item.key} feedback must reference a declared body activity output`,item);
    if(item.item_scope){
      const scope=item.item_scope,verdicts=output(scope.verdicts);
      if(!(typeof scope.items==='string'&&(scope.items.startsWith('input:')||output(scope.items)?.kind==='list'))||!scope.paths_field)report('loop_item_source',`Repair loop ${item.key} requires original items from Workflow input or an existing Host list with exact artifact paths`,item);
      if(typeof scope.items==='string'&&!scope.items.startsWith('input:')&&!activities.get(scope.items.split('.')[0])?.tool)report('loop_item_source',`Repair loop ${item.key} original items must be Host-owned; an Agent cannot re-emit original records`,item);
      if(verdicts?.kind!=='list'||scope.verdicts?.split('.')[0]!==item.exit_activity)report('loop_verdicts',`Repair loop ${item.key} item verdicts must be the exit review's positional list`,item);
      const entry=activities.get(item.entry_activity);
      if(!entry?.profile?.endsWith('_write')||!(entry.inputs??[]).some(input=>input.from===`loop:${item.key}.repair_items`))report('loop_repair_input',`Repair loop ${item.key} entry must write only from its Host repair_items handoff`,item);
      if(!(exit?.inputs??[]).some(input=>input.from===`loop:${item.key}.review_items`))report('loop_review_input',`Repair loop ${item.key} exit review must read its Host review_items handoff`,item);
    }
  }
  for(const activity of activities.values())for(const input of activity.inputs??[]){
    const ref=semanticLoopReference(input.from);if(!ref)continue;
    const loop=loops.get(ref.key);
    if(!loop||!LOOP_FIELDS.has(ref.output)||!loop.activity_keys?.includes(activity.key))findings.push(finding('loop_input',`Activity ${activity.key} references an unavailable loop handoff ${input.from}`,[activity.key,ref.key],`activities.${activity.key}.inputs`));
  }
  return findings;
}

function affirmativeRepairReviewClauses(text){
  const review=/(?:\breview\b|\baudit\b|审查|审核|审阅|验收)/i;
  const repair=/(?:\brepair\b|\bfix\b|\brevise\b|\brework\b|修复|修改|返工)/i;
  const repeatedReview=/(?:\b(?:repeat|rerun|re-run)\s+(?:the\s+)?(?:independent\s+)?(?:review|audit)\b|\b(?:review|audit)\b[^;；.!?。！？]{0,60}\bagain\b|\brepeat\s+(?:the\s+)?(?:repair|fix|revise|rework)\b[^;；.!?。！？]{0,60}\b(?:review|audit)\b|(?:重新|再次|重复)(?:进行)?(?:独立)?(?:审查|审核|审阅|验收)|重审|重复(?:修复|修改|返工).{0,30}(?:审查|审核|审阅|验收))/i;
  const negated=/(?:\b(?:do\s+not|don['’]t|never|must\s+not|should\s+not|cannot|can['’]t|no\s+need\s+to|without|not\s+to)\b[^;；.!?。！？]{0,60}(?:repeat|again|review|audit|repair|fix|revise|rework)|(?:不要|不得|禁止|无需|不必|不能|不可|不再|不应|不需要|不重复|不重新)[^;；.!?。！？]{0,30}(?:重复|再次|重新|审查|审核|审阅|验收|修复|修改)|不(?:重复|重审|重新审|再次审))/i;
  const uncertainOrDiscussion=/(?:\b(?:may|might|could|maybe|perhaps|optional|optionally|consider|discuss|reference|references|documentation|example|examples|mentions?|describe|describes|explain|explains|quote|quotes)\b|\bif\s+(?:desired|needed|appropriate)\b|\bnot\s+(?:required|necessary|mandatory)\b|可能|或许|可选|酌情|考虑|讨论|参考|引用|示例|提到|解释|是否|非必须|不是必须|并非必须|不是要求|不作要求)/i;
  // Quoted examples are evidence to review, not affirmative execution policy.
  const instructions=text.replace(/"[^"\n]*"|“[^”\n]*”|‘[^’\n]*’|`[^`\n]*`/g,' ');
  const clauses=instructions.split(/[;；.!?。！？\n]+/).map(clause=>clause.trim()).filter(Boolean),accepted=[];
  for(let index=0;index<clauses.length;index++){
    const clause=clauses[index];
    if(!repeatedReview.test(clause)||negated.test(clause)||uncertainOrDiscussion.test(clause))continue;
    let instruction=clause;
    if(!repair.test(instruction)){
      // A neighboring repair instruction is insufficient without an explicit
      // ordering link; it may concern a different artifact or responsibility.
      if(!/^(?:then\b|after\b|once\b|next\b|随后|然后|再次|修复后|修改后|返工后)/i.test(clause))continue;
      const prior=clauses[index-1];
      if(!prior||!repair.test(prior)||negated.test(prior)||uncertainOrDiscussion.test(prior))continue;
      instruction=`${prior}. ${clause}`;
    }
    if(review.test(instruction))accepted.push(instruction);
  }
  return accepted;
}

// Recognize affirmative repair-and-repeated-review instructions, rather than
// joining unrelated keyword hits. Negation, uncertainty and reference prose
// remain the independent semantic reviewer's responsibility.
export function sourceRepairLoopIntentFindings(proposal,resources){
  if(!['source/SKILL.md','source/WORKFLOW.md'].some(path=>Buffer.isBuffer(resources?.[path])))return [];
  const resource=authoringSourcePath(resources),lines=Buffer.from(resources[resource]??'').toString('utf8').split('\n'),findings=[];
  let start=0;
  const inspect=end=>{
    const text=lines.slice(start,end).join(' ');
    const downstream=/(?:independent(?:ly)?|reviewer|downstream|if (?:the )?review|review (?:rejects|fails)|独立|(?:审查|审核|审阅|验收).*(?:不通过|拒绝|失败))/i.test(text)&&affirmativeRepairReviewClauses(text).length>0;
    if(!downstream)return;
    const span={resource,start_line:start+1,end_line:end},covered=(proposal.nodes??[]).filter(node=>(node.source_spans??[node.source_span]).some(source=>source?.resource===resource&&source.start_line<=end&&source.end_line>=start+1));
    const keys=covered.map(node=>node.semantic_key).filter(Boolean),loop=(proposal.loops??[]).find(loop=>loop.node_ids?.some(id=>covered.some(node=>node.id===id)));
    if(/(?:unbounded|unlimited|without (?:a )?(?:limit|maximum)|无限|不设上限)/i.test(text))findings.push({...finding('loop_source_unbounded','The source explicitly requires unbounded semantic repair; a finite executable loop cannot preserve that instruction',keys,'loops'),source_refs:[span],check_ids:['failure_semantics']});
    else if(!loop)findings.push({...finding('loop_source_missing','The source requires downstream review to repair upstream work and review again; declare a real bounded repair loop rather than local repeat_until or prose',keys,'loops'),source_refs:[span],check_ids:['failure_semantics']});
    else {
      const match=/(?:at most|maximum of|up to)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+rounds?\b|最多\s*(\d+)\s*轮/i.exec(text);
      const number=match?.[1]??match?.[2],words={one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10},bound=number?(words[number.toLowerCase()]??Number(number)):null;
      if(Number.isSafeInteger(bound)&&bound>0&&loop.max_rounds!==bound)findings.push({...finding('loop_source_bound','The repair-loop round limit conflicts with the explicit source bound',keys,'loops'),source_refs:[span],check_ids:['failure_semantics']});
    }
  };
  for(let index=0;index<=lines.length;index++)if(index===lines.length||!lines[index].trim()){inspect(index);start=index+1;}
  return findings;
}

// All concrete identities and pointers are allocated here, never by a planner.
export function compileSemanticLoops({blueprint,nodes,edges,activityIds,activityOutputs,loopIds,nodeId,addEdge,evidence}){
  const pointer=source=>{
    if(source.startsWith('input:'))return `/inputs/${source.slice(6)}`;
    const split=source.indexOf('.'),key=source.slice(0,split),name=source.slice(split+1),id=activityIds.get(key);
    requireValue(id&&Object.hasOwn(activityOutputs.get(key)??{},name),'AUTHORING_SEMANTIC',`Loop source ${source} is unknown`);
    return `/nodes/${id}/output/${name}`;
  };
  const reaches=(from,to)=>{const queue=[from],seen=new Set();while(queue.length){const current=queue.shift();if(current===to)return true;if(seen.has(current))continue;seen.add(current);queue.push(...edges.filter(edge=>edge.source===current).map(edge=>edge.target));}return false;};
  const compiled=[];
  // Compile children first so a parent's region includes generated child entry controls.
  for(const item of [...(blueprint.loops??[])].sort((a,b)=>a.activity_keys.length-b.activity_keys.length)){
    const id=loopIds.get(item.key),entry=activityIds.get(item.entry_activity),exit=activityIds.get(item.exit_activity);
    requireValue(entry&&exit&&entry!==exit&&reaches(entry,exit),'AUTHORING_SEMANTIC',`Repair loop ${item.key} must have a reachable distinct entry and exit`);
    const region=nodes.filter(node=>reaches(entry,node.id)&&reaches(node.id,exit)).map(node=>node.id),members=new Set(region);
    const bodyActivities=nodes.filter(node=>members.has(node.id)&&activityIds.has(node.semantic_key)).map(node=>node.semantic_key);
    requireValue(bodyActivities.length===item.activity_keys.length&&bodyActivities.every(key=>item.activity_keys.includes(key)),'AUTHORING_SEMANTIC',`Repair loop ${item.key} activity_keys must describe the complete closed region`);
    requireValue(edges.every(edge=>members.has(edge.target)&&!members.has(edge.source)?edge.target===entry:members.has(edge.source)&&!members.has(edge.target)?edge.source===exit:true),'AUTHORING_SEMANTIC',`Repair loop ${item.key} must be single-entry, single-exit and closed`);
    let entryNode=entry;
    if(item.item_scope){
      entryNode=nodeId('loop_entry');
      const sections=blueprint.activities.find(activity=>activity.key===item.entry_activity).source_sections;
      nodes.push({id:entryNode,type:'condition',semantic_key:item.key,cases:[{label:'repair',when:{op:'ne',args:[{path:`/loops/${id}/repair_items`},{value:[]}]}}],default_label:'review',confidence:1,...evidence(sections)});
      for(const edge of edges)if(edge.target===entry&&!members.has(edge.source))edge.target=entryNode;
      addEdge(entryNode,entry,{label:'repair',section_ids:sections});addEdge(entryNode,exit,{label:'review',section_ids:sections});members.add(entryNode);
    }
    const source=item.until.loop?`/loops/${loopIds.get(item.until.loop)}/${item.until.output}`:pointer(`${item.until.activity}.${item.until.output}`);
    compiled.push({id,entry_node:entryNode,exit_node:exit,node_ids:[...members],max_rounds:item.max_rounds,until:{op:item.until.op??'eq',args:[{path:source},{value:Object.hasOwn(item.until,'value')?item.until.value:true}]},...(item.feedback_inputs?.length?{feedback_bindings:Object.fromEntries(item.feedback_inputs.map(input=>[input.name,pointer(input.from)]))}:{}),...(item.item_scope?{item_scope:{items:pointer(item.item_scope.items),verdicts:pointer(item.item_scope.verdicts),paths_field:item.item_scope.paths_field,...(item.item_scope.dependencies_field?{dependencies_field:item.item_scope.dependencies_field}:{})}}:{})});
  }
  for(let left=0;left<compiled.length;left++)for(let right=left+1;right<compiled.length;right++){
    const a=new Set(compiled[left].node_ids),b=new Set(compiled[right].node_ids),overlap=[...a].filter(id=>b.has(id));
    requireValue(!overlap.length||[...a].every(id=>b.has(id))||[...b].every(id=>a.has(id)),'AUTHORING_SEMANTIC','Repair loop regions must be nested or disjoint');
  }
  return compiled;
}
