// Derived from verified journal data; never another source of Run state.
export function generationProgress({state,pins}, nodeId, now=Date.now()) {
  const node=state.nodes[nodeId];
  const attempt=node?.attempts.find(a=>a.id===node.active_attempt_id) ?? node?.attempts.at(-1);
  const events=attempt?.executor_events ?? [];
  const reads=events.filter(e=>e.kind==='tool_operation' && e.metadata.phase==='read');
  const last=events.at(-1);
  const provider=nodeId==='final'?(pins.authoring_reviewer ?? pins.generation?.reviewer):pins.providers?.find(p=>p.id===pins.root.provenance.selected_provider_id);
  const activity=last?.metadata?.item_type==='contextCompaction' && last.metadata.method==='item/started'?'compacting':last?.kind==='tool_operation'?'reading':last?.metadata?.status ?? 'working';
  return {round:Math.max(1,state.nodes.expand.attempts.length),max_rounds:pins.generation?.settings?.max_rounds ?? 1,
    node_id:nodeId,model:provider?.config.model,effort:provider?.config.reasoning_effort,
    stage_elapsed_ms:attempt?.started_at?Math.max(0,now-Date.parse(attempt.started_at)):0,
    resource_reads:reads.length,read_count_scope:'recent_64_events',last_resource:reads.at(-1)?.metadata.path,activity};
}
