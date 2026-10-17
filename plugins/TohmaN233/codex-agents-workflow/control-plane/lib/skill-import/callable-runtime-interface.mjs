// Authoring evidence retains the literal source command. Runtime delivery uses
// its exact pinned program handle, never a private Skill root or alias quote.
export function runtimeCallableInterface(original){
  const result=structuredClone(original);
  delete result.alias_declaration;
  delete result.arguments_source_span;
  delete result.arguments_source_location;
  if(result.stdin){delete result.stdin.source_span;delete result.stdin.source_location;}
  if(result.composite_transport){
    const transport=result.composite_transport;
    // Literal composite text and source coordinates remain private evidence.
    // After coverage binds all members to one operation owner, only transport
    // topology is required at runtime; each member has its own relocated argv.
    result.composite_transport=Object.fromEntries(['composite_id','segment_index','segment_count','connector_before','connector_after','guards','previous_callsite_id','next_callsite_id','member_callsite_ids'].filter(key=>Object.hasOwn(transport,key)).map(key=>[key,transport[key]]));
    result.composite_transport.transport_status='same_activity';
    result.composite_transport.address_binding='pinned_program_handles';
  }
  if(result.target_resource && result.entrypoint){
    const sourceEntrypoint=result.entrypoint;
    if(result.executable===sourceEntrypoint)result.executable=result.target_resource;
    result.entrypoint=result.target_resource;
    if(Array.isArray(result.argv))result.argv=result.argv.map(argument=>argument===sourceEntrypoint?result.target_resource:argument);
  }
  return result;
}

export function runtimeCallableOperation(requirement){
  const original=requirement.details.interface;
  const trigger=original.composite_transport?.guards?.length
    ? `Source shell guard ${original.composite_transport.guards.map(item=>item.connector).join(' ')}; preserve the declared composite transport.`
    : requirement.trigger;
  return {trigger,interface:runtimeCallableInterface(original)};
}

// A shell pipe/guard is one original operation boundary. Splitting its members
// between Agents loses process stdin/exit status; an unrelated tool cannot be
// accepted as its implementation. This is coverage, not another runtime audit.
export function callableBindingIssues(requirements,mappings,nodes,toolContracts=new Map()){
  const issues=new Map(),nodeById=new Map(nodes.map(node=>[node.id,node])),mappingById=new Map(mappings.map(item=>[item.requirement_id,item]));
  const groups=new Map();
  for(const requirement of requirements.filter(item=>item.details?.callable_id)){
    const iface=requirement.details.interface,mapping=mappingById.get(requirement.requirement_id);
    if(!mapping||mapping.status==='unsupported')continue;
    const responsible=(mapping.node_ids??[]).map(id=>nodeById.get(id)).filter(Boolean);
    if(!responsible.some(node=>node.type==='agent'||node.type==='tool'&&(toolContracts.get(node.tool)?.implements??[]).includes(requirement.requirement_id)))issues.set(requirement.requirement_id,'Original callable needs an Agent with its complete interface, or an exact registered tool implementation.');
    if(!iface.composite_transport)continue;
    const group=groups.get(iface.composite_transport.composite_id)??[];group.push(requirement);groups.set(iface.composite_transport.composite_id,group);
  }
  for(const group of groups.values()){
    const transport=group[0].details.interface.composite_transport;
    const memberIds=transport.member_callsite_ids??[];
    const complete=memberIds.length===transport.segment_count&&memberIds.every(id=>id&&group.some(item=>item.requirement_id===id));
    const ownerIds=[...new Set(group.flatMap(item=>mappingById.get(item.requirement_id)?.node_ids??[]))];
    const completeOwners=ownerIds.length>0&&ownerIds.every(id=>{
      const node=nodeById.get(id);
      return group.every(item=>mappingById.get(item.requirement_id)?.node_ids?.includes(id))&&(node?.type==='agent'||node?.type==='tool'&&memberIds.every(callId=>(toolContracts.get(node.tool)?.implements??[]).includes(callId)));
    });
    const bound=complete&&completeOwners&&group.every(item=>item.details.interface.composite_transport.binding_status==='recognized_segments');
    if(!bound)for(const item of group)issues.set(item.requirement_id,'Original composite command requires all recognized members and their pipeline/exit-status guards at one activity, or one exact registered composite-tool contract.');
  }
  return issues;
}
