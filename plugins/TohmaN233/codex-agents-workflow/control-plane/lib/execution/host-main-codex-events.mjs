const methods = new Set(['thread/started', 'turn/started', 'turn/completed', 'thread/tokenUsage/updated',
  'workflow/turnUsage', 'workflow/toolInterface', 'workflow/rawObservation', 'workflow/toolSearch',
  'workflow/command', 'workflow/sessionShutdown', 'item/tool/call', 'item/started', 'item/completed', 'error']);

// Main and Main fanout share the same bounded Runtime journal contract. Keep
// command/shutdown details observable without exposing their raw outer shape.
export function normalizeHostMainCodexEvent(metadata) {
  if (!methods.has(metadata.method)) return;
  if (!['workflow/command', 'workflow/sessionShutdown'].includes(metadata.method)) return metadata;
  const { method, phase, error_code, ...detail } = metadata;
  if (Array.isArray(detail.pending_process_ids)) {
    detail.pending_command_count = detail.pending_process_ids.length;
    detail.pending_ids_complete = detail.pending_process_ids.length <= 64;
    detail.pending_process_ids = detail.pending_process_ids.slice(0, 64);
  }
  // Runtime validates the complete diagnostic size; oversized evidence fails
  // explicitly instead of being clipped or dropped.
  return { method, status: phase, diagnostic: JSON.stringify(detail), ...(error_code ? { error_code } : {}) };
}
