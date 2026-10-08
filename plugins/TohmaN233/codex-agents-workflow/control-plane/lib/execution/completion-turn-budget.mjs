import { canonicalJSON } from '../workflow-revisions.mjs';

/** Local retries belong to the current loop round, never to prior accepted rounds. */
export function currentRoundAttempts(node) {
  if (!node.current_loop_rounds) return node.attempts;
  const signature = canonicalJSON(node.current_loop_rounds);
  return node.attempts.filter(attempt => canonicalJSON(attempt.loop_rounds ?? {}) === signature);
}

/** Count model turns across local attempts; a finished attempt costs at least one. */
export function semanticTurnsConsumed(node) {
  return currentRoundAttempts(node).reduce((sum, attempt) => sum + (['claimed', 'running'].includes(attempt.status)
    ? attempt.completion_turns ?? 1 : Math.max(1, attempt.completion_turns ?? 1)), 0);
}
