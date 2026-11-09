/**
 * How the band and the pane look. Pure drawing: each function takes the surface's element kit
 * (`$.ui.resolve(e)`), the model from model.ts and a set of actions, and returns a tree. No engine
 * calls live here, so the same trees are drawn in the terminal, in the desktop app and in tests.
 *
 * Design: Joxo's own language (theme.ts). People are lime, the agents are amber, a blocker or an
 * unreachable Joxo is red, idle and offline are quiet grey. Plain words, no boxes inside boxes:
 * sections are separated by space and a small caps heading, never by frames. Where the surface has
 * `Svg` (the desktop app, VS Code, mobile) people get an avatar tile with a presence dot; the
 * terminal gets the same facts in glyphs. Anything a teammate wrote is a Text child: text, never
 * markup, and never a prompt.
 */
import type { UiPressArgument } from 'claude-code'

import { plain } from './model.ts'
import type { BoardRow, ComputerRow, EventRow, Group, PaneModel, PersonRow, Presence, SessionRow, UsageRow } from './model.ts'
import { brand, toneColor } from './theme.ts'

// The kit is the surface's table; each element is called with props, the way JSX does.
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- one call shape for every surface's table
type Part = (props: any) => any
export type Kit = { Box: Part; Text: Part; Button: Part; Svg?: Part }

export type Actions = {
  take: (taskId: string) => void
  invite: (press: UiPressArgument) => void
  openWeb: () => void
  refresh: () => void
  close: () => void
  hide: () => void
  open: () => void
}

const PRESENCE_WORD: Record<Presence, string> = { waiting: 'waiting on a person', working: 'working', online: 'online', offline: 'offline' }
const PRESENCE_COLOR: Record<Presence, string> = { waiting: brand.amber, working: brand.limeDeep, online: brand.faint, offline: brand.muted }

// ---- the band --------------------------------------------------------------------------------

/** One quiet line above the prompt, and the two buttons that act on it. */
export function bandView(kit: Kit, groups: Group[], actions: Actions) {
  const { Box, Text, Button } = kit
  const parts = groups.flatMap((group, index) => [
    ...(index ? [<Text key={`sep${index}`} color={brand.muted}>{' · '}</Text>] : []),
    ...group.segs.map((seg, i) => seg.tone === 'brand'
      ? <Text key={`g${index}s${i}`} backgroundColor={brand.lime} color={brand.ink} bold>{seg.text}</Text>
      : <Text key={`g${index}s${i}`} color={toneColor(seg.tone)} bold={seg.isBold === true}>{seg.text}</Text>),
  ])
  return (
    <Box flexDirection="row" columnGap={2}>
      <Box flexDirection="row" flexShrink={1}>{parts}</Box>
      <Button key="open" label="Open" hotkey="o" plain onPress={actions.open} />
      <Button key="hide" label="Hide" hotkey="h" plain dimColor onPress={actions.hide} />
    </Box>
  )
}

// ---- small pieces ----------------------------------------------------------------------------

function heading(kit: Kit, text: string, note?: string) {
  const { Box, Text } = kit
  return (
    <Box flexDirection="row" columnGap={2} marginTop={1}>
      <Text bold color={brand.muted}>{text.toUpperCase()}</Text>
      {note ? <Text color={brand.muted} dimColor>{note}</Text> : null}
    </Box>
  )
}

/** The avatar tile of the desktop pane: initials on charcoal, a presence dot in the corner. */
export function avatarSvg(initials: string, presence: Presence): string {
  const letters = initials.replace(/[^A-Za-z0-9·]/g, '').slice(0, 2) || '·'
  const dot = PRESENCE_COLOR[presence]
  const ring = presence === 'offline' ? `fill="none" stroke="${dot}" stroke-width="1.6"` : `fill="${dot}" stroke="${brand.charcoal}" stroke-width="2"`
  return `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36"><rect width="36" height="36" rx="11" fill="${brand.tile}"/><text x="18" y="23" text-anchor="middle" font-family="system-ui, sans-serif" font-size="14" font-weight="600" fill="${presence === 'offline' ? brand.muted : brand.lime}">${letters}</text><circle cx="30" cy="30" r="5" ${ring}/></svg>`
}

function sessionLine(kit: Kit, session: SessionRow) {
  const { Box, Text } = kit
  const glyph = session.state === 'idle' ? '◇' : '◆'
  const color = session.state === 'waiting' ? brand.amberBright : session.state === 'working' ? brand.amber : brand.muted
  return (
    <Box flexDirection="row" columnGap={1} paddingLeft={4}>
      <Text color={color}>{glyph}</Text>
      <Text>{`${session.agent}${session.where ? ` in ${session.where}` : ''}`}</Text>
      <Text color={brand.muted}>{session.note}</Text>
    </Box>
  )
}

function computerLines(kit: Kit, computer: ComputerRow) {
  const { Box, Text } = kit
  const count = computer.sessions === 'hidden' ? 'agents hidden by its owner' : `${computer.sessions.length} agent${computer.sessions.length === 1 ? '' : 's'}`
  return (
    <Box flexDirection="column">
      <Box flexDirection="row" columnGap={1} paddingLeft={2}>
        <Text color={brand.muted}>{`${computer.name} · ${computer.presence === 'offline' ? computer.seen : count}`}</Text>
      </Box>
      {computer.workingOn ? (
        <Box flexDirection="row" columnGap={1} paddingLeft={4}>
          <Text color={brand.amber}>▸</Text>
          <Text>{`on “${computer.workingOn}”`}</Text>
        </Box>
      ) : null}
      {Array.isArray(computer.sessions) ? computer.sessions.map(session => sessionLine(kit, session)) : null}
    </Box>
  )
}

function personGlyphRow(kit: Kit, person: PersonRow) {
  const { Box, Text } = kit
  const dot = person.presence === 'offline' ? '○' : '●'
  return (
    <Box flexDirection="column">
      <Box flexDirection="row" columnGap={1}>
        <Text color={PRESENCE_COLOR[person.presence]}>{dot}</Text>
        <Text bold>{person.name}</Text>
        <Text color={PRESENCE_COLOR[person.presence]}>{PRESENCE_WORD[person.presence]}</Text>
      </Box>
      {person.computers.map(computer => computerLines(kit, computer))}
    </Box>
  )
}

function personRow(kit: Kit, person: PersonRow) {
  const { Box, Text, Svg } = kit
  if (!Svg) return personGlyphRow(kit, person)
  return (
    <Box flexDirection="row" columnGap={2} alignItems="flex-start" marginTop={1}>
      <Svg source={avatarSvg(person.initials, person.presence)} alt={`${person.name}, ${PRESENCE_WORD[person.presence]}`} width={36} height={36} />
      <Box flexDirection="column" flexGrow={1}>
        <Box flexDirection="row" columnGap={2}>
          <Text bold>{person.name}</Text>
          <Text color={PRESENCE_COLOR[person.presence]}>{PRESENCE_WORD[person.presence]}</Text>
        </Box>
        {person.computers.map(computer => computerLines(kit, computer))}
      </Box>
    </Box>
  )
}

const STATE_TEXT: Record<BoardRow['state'], string> = { mine: 'yours', claimed: 'claimed', lapsed: 'lease lapsed', open: 'open' }
const STATE_COLOR: Record<BoardRow['state'], string | undefined> = { mine: brand.limeDeep, claimed: undefined, lapsed: brand.amber, open: brand.muted }

function boardLine(kit: Kit, row: BoardRow, actions: Actions) {
  const { Box, Text, Button } = kit
  return (
    <Box flexDirection="row" columnGap={2}>
      <Box flexDirection="row" columnGap={1} flexGrow={1} flexShrink={1}>
        <Text color={STATE_COLOR[row.state]}>{row.state === 'open' ? '○' : '●'}</Text>
        <Text wrap="truncate-end">{row.title}</Text>
      </Box>
      <Text color={STATE_COLOR[row.state]}>{row.holder ? `${STATE_TEXT[row.state]} · ${row.holder}` : STATE_TEXT[row.state]}</Text>
      {row.canTake ? <Button key={`take-${row.id}`} label="Take" variant="primary" onPress={() => actions.take(row.id)} /> : null}
    </Box>
  )
}

const KIND_COLOR: Record<EventRow['kind'], string | undefined> = { message: brand.muted, handoff: brand.limeDeep, decision: brand.amber, blocker: brand.red }

function eventLine(kit: Kit, row: EventRow) {
  const { Box, Text } = kit
  return (
    <Box flexDirection="column" marginBottom={1}>
      <Box flexDirection="row" columnGap={1}>
        <Text color={row.isUnread ? brand.limeDeep : brand.muted}>{row.isUnread ? '●' : '○'}</Text>
        <Text bold>{row.from}</Text>
        <Text color={KIND_COLOR[row.kind]}>{row.kind}</Text>
        <Text color={brand.muted}>{row.when}</Text>
      </Box>
      <Box paddingLeft={2}><Text wrap="wrap">{plain(row.body, 160)}</Text></Box>
    </Box>
  )
}

function usageLine(kit: Kit, row: UsageRow) {
  const { Box, Text } = kit
  return (
    <Box flexDirection="row" columnGap={2}>
      <Text bold>{row.label}</Text>
      {row.parts.map((part, i) => (
        <Text key={`p${i}`} color={part.leftPercent !== null && part.leftPercent <= 10 ? brand.red : part.leftPercent !== null && part.leftPercent <= 25 ? brand.amber : undefined}>
          {`${part.name} ${part.leftPercent === null ? 'not shared' : `${Math.round(part.leftPercent)}% left`}${part.resets ? ` · resets ${part.resets}` : ''}`}
        </Text>
      ))}
      {row.reported ? <Text color={brand.muted} dimColor>{row.reported}</Text> : null}
    </Box>
  )
}

// ---- the pane --------------------------------------------------------------------------------

/** The full roster, the board, what was said, usage, and the things you can do. */
export function paneView(kit: Kit, model: PaneModel, actions: Actions) {
  const { Box, Text, Button } = kit
  const counts = model.boardCounts
  const boardNote = `${counts.open} open · ${counts.claimed} claimed · ${counts.mine} yours${counts.done ? ` · ${counts.done} done` : ''}`
  const people = model.people.length
    ? model.people.map(person => personRow(kit, person))
    : [<Text key="nobody" color={brand.muted}>Nobody else is connected yet.</Text>]
  const board = model.board.length
    ? model.board.map(row => boardLine(kit, row, actions))
    : [<Text key="notasks" color={brand.muted}>No open tasks.</Text>]
  const events = model.events.length
    ? model.events.map(row => eventLine(kit, row))
    : [<Text key="nothing" color={brand.muted}>Nothing yet.</Text>]
  return (
    <Box flexDirection="column" paddingX={1}>
      <Box flexDirection="row" columnGap={2}>
        <Text backgroundColor={brand.lime} color={brand.ink} bold>{' Joxo '}</Text>
        <Text bold>{model.project}</Text>
        <Text color={model.isStale ? brand.red : brand.muted}>{`${model.isStale ? '○' : '●'} ${model.syncNote}`}</Text>
      </Box>
      {heading(kit, 'Team')}
      {people}
      <Box marginTop={1}><Text color={brand.muted} dimColor>{model.selfLine}</Text></Box>
      {heading(kit, 'Board', boardNote)}
      {board}
      {heading(kit, 'Recent')}
      {events}
      {model.usage.length ? heading(kit, 'Your usage', 'this computer') : null}
      {model.usage.map(row => usageLine(kit, row))}
      {heading(kit, 'Invite')}
      <Text color={brand.muted}>Tell your agent “invite name@email to Joxo”, or run joxo invite.</Text>
      <Box flexDirection="row" columnGap={2} marginTop={1}>
        <Button key="invite" label="Copy invite command" hotkey="i" onPress={actions.invite} />
        <Button key="web" label="Open on web" hotkey="w" onPress={actions.openWeb} />
        <Button key="refresh" label="Refresh" hotkey="r" dimColor onPress={actions.refresh} />
        {/* oxlint-disable-next-line jsx-a11y/aria-role -- `role` is this Button's own prop (dismiss), not an ARIA role. */}
        <Button key="close" label="Close" role="dismiss" hotkey="x" dimColor onPress={actions.close} />
      </Box>
    </Box>
  )
}

/** The pane before Joxo is reachable: say what to do, in words. */
export function emptyPaneView(kit: Kit, message: string, actions: Actions) {
  const { Box, Text, Button } = kit
  return (
    <Box flexDirection="column" paddingX={1}>
      <Box flexDirection="row" columnGap={2}>
        <Text backgroundColor={brand.lime} color={brand.ink} bold>{' Joxo '}</Text>
        <Text>{message}</Text>
      </Box>
      <Box flexDirection="row" columnGap={2} marginTop={1}>
        <Button key="refresh" label="Try again" hotkey="r" onPress={actions.refresh} />
        {/* oxlint-disable-next-line jsx-a11y/aria-role -- `role` is this Button's own prop (dismiss), not an ARIA role. */}
        <Button key="close" label="Close" role="dismiss" hotkey="x" dimColor onPress={actions.close} />
      </Box>
    </Box>
  )
}
