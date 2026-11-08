/**
 * Joxo's colors, taken from the product itself: app/globals.css and desktop/ui/src/styles/tokens.css
 * (charcoal and lime), and the team chat (app/team-panel.css), where lime is people and the agents
 * are amber, and Sentry's cards use the brand's error red. Raw colors, so they read the same in the
 * terminal and in the desktop app.
 *
 * On a terminal the accents are small (a dot, a chip, a name); running text keeps the terminal's own
 * foreground so a light theme stays readable. The desktop avatars sit on their own charcoal tile
 * for the same reason.
 */
export const brand = {
  /** Charcoal: the tile behind an avatar, never a page background. */
  charcoal: '#1d1f20',
  tile: '#262a23',
  /** Lime: people, the Joxo mark, "done". */
  lime: '#d3f49b',
  limeDeep: '#b8e66f',
  /** Ink for text set on lime or amber. */
  ink: '#101309',
  /** Amber: the agents, and anything waiting on a person. */
  amber: '#d9a666',
  amberBright: '#f2c46b',
  /** Sentry's red: a blocker, or Joxo itself out of reach. */
  red: '#e5484d',
  /** Quiet greys: idle and offline. */
  muted: '#96999e',
  faint: '#7f8a77',
} as const

export type Tone = 'brand' | 'name' | 'lime' | 'amber' | 'red' | 'muted' | 'plain'

/** The text color for a tone; `undefined` leaves the surface's own foreground. */
export function toneColor(tone: Tone): string | undefined {
  switch (tone) {
    case 'lime': return brand.limeDeep
    case 'amber': return brand.amber
    case 'red': return brand.red
    case 'muted': return brand.muted
    default: return undefined
  }
}
