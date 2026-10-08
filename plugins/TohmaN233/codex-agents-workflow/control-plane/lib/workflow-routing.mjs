import { requireValue } from './workflow-paths.mjs';
import { templateKind } from './template-kind.mjs';

const ASCII_STOP=new Set(['a','an','and','as','at','be','by','for','from','in','is','it','of','on','or','the','to','with','this','that','please']);

function terms(value) {
  const text=String(value ?? '').normalize('NFKC').toLowerCase();
  const ascii=[...text.matchAll(/[a-z0-9][a-z0-9._-]*/g)].map(match=>match[0]).filter(term=>term.length>1&&!ASCII_STOP.has(term));
  const cjk=[];
  for(const match of text.matchAll(/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]+/gu)){
    const chars=[...match[0]];
    if(chars.length===1)cjk.push(chars[0]);
    else for(let index=0;index<chars.length-1;index++)cjk.push(chars[index]+chars[index+1]);
  }
  return [...new Set([...ascii,...cjk])];
}

function accessSummary(workflow) {
  const semantic=(workflow.nodes ?? []).filter(node=>['agent','tool','skill_ref','subworkflow'].includes(node.type));
  return {
    writes:semantic.some(node=>node.access==='bounded_write'),
    human_approval:(workflow.nodes ?? []).some(node=>node.type==='human_gate'||node.approval?.required===true),
    external_execution:semantic.some(node=>['provider','thread'].includes(node.executor?.kind)),
  };
}

function compact(pack,score,reasons) {
  const workflow=pack.workflow;
  return {id:workflow.id,name:workflow.name,revision_hash:pack.revision_hash,purpose:workflow.description,tags:[...(workflow.tags ?? [])],
    required_inputs:[...(workflow.inputs_schema?.required ?? [])],effects:accessSummary(workflow),score,reasons};
}

function escaped(value){return value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');}
function explicitReference(query,value,{name=false}={}){
  const normalized=String(value ?? '').normalize('NFKC').toLowerCase().trim();
  if(!normalized || name && [...normalized].length<4 || !name && normalized.length<2)return false;
  if(/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]/u.test(normalized))return [...normalized].length>=4&&query.includes(normalized);
  const boundary=name?'a-z0-9':'a-z0-9._-';
  return new RegExp(`(^|[^${boundary}])${escaped(normalized)}($|[^${boundary}])`,'u').test(query);
}

export function routeReadyWorkflows(packs,intent,{limit=5}={}) {
  requireValue(typeof intent==='string'&&intent.trim()&&intent.length<=12000,'WORKFLOW_ROUTE_INTENT','Workflow routing needs a bounded concrete task description');
  requireValue(Array.isArray(packs)&&Number.isInteger(limit)&&limit>=1&&limit<=20,'WORKFLOW_ROUTE_INPUT','Workflow routing needs a bounded Pack list and candidate limit');
  const query=intent.normalize('NFKC').toLowerCase(),queryTerms=terms(intent),available=packs.filter(pack=>pack?.workflow?.status==='ready'&&pack.workflow.enabled!==false&&!['bundled_authoring_workflow','v6-migration'].includes(pack.provenance?.kind)&&templateKind(pack)==='workflow');
  const ranked=available.map(pack=>{
    const workflow=pack.workflow,name=workflow.name.normalize('NFKC').toLowerCase(),id=workflow.id.toLowerCase();
    const explicit=explicitReference(query,id)||explicitReference(query,name,{name:true});
    const fields=[['id',terms(workflow.id),7],['name',terms(workflow.name),6],['tag',terms((workflow.tags ?? []).join(' ')),4],['purpose',terms(workflow.description),2]];
    let score=explicit?1000:0;const reasons=[];
    for(const [field,fieldTerms,weight] of fields){const matches=queryTerms.filter(term=>fieldTerms.includes(term));if(matches.length){score+=matches.length*weight;reasons.push(`${field}:${matches.join(',')}`);}}
    return compact(pack,score,explicit?['explicit_identity',...reasons]:reasons);
  }).filter(item=>item.score>0).sort((left,right)=>right.score-left.score||left.id.localeCompare(right.id));
  if(!ranked.length)return {decision:'none',selected:null,candidates:[],available_ready:available.length};
  const top=ranked[0],next=ranked[1];
  const explicit=ranked.filter(item=>item.reasons.includes('explicit_identity'));
  if(explicit.length>1)return {decision:'candidates',selected:null,candidates:ranked.slice(0,limit),available_ready:available.length};
  const exact=explicit.length===1&&top===explicit[0],strong=explicit.length===0&&top.score>=10&&(!next||top.score>=next.score+4);
  return {decision:exact||strong?'selected':'candidates',selected:exact||strong?top:null,
    candidates:exact||strong?[]:ranked.slice(0,limit),available_ready:available.length};
}
