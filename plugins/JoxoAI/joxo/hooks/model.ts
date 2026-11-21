/**
 * What the mod knows about the project, and every decision about what to say of it. Pure
 * functions, no engine calls: the hooks in register.tsx fetch and draw, this file reads
 * `joxo pulse --json`, derives the band, the roster, the board and the toasts, and is tested alone.
 *
 * Everything a teammate wrote (names, task titles, messages) is untrusted. `joxo pulse` already
 * clips and cleans it, and `plain` does it again here, including the bidirectional-override
 * characters that can make a line read differently from what it is. It is only ever drawn as text.
 * It never goes near the model's prompt.
 */

import type { Tone } from './theme.ts'

/**
 * Code points that never belong in a line of text: controls, zero-width and invisible fillers, Unicode
 * tag characters (they carry hidden text), variation selectors, and bidirectional overrides.
 */
const UNSAFE_RANGES: readonly (readonly [number, number])[] = [
  [0, 0x1f], [0x7f, 0x9f], [0xad, 0xad], [0x34f, 0x34f], [0x61c, 0x61c], [0x115f, 0x1160], [0x17b4, 0x17b5], [0x180b, 0x180f],
  [0x200b, 0x200f], [0x2028, 0x202e], [0x2060, 0x206f], [0x3164, 0x3164], [0xfe00, 0xfe0f], [0xfeff, 0xfeff], [0xffa0, 0xffa0],
  [0xfff9, 0xfffb], [0xe0000, 0xe007f], [0xe0100, 0xe01ef],
]
const isUnsafe = (code: number): boolean => UNSAFE_RANGES.some(([from, to]) => code >= from && code <= to)

/** One clipped line of untrusted text, safe to draw: NFKC-folded (look-alike forms become plain ones), then stripped. */
export function plain(value: unknown, max: number): string {
  if (typeof value !== 'string') return ''
  let cleaned = ''
  for (const char of value.normalize('NFKC')) cleaned += isUnsafe(char.codePointAt(0) ?? 0) ? ' ' : char
  const text = cleaned.replace(/\s+/g, ' ').trim()
  return text.length > max ? `${text.slice(0, Math.max(1, max - 1)).trimEnd()}…` : text
}

/**
 * A sender's name as drawn: always the name alone, in the one fixed style, never a label of its own. A
 * name that could pass for Joxo or for Claude Code, or that carries the colon of a speaker label, is
 * shown as what it is: somebody's name, marked as a teammate's.
 */
export function displayName(value: unknown, max = 24): string {
  const name = plain(value, max).replace(/[:\u2236\uff1a]+/g, ' ').replace(/\s+/g, ' ').trim()
  if (!name) return 'A teammate'
  return /^(joxo|claude|claude code|anthropic|system|assistant|you|me|owner)$/i.test(name) ? `${name} (a teammate)` : name
}

const ABSOLUTE = /^(\/|[A-Za-z]:[\\/])/
// oxlint-disable-next-line typescript/no-misused-spread -- Only code points below 32 are looked at; splitting is fine.
export const isAbsolute = (value: unknown): value is string => typeof value === 'string' && ABSOLUTE.test(value) && value.length < 1024 && ![...value].some(char => (char.codePointAt(0) ?? 0) < 32)

export type Attention = 'permission' | 'question' | 'finished'
export type Session = { agent: string; folder: string | null; name: string | null; isActive: boolean; attention: Attention | null; lastActiveAt: string | null }
export type Peer = { id: string; name: string; owner: string | null; isOnline: boolean; sessions: Session[] | 'hidden'; workingOn: string | null; lastSeen: string | null }
export type Task = { id: string; title: string; status: string; ownerName: string | null; ownerDeviceId: string | null; isMine: boolean; isLapsed: boolean }
export type Item = { id: string; kind: 'message' | 'handoff' | 'decision' | 'blocker'; from: string; at: string | null; body: string; isUnread: boolean; isFromOwner: boolean }
export type Usage = { label: string; updatedAt: string | null; windows: { name: string; leftPercent: number | null; resetsAt: string | null }[] }
export type Pulse = {
  project: string
  folder: string | null
  isStale: boolean
  isQuiet: boolean
  syncAgeMs: number | null
  unread: number
  self: { name: string; sessions: Session[] }
  peers: Peer[]
  tasks: Task[]
  tasksDone: number
  items: Item[]
  usage: Usage[]
}

export type Reading = { kind: 'ok'; pulse: Pulse } | { kind: 'unpaired' } | { kind: 'error'; reason: string }

type Json = Record<string, unknown>
const isObject = (value: unknown): value is Json => typeof value === 'object' && value !== null && !Array.isArray(value)
const list = (value: unknown): Json[] => (Array.isArray(value) ? value.filter(isObject) : [])
const ATTENTION: readonly string[] = ['permission', 'question', 'finished']
const KINDS: readonly string[] = ['message', 'handoff', 'decision', 'blocker']

function readSession(raw: Json): Session {
  return {
    agent: plain(raw.agent, 30) || 'agent',
    folder: plain(raw.folder, 80) || null,
    name: plain(raw.name, 60) || null,
    isActive: raw.state === 'active',
    attention: typeof raw.attention === 'string' && ATTENTION.includes(raw.attention) ? (raw.attention as Attention) : null,
    lastActiveAt: typeof raw.last_active_at === 'string' ? raw.last_active_at : null,
  }
}

/** The answer of `joxo pulse --json`, read defensively: a shape it does not know is an error, not a guess. */
export function parsePulse(stdout: string): Reading {
  let raw: unknown
  try { raw = JSON.parse(stdout) } catch { return { kind: 'error', reason: 'unreadable answer' } }
  if (!isObject(raw)) return { kind: 'error', reason: 'unreadable answer' }
  if (raw.paired === false) return { kind: 'unpaired' }
  if (raw.version !== 1 || raw.paired !== true) return { kind: 'error', reason: 'a newer Joxo than this mod understands' }
  const project = isObject(raw.project) ? plain(raw.project.name, 40) : ''
  const self = isObject(raw.this_computer) ? raw.this_computer : {}
  return {
    kind: 'ok',
    pulse: {
      project: project || 'Joxo',
      folder: isAbsolute(raw.folder) ? raw.folder : null,
      isStale: raw.stale === true,
      isQuiet: raw.quiet_hours === true,
      syncAgeMs: typeof raw.last_sync_age_ms === 'number' ? raw.last_sync_age_ms : null,
      unread: typeof raw.unread === 'number' && raw.unread > 0 ? Math.floor(raw.unread) : 0,
      self: { name: plain(self.name, 60) || 'This computer', sessions: list(self.sessions).map(readSession) },
      peers: list(raw.peers).map(peer => ({
        id: plain(peer.device_id, 128),
        name: plain(peer.name, 60) || 'A computer',
        owner: plain(peer.owner, 60) ? displayName(peer.owner, 60) : null,
        isOnline: peer.online === true,
        sessions: peer.sessions === 'hidden' ? 'hidden' : list(peer.sessions).map(readSession),
        workingOn: plain(peer.working_on, 120) || null,
        lastSeen: typeof peer.last_seen === 'string' ? peer.last_seen : null,
      })),
      tasks: list(raw.tasks).map(task => ({
        id: plain(task.id, 128),
        title: plain(task.title, 120) || '(untitled)',
        status: plain(task.status, 24) || 'open',
        ownerName: plain(task.owner_name, 60) ? displayName(task.owner_name, 60) : null,
        ownerDeviceId: plain(task.owner_device_id, 128) || null,
        isMine: task.mine === true,
        isLapsed: task.lease_expired === true,
      })).filter(task => task.id),
      tasksDone: typeof raw.tasks_done === 'number' ? raw.tasks_done : 0,
      items: list(raw.events).filter(event => typeof event.kind === 'string' && KINDS.includes(event.kind)).map(event => ({
        id: plain(event.id, 128),
        kind: event.kind as Item['kind'],
        from: displayName(event.from),
        at: typeof event.at === 'string' ? event.at : null,
        body: plain(event.body, 240),
        isUnread: event.unread === true,
        isFromOwner: event.from_owner === true,
      })).filter(item => item.id),
      usage: list(raw.accounts).map(account => ({
        label: plain(account.label, 40) || 'this computer',
        updatedAt: typeof account.updated_at === 'string' ? account.updated_at : null,
        windows: list(account.windows).map(window => ({
          name: plain(window.name, 40) || 'window',
          leftPercent: typeof window.left_percent === 'number' ? window.left_percent : null,
          resetsAt: typeof window.resets_at === 'string' ? window.resets_at : null,
        })),
      })),
    },
  }
}

// ---- presence --------------------------------------------------------------------------------

/** waiting: an agent there waits on a person. working: one is running. online: connected, idle. */
export type Presence = 'waiting' | 'working' | 'online' | 'offline'
const RANK: Record<Presence, number> = { waiting: 3, working: 2, online: 1, offline: 0 }

export function presenceOf(peer: Peer): Presence {
  if (!peer.isOnline) return 'offline'
  const sessions = Array.isArray(peer.sessions) ? peer.sessions : []
  if (sessions.some(s => s.attention === 'permission' || s.attention === 'question')) return 'waiting'
  if (peer.workingOn || sessions.some(s => s.isActive && s.attention !== 'finished')) return 'working'
  return 'online'
}

export type Person = { name: string; presence: Presence; computers: Peer[] }

/** Computers grouped under the person who owns them, the busiest person first, then by name. */
export function peopleOf(pulse: Pulse): Person[] {
  const byKey = new Map<string, Person>()
  for (const peer of pulse.peers) {
    const name = peer.owner ?? peer.name
    const key = name.toLowerCase()
    const found = byKey.get(key)
    const presence = presenceOf(peer)
    if (!found) byKey.set(key, { name, presence, computers: [peer] })
    else byKey.set(key, { ...found, presence: RANK[presence] > RANK[found.presence] ? presence : found.presence, computers: [...found.computers, peer] })
  }
  return [...byKey.values()].sort((a, b) => RANK[b.presence] - RANK[a.presence] || a.name.localeCompare(b.name))
}

export function initialsOf(name: string): string {
  const words = name.split(/[\s._-]+/).filter(Boolean)
  const letters = (words.length > 1 ? `${words[0]?.[0] ?? ''}${words[1]?.[0] ?? ''}` : (words[0] ?? '').slice(0, 2)).replace(/[^A-Za-z0-9]/g, '')
  return letters ? letters.toUpperCase() : '·'
}

const AGENT_LABELS: Record<string, string> = { 'claude-code': 'Claude Code', claude: 'Claude Code', codex: 'Codex', cursor: 'Cursor', opencode: 'OpenCode', gemini: 'Gemini CLI', 'gemini-cli': 'Gemini CLI' }
export function agentLabel(agent: string): string {
  return AGENT_LABELS[agent] ?? (agent.replace(/[-_]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || 'Agent')
}

// ---- time ------------------------------------------------------------------------------------

export function ago(iso: string | null, now: number): string {
  const at = iso ? Date.parse(iso) : NaN
  if (!Number.isFinite(at)) return ''
  const seconds = Math.max(0, Math.round((now - at) / 1000))
  if (seconds < 45) return 'now'
  if (Math.round(seconds / 60) < 60) return `${Math.max(1, Math.round(seconds / 60))}m`
  if (Math.round(seconds / 3600) < 24) return `${Math.round(seconds / 3600)}h`
  return `${Math.round(seconds / 86_400)}d`
}

/** "Sun 22:00" or "in 3h": when a usage window resets, short. */
export function resetsIn(iso: string | null, now: number): string {
  const at = iso ? Date.parse(iso) : NaN
  if (!Number.isFinite(at) || at <= now) return ''
  const minutes = Math.round((at - now) / 60_000)
  if (minutes < 60) return `in ${minutes}m`
  if (Math.round(minutes / 60) < 48) return `in ${Math.round(minutes / 60)}h`
  return `in ${Math.round(minutes / 1440)}d`
}

// ---- the band --------------------------------------------------------------------------------

export type Seg = { text: string; tone: Tone; isBold?: boolean }
export type Group = { rank: number; segs: Seg[] }

const claimedCount = (pulse: Pulse) => pulse.tasks.filter(t => t.ownerDeviceId && !t.isLapsed).length
const mineCount = (pulse: Pulse) => pulse.tasks.filter(t => t.isMine).length

/** The tightest window the headline account has, when it is low enough to be worth a word. */
export function lowUsage(pulse: Pulse): { label: string; window: string; leftPercent: number } | null {
  let worst: { label: string; window: string; leftPercent: number } | null = null
  for (const account of pulse.usage) {
    for (const window of account.windows) {
      if (window.leftPercent === null || window.leftPercent > 25) continue
      if (!worst || window.leftPercent < worst.leftPercent) worst = { label: account.label, window: window.name, leftPercent: window.leftPercent }
    }
  }
  return worst
}

/** Is there anything to say? A band with nothing to say is no band. */
export function hasNews(pulse: Pulse): boolean {
  return pulse.unread > 0 || mineCount(pulse) > 0 || peopleOf(pulse).some(p => p.presence === 'working' || p.presence === 'waiting') || lowUsage(pulse) !== null
}

/** What would make a dismissed band come back: it changed in a way someone would care about. */
export function signature(pulse: Pulse): string {
  return JSON.stringify([pulse.unread, peopleOf(pulse).filter(p => p.presence === 'working' || p.presence === 'waiting').map(p => `${p.name}:${p.presence}`), claimedCount(pulse), mineCount(pulse), lowUsage(pulse)?.window ?? null])
}

/** The band's line as groups, most important first (lowest rank). */
export function bandGroups(pulse: Pulse): Group[] {
  const groups: Group[] = [{ rank: 0, segs: [{ text: ' Joxo ', tone: 'brand', isBold: true }, { text: ` ${plain(pulse.project, 24)}`, tone: 'name', isBold: true }] }]
  if (pulse.isStale) groups.push({ rank: 1, segs: [{ text: '○ can’t reach Joxo, showing the last it saw', tone: 'red' }] })
  const people = peopleOf(pulse)
  const working = people.filter(p => p.presence === 'working')
  const waiting = people.filter(p => p.presence === 'waiting')
  const named = (list: Person[], tone: Seg['tone'], word: string, rank: number): Group => {
    const shown = list.slice(0, 2)
    const segs: Seg[] = shown.flatMap((p, i) => [
      { text: `${i ? ', ' : ''}● `, tone },
      { text: plain(p.name, 14), tone: 'plain' as const },
    ])
    if (list.length > shown.length) segs.push({ text: ` +${list.length - shown.length}`, tone: 'muted' })
    segs.push({ text: ` ${word}`, tone: 'muted' })
    return { rank, segs }
  }
  if (working.length) groups.push(named(working, 'lime', 'working', 1))
  if (waiting.length) groups.push(named(waiting, 'amber', 'waiting', 2))
  if (!working.length && !waiting.length) {
    const online = pulse.peers.filter(p => p.isOnline).length
    if (online) groups.push({ rank: 3, segs: [{ text: `○ ${online} online`, tone: 'muted' }] })
  }
  const claimed = claimedCount(pulse)
  if (claimed) groups.push({ rank: 3, segs: [{ text: `${claimed} task${claimed === 1 ? '' : 's'} claimed`, tone: 'muted' }] })
  if (pulse.unread) groups.push({ rank: 1, segs: [{ text: `${pulse.unread} for you`, tone: 'lime', isBold: true }] })
  else if (mineCount(pulse)) groups.push({ rank: 2, segs: [{ text: `${mineCount(pulse)} of yours`, tone: 'lime' }] })
  const low = lowUsage(pulse)
  if (low) groups.push({ rank: 2, segs: [{ text: `${low.window} ${Math.round(low.leftPercent)}% left (${plain(low.label, 14)})`, tone: 'amber' }] })
  return groups
}

const lengthOf = (groups: Group[]) => groups.reduce((sum, g, i) => sum + (i ? 3 : 0) + g.segs.reduce((n, s) => n + s.text.length, 0), 0)

/** Keep the most important groups that fit `columns` (room kept for the buttons), in their order. */
export function fitGroups(groups: Group[], columns: number): Group[] {
  let kept = groups
  while (kept.length > 1 && lengthOf(kept) > columns) {
    const worst = Math.max(...kept.map(g => g.rank))
    if (worst === 0) break
    const last = [...kept].reverse().find(g => g.rank === worst)
    kept = kept.filter(g => g !== last)
  }
  return kept
}

/** The same line as plain text (tests, status line, surfaces that draw nothing). */
export function bandText(pulse: Pulse, columns = 200): string {
  return fitGroups(bandGroups(pulse), columns).map(g => g.segs.map(s => s.text).join('').replace(/ {2,}/g, ' ').trim()).join(' · ')
}

/** The status entry: compact, and different from the statusline command's usage segment. */
export function statusText(reading: Reading | null): string | undefined {
  // Never in a folder with no Joxo, and never for a failure before Joxo has been seen once.
  if (!reading || reading.kind !== 'ok') return undefined
  const { pulse } = reading
  if (pulse.isStale) return 'Joxo ○ offline'
  const on = peopleOf(pulse).filter(p => p.presence !== 'offline').length
  return `Joxo ● ${on}${pulse.unread ? ` · ${pulse.unread} new` : ''}`
}

// ---- toasts ----------------------------------------------------------------------------------

export const SEEN_KEEP = 200
const FRESH_MS = 30 * 60_000
/** At most this many toasts in any five minutes, and one per sender: a flood is one line, not a stream. */
export const TOAST_WINDOW_MS = 5 * 60_000
export const TOAST_MAX = 3

/**
 * Which new messages and handoffs deserve a toast, once each. The first reading of a project only
 * learns what is already there (`isFirst`), and quiet hours learn without speaking. `recent` is the
 * times of toasts already shown; the answer's `log` is its next value. A sender is toasted once per
 * window and at most three toasts appear per window; what is held back is counted in one line.
 */
export function pickToasts(pulse: Pulse, seen: readonly string[], opts: { isFirst: boolean; now: number; recent?: readonly number[] }): { toasts: string[]; seen: string[]; log: number[] } {
  const known = new Set(seen)
  const fresh = pulse.items.filter(item => (item.kind === 'message' || item.kind === 'handoff') && !known.has(item.id))
  const nextSeen = [...seen, ...fresh.map(item => item.id)].slice(-SEEN_KEEP)
  const log = (opts.recent ?? []).filter(at => opts.now - at < TOAST_WINDOW_MS)
  if (opts.isFirst || pulse.isQuiet) return { toasts: [], seen: nextSeen, log }
  const recent = fresh.filter(item => { const at = item.at ? Date.parse(item.at) : NaN; return !Number.isFinite(at) || opts.now - at <= FRESH_MS }).reverse()
  const room = Math.max(0, TOAST_MAX - log.length)
  const senders = new Set<string>()
  const shown: Item[] = []
  for (const item of recent) {
    if (shown.length >= room || senders.has(item.from)) continue
    senders.add(item.from)
    shown.push(item)
  }
  const held = recent.length - shown.length
  const lines = shown.map(item => (item.kind === 'handoff' ? `${item.from} handed off: ${plain(item.body, 90)}` : `${item.from} wrote: “${plain(item.body, 100)}”`))
  if (held > 0 && lines.length) lines.push(`and ${held} more from your team`)
  return { toasts: lines, seen: nextSeen, log: [...log, ...shown.map(() => opts.now)] }
}

// ---- polling ---------------------------------------------------------------------------------

/**
 * How long to wait before the next look: gentle, slower when idle, backing off on failure. Where Joxo is
 * not set up (not paired, not installed, not recorded) it looks twice an hour, to notice a pairing.
 */
export function nextDelayMs(input: { now: number; lastActivityAt: number; failures: number; isDormant: boolean }): number {
  if (input.isDormant) return 30 * 60_000
  const idle = input.now - input.lastActivityAt
  const base = idle < 10 * 60_000 ? 30_000 : idle < 60 * 60_000 ? 90_000 : 180_000
  return Math.min(10 * 60_000, base * 2 ** Math.min(input.failures, 4))
}

// ---- the pane's rows -------------------------------------------------------------------------

export type SessionRow = { agent: string; where: string | null; state: 'working' | 'waiting' | 'idle'; note: string }
export type ComputerRow = { name: string; presence: Presence; sessions: SessionRow[] | 'hidden'; workingOn: string | null; seen: string }
export type PersonRow = { name: string; initials: string; presence: Presence; computers: ComputerRow[] }
export type BoardRow = { id: string; title: string; state: 'mine' | 'claimed' | 'lapsed' | 'open'; holder: string | null; canTake: boolean }
export type EventRow = { id: string; kind: Item['kind']; from: string; when: string; body: string; isUnread: boolean }
export type UsageRow = { label: string; reported: string; parts: { name: string; leftPercent: number | null; resets: string }[] }
export type PaneModel = { project: string; syncNote: string; isStale: boolean; people: PersonRow[]; selfLine: string; board: BoardRow[]; boardCounts: { open: number; claimed: number; mine: number; done: number }; events: EventRow[]; usage: UsageRow[] }

function sessionRow(session: Session, now: number): SessionRow {
  const state: SessionRow['state'] = session.attention === 'permission' || session.attention === 'question' ? 'waiting' : session.isActive && session.attention !== 'finished' ? 'working' : 'idle'
  const note = state === 'waiting' ? 'waiting on a person' : state === 'working' ? 'working' : `idle ${ago(session.lastActiveAt, now)}`.trim()
  return { agent: session.name ?? agentLabel(session.agent), where: session.folder, state, note }
}

export function paneModel(pulse: Pulse, now: number, syncAgeMs: number | null): PaneModel {
  const people: PersonRow[] = peopleOf(pulse).map(person => ({
    name: person.name,
    initials: initialsOf(person.name),
    presence: person.presence,
    computers: person.computers.map(peer => ({
      name: peer.name,
      presence: presenceOf(peer),
      sessions: peer.sessions === 'hidden' ? 'hidden' : peer.sessions.map(s => sessionRow(s, now)),
      workingOn: peer.workingOn,
      seen: peer.isOnline ? '' : `seen ${ago(peer.lastSeen, now)}`.trim(),
    })),
  }))
  const computerOf = new Map(pulse.peers.map(p => [p.id, p.name]))
  const rank = { mine: 0, claimed: 1, lapsed: 2, open: 3 } as const
  const board: BoardRow[] = pulse.tasks.map(task => {
    const state: BoardRow['state'] = task.isMine ? 'mine' : task.isLapsed ? 'lapsed' : task.ownerDeviceId ? 'claimed' : 'open'
    const computer = task.ownerDeviceId ? computerOf.get(task.ownerDeviceId) : undefined
    const holder = task.isMine ? null : task.ownerName ? `${task.ownerName}${computer && computer !== task.ownerName ? ` · ${computer}` : ''}` : null
    return { id: task.id, title: task.title, state, holder, canTake: state === 'open' || state === 'lapsed' }
  }).sort((a, b) => rank[a.state] - rank[b.state])
  const sessions = pulse.self.sessions.length
  return {
    project: pulse.project,
    isStale: pulse.isStale,
    syncNote: pulse.isStale ? 'can’t reach Joxo, showing the last it saw' : syncAgeMs === null ? '' : syncAgeMs < 45_000 ? 'live' : `updated ${ago(new Date(now - syncAgeMs).toISOString(), now)} ago`,
    people,
    selfLine: `${pulse.self.name} · ${sessions} other agent session${sessions === 1 ? '' : 's'} here`,
    board,
    boardCounts: { open: board.length, claimed: board.filter(r => r.state === 'claimed' || r.state === 'lapsed').length, mine: board.filter(r => r.state === 'mine').length, done: pulse.tasksDone },
    events: pulse.items.slice(0, 8).map(item => ({ id: item.id, kind: item.kind, from: item.from, when: ago(item.at, now), body: item.body, isUnread: item.isUnread })),
    usage: pulse.usage.map(u => ({ label: u.label, reported: u.updatedAt ? `reported ${ago(u.updatedAt, now)}${ago(u.updatedAt, now) === 'now' ? '' : ' ago'}` : '', parts: u.windows.map(w => ({ name: w.name, leftPercent: w.leftPercent, resets: resetsIn(w.resetsAt, now) })) })),
  }
}

/** The whole picture as plain lines, for a surface that draws nothing (`claude -p`, VS Code, a phone). */
export function summaryLines(reading: Reading, now: number): string[] {
  if (reading.kind === 'unpaired') return ['This folder is not connected to a Joxo project. Say “set up Joxo” to your agent.']
  if (reading.kind === 'error') return [`Joxo could not be read (${reading.reason}).`]
  const model = paneModel(reading.pulse, now, null)
  const lines = [`Joxo · ${model.project}${model.isStale ? ' (offline, last known)' : ''}`]
  for (const person of model.people) lines.push(`${person.presence === 'offline' ? '○' : '●'} ${person.name}: ${person.presence}${person.computers[0]?.workingOn ? `, on “${person.computers[0].workingOn}”` : ''}`)
  if (!model.people.length) lines.push('No teammates yet. Say “invite <email> to Joxo” to your agent.')
  for (const row of model.board) lines.push(`task ${row.state}: ${row.title}${row.holder ? ` (${row.holder})` : ''}`)
  if (reading.pulse.unread) lines.push(`${reading.pulse.unread} waiting for you`)
  for (const usage of model.usage) lines.push(`usage ${usage.label}: ${usage.parts.map(p => `${p.name} ${p.leftPercent === null ? '?' : `${Math.round(p.leftPercent)}%`} left`).join(', ')}`)
  return lines
}
