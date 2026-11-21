import {
  deliverBatch,
  enqueueDecision,
  previousApproval,
  recordEvaluationError,
  rememberPendingApproval,
  requestDecision,
} from '../../core/bridge.mjs'
import {
  activityForHook,
  approvalFingerprint,
  codexEvaluationFailure,
  codexToolDecision,
  evaluationForHook,
  rememberToolDecision,
} from './bridge.mjs'

// Codex's hook timeout is set to 600 seconds in the plugin, so a held call
// gives up a minute earlier and tells the agent how to continue.
export const holdMs = () => (Number(process.env.ACTERA_HOLD_SECONDS) || 540) * 1000
export const pollMs = () => Number(process.env.ACTERA_HOLD_POLL_MS) || 2000

// Codex waits for every process a hook starts, so queued reports are sent
// from the hook itself rather than a background worker. A failure leaves them
// queued (with a short back-off) for the next hook or an explicit flush.
export async function deliverQueued(config, home) {
  const result = await deliverBatch(config, { home, limit: 8, timeoutMs: 3000 })
  if (result.error) await recordEvaluationError(new Error(`Report delivery: ${result.error}`), home)
}

// Decide one PreToolUse call and return Codex's hook output, or null to leave
// the call to Codex. `hold` waits on a Decision that needs approval.
export async function preToolUse(hook, config, home, { hold }) {
  let output
  let evaluationError
  let request
  let decision
  const monitoring = config.mode === 'MONITORING'
  try {
    const activity = await activityForHook(hook, config, home)
    if (activity.details.tool_input_omitted && activity.details.tool_input_omitted !== 'metadata_only')
      evaluationError = new Error(`Actera tool inputs unavailable: ${activity.details.tool_input_omitted}`)
    request = evaluationForHook(hook, config, activity)
    await rememberToolDecision(hook, config, request, undefined, home)
    const fingerprint = approvalFingerprint(hook, config)
    decision = monitoring ? undefined : await previousApproval(home, fingerprint, config, request)
    if (!decision) {
      decision = await requestDecision(config, request)
      if (!monitoring) await rememberPendingApproval(home, fingerprint, decision, request)
    }
    if (!monitoring && decision.status === 'PENDING_APPROVAL') decision = await hold(decision)
    await rememberToolDecision(hook, config, request, decision, home)
    output = monitoring ? null : codexToolDecision(decision)
  } catch (error) {
    evaluationError = error
    output = !monitoring && config.onEvaluationError === 'deny' ? codexEvaluationFailure(error) : null
  }
  try {
    if (request && !decision) await enqueueDecision(request, home)
    if (evaluationError) await recordEvaluationError(evaluationError, home)
    await deliverQueued(config, home)
  } catch (error) {
    await recordEvaluationError(error, home).catch(() => {})
  }
  return output
}
