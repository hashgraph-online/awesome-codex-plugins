import { reviewDecision, reviewerLinkStatus, startReviewerLink } from '../../core/bridge.mjs'
import { holdForApproval } from './bridge.mjs'

// Review in Codex: while a call is held, the person who linked Codex to their
// Actera account can approve or deny it in a Codex prompt (an MCP elicitation)
// instead of in Actera. Actera still checks that they may review it. The hold
// keeps polling meanwhile, so a review in Actera, Slack or email still decides
// it and closes the prompt. A prompt Codex cannot show, or one the person
// dismisses, ends the hold at once with the review link.

function readableName(value) {
  return String(value || '')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_\-.]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase()
}

const actionVerbs = new Set([
  'add', 'archive', 'cancel', 'create', 'delete', 'edit', 'execute', 'export',
  'invite', 'post', 'publish', 'remove', 'rename', 'run', 'send', 'share',
  'submit', 'transfer', 'update', 'upload', 'write',
])

function actionName(tool) {
  // MCP server names can be opaque, installation-specific IDs. The operation
  // suffix is the part a reviewer can use to recognize the requested action.
  const operation = tool.startsWith('mcp__') ? tool.split('__').slice(2).join('__') : tool
  const words = readableName(operation).split(' ').filter(Boolean)
  const verbIndex = words.findIndex((word) => actionVerbs.has(word))
  if (verbIndex > 0) {
    const source = words.slice(0, verbIndex).join(' ').replace(/^./, (letter) => letter.toUpperCase())
    return `${words.slice(verbIndex).join(' ')} via ${source}`
  }
  if (verbIndex === 0) return words.join(' ')
  return words.length ? `use ${words.join(' ')}` : 'use a tool'
}

function fieldLabel(key) {
  return readableName(key)
    .replace(/^./, (letter) => letter.toUpperCase())
    .replace(/\b(id|api|url)\b/gi, (word) => word.toUpperCase())
}

export function reviewQuestion(tool, input) {
  const lines = [`Allow Codex to ${actionName(String(tool || ''))}?`]
  if (input && typeof input === 'object' && !Array.isArray(input)) {
    let shown = 0
    let omitted = 0
    for (const [key, value] of Object.entries(input)) {
      if (shown >= 4 || value === null || typeof value === 'object') {
        omitted++
        continue
      }
      const secret = /(?:secret|password|token|credential|api.?key|authorization)/i.test(key)
      const raw = secret ? '(hidden)' : String(value).replace(/\s+/g, ' ').trim()
      lines.push(`${fieldLabel(key)}: ${raw.length > 180 ? `${raw.slice(0, 180)}…` : raw}`)
      shown++
    }
    if (omitted) lines.push('Additional details are in the tool request.')
  }
  lines.push('Actera will record your choice. Review the full tool request before allowing it.')
  return lines.join('\n')
}

async function choose(ask, message, options, signal) {
  const answer = await ask({
    mode: 'form',
    message,
    requestedSchema: {
      type: 'object',
      properties: { choice: { type: 'string', title: 'Choice', enum: options.map(([value]) => value), enumNames: options.map(([, title]) => title) } },
      required: ['choice'],
    },
  }, signal)
  return answer?.action === 'accept' ? answer.content?.choice : undefined
}

async function linked(config, home) {
  try { return (await reviewerLinkStatus(config, home)).linked } catch { return false }
}

// Returns 'approve', 'reject' or 'wait' (the person chose to wait for a
// reviewer elsewhere), or undefined when no one answered here. Codex declines
// at once a prompt it cannot show (approval policy "never", codex exec), and a
// person who dismisses the prompt declines it too.
async function askInCodex(config, home, hook, { ask, openBrowser, signal }) {
  if (!(await linked(config, home))) {
    const wanted = await choose(ask, 'Actera is holding this tool call for a reviewer. Link Codex to your Actera account to review it here, or wait for a reviewer in Actera.', [
      ['link', 'Link my Actera account'],
      ['wait', 'Wait for a reviewer'],
    ], signal)
    if (wanted !== 'link' || signal.aborted) return wanted
    const link = await startReviewerLink(config, home)
    openBrowser(link.browserUrl)
    const done = await choose(ask, `Finish linking in the Actera page that just opened, then continue here. If it did not open, visit ${link.browserUrl}`, [
      ['continue', 'Continue'],
      ['wait', 'Wait for a reviewer'],
    ], signal)
    if (done !== 'continue' || signal.aborted) return done
    if (!(await linked(config, home))) return undefined
  }
  return choose(ask, reviewQuestion(hook.tool_name, hook.tool_input), [
    ['approve', 'Allow once'],
    ['reject', 'Deny'],
  ], signal)
}

export async function holdWithReview(config, decision, home, hook, { holdMs, pollMs, ask, openBrowser }) {
  const controller = new AbortController()
  const held = holdForApproval(config, decision, home, { holdMs, pollMs, signal: controller.signal })
  const asked = askInCodex(config, home, hook, { ask, openBrowser, signal: controller.signal }).catch(() => undefined)
  const first = await Promise.race([
    held.then((current) => ({ current })),
    asked.then((choice) => (choice === 'wait' ? held.then((current) => ({ current })) : { choice })),
  ])
  controller.abort() // Closes an open prompt or stops the hold.
  if (first.current) return first.current
  // Unanswered here: end the hold now so the agent can say where to review it,
  // instead of waiting silently. A retry reuses this Decision.
  if (!first.choice) return { ...decision, unansweredInCodex: true }
  try {
    const reviewed = await reviewDecision(config, decision.id, first.choice, { home, idempotencyPrefix: 'codex-native', rejectReason: 'Declined in Codex' })
    return { ...decision, ...reviewed, reviewedIn: 'codex' }
  } catch (error) {
    return { ...decision, status: 'REVIEW_FAILED', explanation: error.message }
  }
}
