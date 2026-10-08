// One activity definition for every App Server-backed agent executor.
// Accounting/heartbeat notifications never keep an otherwise idle agent alive.
export function agentTurnActivity(event, threadId, turnId) {
  const params = event?.params ?? {};
  if (params.threadId !== threadId || params.turnId !== turnId) return false;
  if (event.method === 'thread/tokenUsage/updated') return false;
  return event.method === 'item/started' || event.method === 'item/completed' || event.method === 'item/tool/call'
    || event.method === 'turn/diff/updated'
    || /^item\/.+\/(?:[^/]*Delta|updated)$/.test(event.method);
}
