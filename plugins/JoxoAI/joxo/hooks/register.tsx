/**
 * Joxo's live view for Claude Code: a quiet band above the prompt, a pane (`/team`), toasts for
 * what is addressed to this computer, and a small status entry.
 *
 * What this mod does, all of it:
 *  - asks the plugin's own MCP server (the entry in .mcp.json) for the read it draws, and, only when a
 *    person presses Take or Open on web, to claim a task or open the project in the browser. It does that
 *    with $.mcp.call and starts no program itself: no command, no process, no shell. The server is
 *    the one the plugin declares, `joxo mcp --if-paired --channel-only`, started by Claude Code from the
 *    absolute paths `joxo setup` records. Without it the mod has nothing to read and shows nothing.
 *  - draws and toasts what it read, as text.
 *  - remembers which messages it already toasted, in its own $.store.
 *
 * What it never does: read a credential, token, keychain item or environment variable; touch the
 * network (only the joxo command talks to Joxo); write a file outside its own store; add anything
 * to the model's prompt or to a tool call; intercept tool calls. validate lists every call it
 * makes, and that list is short on purpose (see README.md).
 */
import type { EngineInterface, Register, UiPressArgument } from 'claude-code'

import { bandGroups, fitGroups, hasNews, nextDelayMs, paneModel, parsePulse, pickToasts, plain, signature, statusText, summaryLines } from './model.ts'
import type { Reading } from './model.ts'
import { bandView, emptyPaneView, paneView } from './views.tsx'
import type { Actions } from './views.tsx'

const PANE = 'joxo'
const SAFE_ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/

// Module state. A hot reload loses it, and the next look refills it.
let reading: Reading | null = null
let failures = 0
let lastLookAt = 0
let lastActivityAt = 0
let inFlight: Promise<void> | null = null
let hiddenAt: string | null = null
let folder: string | null = null
let toastLog: number[] = []
let timer: { cancel: () => void } | null = null
/** The plugin's own MCP server (the entry in .mcp.json): the one thing the mod talks to. */
const SERVER = 'plugin:joxo:joxo'

/** Ask the plugin's MCP server; a server that is not running, or does not know the call, answers null. */
async function askServer($: EngineInterface, tool: string, args: Readonly<Record<string, unknown>>) {
  const answer = await $.mcp.call(SERVER, tool, args).catch(() => null)
  if (answer === null) return null
  const stdout = answer.content.map(block => (block.type === 'text' ? block.text : '')).join('\n')
  return answer.isError ? { exitCode: 1, stdout: '', stderr: stdout } : { exitCode: 0, stdout, stderr: '' }
}

/** Hold the last good picture when a look fails, marked as stale rather than dropped. */
function afterFailure(previous: Reading | null, reason: string): Reading {
  if (previous?.kind === 'ok') return { kind: 'ok', pulse: { ...previous.pulse, isStale: true } }
  return { kind: 'error', reason }
}

/**
 * One read of the project at a time. A caller that arrives while one is running gets that one's
 * promise, so `/team` waits for the read the session start began instead of answering from nothing
 * ("nothing read yet") when the machine is busy and that first read is still going.
 */
function look($: EngineInterface): Promise<void> {
  if (inFlight !== null) return inFlight
  const running = lookOnce($).finally(() => { if (inFlight === running) inFlight = null })
  inFlight = running
  return running
}

/** One read of the project, then the toasts, the status entry and the next look. */
async function lookOnce($: EngineInterface): Promise<void> {
  let isDormant = false
  try {
    const cwd = await $.session.cwd()
    // No running server (Joxo not set up, a folder that is not paired): nothing to show, and nothing to
    // say about it (no status entry, no "offline") in folders that have nothing to do with Joxo.
    const ran = await askServer($, 'team_view', { dir: cwd })
    lastLookAt = await $.clock.now()
    if (ran === null) {
      reading = reading?.kind === 'ok' ? afterFailure(reading, '') : { kind: 'error', reason: 'Joxo\u2019s server is not running here' }
      isDormant = reading.kind !== 'ok'
      failures += 1
    } else if (ran.exitCode !== 0) {
      failures += 1
      reading = afterFailure(reading, 'joxo could not read the project')
    } else {
      const parsed = parsePulse(ran.stdout)
      if (parsed.kind === 'error') {
        failures += 1
        reading = afterFailure(reading, parsed.reason)
      } else {
        failures = 0
        reading = parsed
        isDormant = parsed.kind === 'unpaired'
        if (parsed.kind === 'ok') {
          folder = parsed.pulse.folder
          const key = `seen:${parsed.pulse.project}`
          const stored = await $.store.get(key)
          const known = Array.isArray(stored) ? stored.filter((id): id is string => typeof id === 'string') : []
          const picked = pickToasts(parsed.pulse, known, { isFirst: stored === undefined, now: lastLookAt, recent: toastLog })
          toastLog = picked.log
          if (stored === undefined || picked.seen.length !== known.length) await $.store.set(key, picked.seen)
          for (const line of picked.toasts) $.ui.toast(line, { timeoutMs: 6000 })
        }
      }
    }
    $.ui.status(isDormant ? undefined : statusText(reading))
    $.ui.invalidate('ui.render')
  } finally {
    timer?.cancel()
    timer = $.clock.after(nextDelayMs({ now: await $.clock.now(), lastActivityAt, failures, isDormant }), () => { void look($) })
  }
}

async function takeTask($: EngineInterface, id: string): Promise<void> {
  if (!SAFE_ID.test(id)) return
  const title = reading?.kind === 'ok' ? reading.pulse.tasks.find(t => t.id === id)?.title : undefined
  const ran = await askServer($, 'team_take', { id, ...(folder === null ? {} : { dir: folder }) })
  if (ran !== null && ran.exitCode === 0) $.ui.toast(`Taken: ${plain(title ?? 'the task', 60)}. It is yours now.`)
  else $.ui.toast(plain(ran?.stderr || ran?.stdout || 'Could not take it right now.', 120) || 'Could not take it right now.')
  await look($)
}

async function openOnWeb($: EngineInterface): Promise<void> {
  const ran = await askServer($, 'team_open', folder === null ? {} : { dir: folder })
  $.ui.toast(ran !== null && ran.exitCode === 0 ? 'Opening Joxo in your browser.' : 'Could not open Joxo in the browser.')
}

function makeActions($: EngineInterface): Actions {
  return {
    take: id => { void takeTask($, id) },
    invite: (press: UiPressArgument) => {
      void $.ui.copy({ text: 'joxo invite --email ', surface: press.surface })
      $.ui.toast('Copied. Add their email, or just tell your agent who to invite.')
    },
    openWeb: () => { void openOnWeb($) },
    refresh: () => { void look($) },
    close: () => { void $.ui.close({ id: PANE }) },
    hide: () => {
      hiddenAt = reading?.kind === 'ok' ? signature(reading.pulse) : null
      $.ui.invalidate('ui.render')
    },
    open: () => { void $.ui.open({ id: PANE, title: 'Joxo', focus: true, closeOnEscape: true }) },
  }
}

/** What to say in a pane that has no picture to draw yet. */
function emptyMessage(): string {
  if (reading === null) return 'Reading your project…'
  if (reading.kind === 'unpaired') return 'This folder is not connected to a Joxo project. Ask your agent to “set up Joxo”.'
  if (reading.kind === 'error') return `Joxo is not reachable from here (${reading.reason}).`
  return ''
}

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    // Not `joxo`: that name is the plugin's own (/joxo:joxo, the setup skill) and Claude Code refuses it.
    await $.command.register({
      name: 'team',
      description: 'Joxo: who is on, who has which task, and what was said',
      immediate: true,
    })
    lastActivityAt = await $.clock.now()
    $.clock.after(50, () => { void look($) })
    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    lastActivityAt = await $.clock.now()
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const now = await $.clock.now()
    lastActivityAt = now
    if (now - lastLookAt > 20_000) $.clock.after(50, () => { void look($) })
    return next(e)
  })

  on('command.run', { command: 'team' }, async $ => {
    const surfaces = await $.session.surfaces()
    if (surfaces.some(s => s === 'terminal' || s === 'desktop')) {
      const opened = await $.ui.open({ id: PANE, title: 'Joxo', focus: true, closeOnEscape: true })
      $.clock.after(50, () => { void look($) })
      if (opened.isPlaced) return {}
    }
    await look($)
    const now = await $.clock.now()
    return { text: summaryLines(reading ?? { kind: 'error', reason: 'nothing read yet' }, now).join('\n') }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || reading?.kind !== 'ok' || !hasNews(reading.pulse) || signature(reading.pulse) === hiddenAt) return next(e)
    const groups = fitGroups(bandGroups(reading.pulse), Math.max(24, e.props.bodyColumns - 20))
    return bandView($.ui.resolve(e), groups, makeActions($))
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const kit = $.ui.resolve(e)
    const actions = makeActions($)
    if (reading?.kind !== 'ok') return emptyPaneView(kit, emptyMessage(), actions)
    const now = await $.clock.now()
    return paneView(kit, paneModel(reading.pulse, now, now - lastLookAt + (reading.pulse.syncAgeMs ?? 0)), actions)
  })
}
