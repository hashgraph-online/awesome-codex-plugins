// Retention is conservative: only explicit source meaning can exclude a mention.
// Names, extensions and directory names carry no runtime authority.
const nonRuntimeRole=/\b(?:not|never)\s+(?:(?:as|for)\s+)?(?:an?\s+|the\s+)?(?:execution|runtime|production)\s+(?:inputs?|resources?|dependencies|templates?)\b|\b(?:non[- ]runtime|non[- ]executing)\s+(?:reference|example|material)s?\b/i;
const historicalRole=/\b(?:historical|archived?)\s+(?:benchmark|example)(?:\s+(?:example|answer|result))?s?\b|\b(?:historical|archived?)\s+(?:answer|result)s?\b|\b(?:benchmark|example)\s+answers?\s+(?:only|for\s+(?:historical|reference)\s+purposes)\b/i;
const negativeUse=/\b(?:do\s+not|don't|never)\s+(?:use|read|load|consume|execute|run|import|ship|deploy|package)\s+[^.!?;]*<resource>/i;
const runtimeUse=/\b(?:use|read|load|consume|execute|run|import|invoke|apply|pass|supply)\s+[^.!?;]*<resource>|<resource>\s+(?:as\s+|is\s+|provides?\s+)(?:(?:an?|the|required|runtime|execution|input)\s+)*(?:input|template|dependency|program)\b/i;
const runtimeBinding=/\b(?:read|load|consume|execute|run|import|invoke|pass|supply)\s+[^.!?;]*<resource>|<resource>\s+(?:as\s+|is\s+|provides?\s+)(?:(?:an?|the|required|runtime|execution|input)\s+)*(?:input|template|dependency|program)\b/i;

// Code bodies are examples/data rather than prose declarations. Preserve source
// offsets while hiding their words from semantic classification; a path inside
// code still receives a mention and remains retained without outside evidence.
function proseMask(text){
  let delimiter=null,result='',at=0;
  while(at<text.length){
    const code=/^(?:`+|~~~+)/.exec(text.slice(at));
    if(code){
      if(delimiter===null)delimiter=code[0];
      else if(delimiter===code[0])delimiter=null;
      result+=' '.repeat(code[0].length);at+=code[0].length;continue;
    }
    result+=delimiter&&text[at]!=='\n'?' ':text[at];at++;
  }
  return result;
}

function evidenceUnits(text,mask){
  const units=[];
  // Keep declarations local, while retaining a trailing negative qualifier
  // with its subject ("Use X for comparison, not an execution input").
  // A wrapped prose line stays in its own sentence.
  const boundaries=/(?:[.!?;。！？；](?=\s|$)|,\s+(?!(?:not|never)\b)|\s+(?:and|but|while|whereas)\s+(?!(?:not|never)\b)|\n(?=\s*(?:[-*+]\s|\d+[.)]\s|#{1,6}\s))|\n\s*\n)/gi;
  let from=0;
  for(const match of mask.matchAll(boundaries)){
    const to=match.index+match[0].length;
    units.push({from,to,text:text.slice(from,to),prose:mask.slice(from,to)});from=to;
  }
  if(from<text.length)units.push({from,to:text.length,text:text.slice(from),prose:mask.slice(from)});
  return units;
}

function introductoryScope(prose,source){
  // A label can cover a following resource list, but an ordinary historical
  // sentence cannot assign a role to every later mention in that paragraph.
  const labels=/(?:^|\n)([^\n]*[:：][ \t\r]*|[ \t]*#{1,6}[ \t]+[^\n]*)(?=\n|$)/g;
  for(const match of [...prose.matchAll(labels)].reverse()){
    if(!/^\s*(?:[-*+]\s*|\d+[.)]\s*)?$/.test(prose.slice(match.index+match[0].length)))continue;
    const from=match.index+(match[0].startsWith('\n')?1:0);
    return {prose:match[1],evidence:source.slice(from,match.index+match[0].length).trim()};
  }
  return null;
}

export function sourceResourceMentions(source,supportingPaths){
  const original=String(source),text=original.replaceAll('\\','/'),mask=proseMask(text),units=evidenceUnits(original,mask);
  const paragraphStarts=[0,...[...mask.matchAll(/\n[ \t\r]*\n/g)].map(match=>match.index+match[0].length)];
  const entries=supportingPaths.map(resource=>{
    const path=resource.replaceAll('\\','/'),aliases=[...new Set([path,path.startsWith('source/')?path.slice(7):path])],ranges=[];
    for(const alias of aliases){
      let from=text.indexOf(alias);
      while(from>=0){ranges.push({from,to:from+alias.length});from=text.indexOf(alias,from+alias.length);}
    }
    // A full source/foo match and its foo suffix are the same occurrence.
    const mentions=ranges.sort((a,b)=>a.from-b.from||b.to-a.to).filter((range,index,all)=>!all.slice(0,index).some(prior=>prior.from<=range.from&&prior.to>=range.to));
    return {resource,mentions};
  });
  const allMentions=entries.flatMap(entry=>entry.mentions);
  return entries.filter(entry=>entry.mentions.length).map(entry=>{
    const mentions=entry.mentions.map(({from,to})=>{
      const unit=units.find(item=>item.from<=from&&item.to>=to)??{from:0,to:text.length,text:original,prose:mask};
      let prose=unit.prose.slice(0,from-unit.from)+'<resource>'+unit.prose.slice(to-unit.from);
      // Do not attribute a neighboring resource's use verb to this occurrence.
      for(const other of allMentions.filter(item=>item.to<=from&&item.from>=unit.from).sort((a,b)=>b.from-a.from)){
        const boundary=other.to-unit.from;prose=prose.slice(boundary);break;
      }
      const paragraphStart=paragraphStarts.findLast(start=>start<=from);
      const firstMention=allMentions.filter(item=>item.from>=paragraphStart&&item.from<=from).sort((a,b)=>a.from-b.from)[0];
      const introduction=firstMention?mask.slice(paragraphStart,firstMention.from):'';
      const scope=introductoryScope(introduction,firstMention?original.slice(paragraphStart,firstMention.from):'');
      const scopedExclusion=scope&&((!runtimeBinding.test(prose)&&nonRuntimeRole.test(scope.prose))||(!runtimeUse.test(prose)&&historicalRole.test(scope.prose)));
      const excluded=negativeUse.test(prose)
        ||(!runtimeBinding.test(prose)&&nonRuntimeRole.test(prose))
        ||(!runtimeUse.test(prose)&&historicalRole.test(prose))||scopedExclusion;
      return {from,to,evidence:unit.text.trim(),...(scopedExclusion?{scope_evidence:scope.evidence}:{}),
        disposition:excluded?'non_runtime_reference':runtimeUse.test(prose)?'runtime':'ambiguous'};
    });
    return {resource:entry.resource,retained:mentions.some(item=>item.disposition!=='non_runtime_reference'),mentions};
  });
}
