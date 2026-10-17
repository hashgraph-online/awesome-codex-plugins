export function strictSessionPresentation(current, snapshot) {
  const attempt = current?.attempts.at(-1);
  if (attempt?.dispatch?.receipt?.executor !== 'codex-app-server') return null;
  // A late poll can belong to a previously selected node or attempt. The Run
  // journal is authoritative even after live polling stops at node completion.
  const cached = snapshot?.attempt_id === attempt.id ? snapshot.value : null;
  const journalStatus = attempt.executor_events?.findLast(event => event.kind === 'session_state')?.metadata?.status;
  const active = ['claimed', 'running'].includes(current.status);
  const status = active && journalStatus !== 'closed' && cached?.status === 'unavailable'
    ? 'unavailable' : journalStatus ?? cached?.status;
  if (!status) return null;
  return {
    status,
    show_login: active && ['auth_required', 'auth_pending'].includes(status),
    output_preview: active && status !== 'closed' ? cached?.output_preview : undefined,
    error: status === 'unavailable' ? cached?.error : undefined,
  };
}
