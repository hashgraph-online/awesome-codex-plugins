/**
 * What a playtest's readings mean. Everything here is plain arithmetic on what the browsers reported: no browser, no
 * clock, no file. The script (playtest.mjs) gathers; this judges; a test feeds it readings whose answers are known.
 *
 * The rule every function keeps: "could not measure" and "measured, and fine" never come out the same. A row whose
 * precondition did not hold (the round was on its results screen, the body was not the player's to steer, the loading
 * cover was still up) is BLOCKED or N/A with the state it was in, never PASS and never FAIL; and one scripted run is
 * reported as one run, never as what always happens.
 *
 * WHERE THE GAME'S STATE COMES FROM (all optional; a reading that is missing stays null and is said to be unknown):
 *
 *   the port probe, `exposePort(net, { ... })` → window.__homiePort in the game's frame
 *     info().round { n, phase: 'live' | 'over', leftMs }      the round and the time left
 *     rows()[..][8]  (from `busy: () => boolean`)             the body is not the player's to steer right now
 *     rows()[..][1..2]                                        where the body is
 *     info().extra.alive      boolean   the local body is alive (false: spectating until the next round)
 *     info().extra.mode       string    the control mode on screen ("manual fire", "auto", "driving")
 *     info().extra.loadout    string    what the player holds (a weapon, a tool): it changes which controls show
 *     info().extra.touchHeld  boolean   a thumb is down on the game's stick
 *     info().extra.drawCalls / .triangles   numbers   the renderer's last frame (three.js: renderer.info.render)
 *   the play page's shell → window.__shell
 *     round { n, phase, endsAt }   arrival { phase ('done' = the loading cover lifted), liftedMs, by }
 *     link { state }               where the browser stands with its room, as the helper told the page
 *     rects { width, height, rects: [{ id, x, y, w, h, fades? }] }   where the page's own controls sit over the game
 *   the netplay helper → window.__homieNet in the game's frame (revision 9)
 *     link       'connecting' | 'online' | 'reconnecting' | 'alone' | 'offline' | 'closed'
 *     reconnects how often the link was interrupted
 *     stale      the revision of a newer build that is live (null: this tab runs the live build)
 *
 * A game sets the `extra` ones in its own exposePort call: `extra: { alive: () => me.hp > 0, mode: () => hud.mode }`.
 */

const num = (v) => (Number.isFinite(v) ? v : null);
const str = (v) => (typeof v === 'string' && v ? v.slice(0, 60) : typeof v === 'number' && Number.isFinite(v) ? String(v) : null);
const bool = (v) => (v === true || v === false ? v : null);

/**
 * The `extra` names read by name from the port probe: the same list as @homie-rocks/studio's port/probe.ts
 * (`PortExtra`, `PORT_EXTRA_NAMES`), where a game's author finds them typed and documented. A test holds the two
 * lists equal and runs this reader against the real probe.
 */
export const EXTRA_NAMES = ['alive', 'mode', 'loadout', 'touchHeld', 'drawCalls', 'triangles'];

/**
 * What the port probe says right now. It runs INSIDE the game's frame (the script hands it to the browser), so it
 * uses nothing but its argument and `window`: the round, the named extras, and the newest row's busy flag and place.
 */
export function readPort(names) {
  const p = window.__homiePort; if (!p) return null;
  let i = null; try { i = p.info(); } catch { /* a probe that throws reports nothing */ }
  const r = p.rows(p.now() - 400); const last = r.length ? r[r.length - 1] : null;
  const extra = {};
  for (const k of names) { const v = i?.extra?.[k]; if (['boolean', 'number', 'string'].includes(typeof v)) extra[k] = v; }
  return { round: i?.round ?? null, extra, frames: i?.frames ?? null, busy: last ? last[8] : null, x: last ? last[1] : null, y: last ? last[2] : null };
}

/*
 * THE LINK. A browser that is `reconnecting`, `alone` (the room never answered: it hosts by itself), `offline` or
 * `closed` is not in its room. What is sampled there is not the game as two people play it: the body may be frozen
 * between snapshots, the other players gone, the scores this browser's alone. Such a reading is labelled `cut-off`
 * and never judged as active play. The same six words and the same four "cut off" ones as the studio's own check
 * (lib/check.mjs LINK_STATES / CUT_OFF), held equal by a test.
 */
export const LINK_STATES = ['connecting', 'online', 'reconnecting', 'alone', 'offline', 'closed'];
export const CUT_OFF = ['reconnecting', 'alone', 'offline', 'closed'];
/** The link's state from the helper's word or the shell's { state } (the shell's `link` is the invite address, a string, until the first change), or null. */
export function linkOf(v) {
  const state = typeof v === 'string' ? v : v && typeof v === 'object' ? v.state : null;
  return LINK_STATES.includes(state) ? state : null;
}

/**
 * One reading of the game's state, from what the probe and the shell said at one moment. `raw`:
 * { at, port: { round, busy, x, y, extra, frames } | null, shell: { round, arrival, seat, link } | null,
 *   net: { link, reconnects } | null }  (`net`: the helper's own word, read in the game's frame; it wins over the shell's).
 */
export function stateOf(raw) {
  const p = raw?.port ?? null; const s = raw?.shell ?? null;
  const pr = p?.round ?? null; const sr = s?.round ?? null;
  const phase = pr?.phase === 'live' || pr?.phase === 'over' ? pr.phase : sr?.phase === 'live' || sr?.phase === 'over' ? sr.phase : null;
  // The probe's leftMs is on the room's own clock. The shell only has the end on the server's clock: without the
  // probe the time left is not known (this computer's clock is not the room's), so it stays null rather than a guess.
  const ex = p?.extra && typeof p.extra === 'object' ? p.extra : {};
  const arrival = s?.arrival ?? null;
  return {
    at: num(raw?.at),
    phase,
    round: num(pr?.n) ?? num(sr?.n),
    leftMs: pr ? num(pr.leftMs) : null,
    busy: p && (p.busy === 0 || p.busy === 1 || typeof p.busy === 'boolean') ? Boolean(p.busy) : null,
    alive: bool(ex.alive),
    pose: p && Number.isFinite(p.x) && Number.isFinite(p.y) ? { x: +p.x.toFixed(2), y: +p.y.toFixed(2) } : null,
    mode: str(ex.mode), loadout: str(ex.loadout), touchHeld: bool(ex.touchHeld),
    cover: arrival ? (arrival.phase === 'done' ? 'lifted' : 'up') : null,
    link: linkOf(raw?.net?.link) ?? linkOf(s?.link),
    // Said beside the state, never judged: how often the link was interrupted so far, and that a newer build of
    // the game is live than the one this tab runs (it loads again at the round's break).
    reconnects: num(raw?.net?.reconnects), stale: raw?.net?.stale ? String(raw.net.stale).slice(0, 40) : s?.stale ? String(s.stale.ver ?? 'a newer build').slice(0, 40) : null,
    source: pr ? 'probe' : sr ? 'shell' : null,
  };
}

/**
 * What kind of moment a reading is, for anything that needs active play:
 *   cut-off     the browser is not in its room (the helper's link: reconnecting, alone, offline, closed)
 *   loading     the arrival cover is still over the game
 *   results     the round is over (its results card, the break before the next)
 *   spectating  the game says the local body is dead
 *   busy        the body is not the player's to steer (knocked back, stunned, respawning; or dead in a game
 *               that reports only `busy`)
 *   live        a live round and nothing above
 *   unknown     the game exposes no round: nothing can be gated on it, and the row says so
 */
export function contextOf(state) {
  if (!state) return { kind: 'unknown', why: 'no reading of the game' };
  if (CUT_OFF.includes(state.link)) return { kind: 'cut-off', why: `the browser was not in its room (link: ${state.link}${state.link === 'alone' ? ', playing by itself because the room never answered' : state.link === 'reconnecting' ? ', its connection lost and knocking again' : ''}): this is not the game as people play it together` };
  if (state.cover === 'up') return { kind: 'loading', why: 'the loading cover was still over the game' };
  if (state.phase === 'over') return { kind: 'results', why: `round ${state.round ?? '?'} was over (its results and the break before the next one)` };
  if (state.alive === false) return { kind: 'spectating', why: 'the local body was dead (spectating until the next round)' };
  if (state.busy === true) return { kind: 'busy', why: 'the body was not the player\'s to steer (knocked back, stunned, dead or respawning: the probe\'s `busy`)' };
  if (state.phase === 'live') return { kind: 'live', why: `round ${state.round ?? '?'} was live` };
  return { kind: 'unknown', why: 'the game exposes no round phase (no port probe, no round on the shell)' };
}

/** A reading in a few words, for a report line: "round 3 live, 31 s left, body free at (878, 120), mode manual". */
export function describeState(state) {
  if (!state) return 'state not read';
  const bits = [];
  bits.push(state.phase ? `round ${state.round ?? '?'} ${state.phase === 'over' ? 'over (results)' : 'live'}` : 'round phase unknown');
  if (state.leftMs !== null) bits.push(`${Math.max(0, Math.round(state.leftMs / 1000))} s left`);
  bits.push(state.alive === false ? 'body dead' : state.busy === true ? 'body busy' : state.busy === false ? `body free${state.pose ? ` at (${state.pose.x}, ${state.pose.y})` : ''}` : 'body state unknown');
  if (state.mode) bits.push(`mode ${state.mode}`);
  if (state.loadout) bits.push(`loadout ${state.loadout}`);
  if (state.touchHeld !== null) bits.push(state.touchHeld ? 'thumb held' : 'thumb up');
  if (state.cover === 'up') bits.push('loading cover up');
  if (CUT_OFF.includes(state.link)) bits.push(`CUT OFF from its room (link ${state.link})`);
  if (state.reconnects > 0) bits.push(`${state.reconnects} reconnect${state.reconnects === 1 ? '' : 's'} so far`);
  if (state.stale) bits.push(`this tab runs an older build (${state.stale} is live)`);
  return bits.join(', ');
}

/** May a row that needs active play be judged at this reading? true, false, or null when the game does not say. */
export const activePlay = (state) => { const k = contextOf(state).kind; return k === 'live' ? true : k === 'unknown' ? null : false; };

/* ---------------------------------------------------------------- the first seconds */

/**
 * WHEN WAS THERE GAMEPLAY ON THE SCREEN. `samples`, in time order: { ms, seated, picture, cover, heartbeat } where
 * `picture` is "this screenshot is not black and not one colour", `cover` is 'up' | 'lifted' | null (a page with no
 * arrival state) and `heartbeat` is "the game's own frame counter moved since the last sample".
 *
 * Four separate times, because they are four different things:
 *   seatedMs         the shell had a room, a seat and a role
 *   firstPaintMs     the page showed anything that is a picture. The loading card is a picture: this is NOT the game.
 *   coverLiftedMs    the loading cover was gone
 *   firstGameplayMs  a picture, with the cover gone and the game's frames advancing: the first meaningful gameplay
 * `readiness` says how sure the last one is: 'arrival' (the page reported its cover lifting), or 'unverified' (the
 * page has no arrival state, so a loading screen the game draws itself cannot be told from play).
 */
export function readinessOf(samples) {
  const first = (f) => { const s = samples.find(f); return s ? s.ms : null; };
  const known = samples.some((s) => s.cover === 'up' || s.cover === 'lifted');
  const gameplay = samples.find((s) => s.picture && s.heartbeat && (known ? s.cover === 'lifted' : true)) ?? null;
  return {
    seatedMs: first((s) => s.seated),
    firstPaintMs: first((s) => s.picture),
    coverLiftedMs: known ? first((s) => s.cover === 'lifted') : null,
    heartbeatMs: first((s) => s.heartbeat),
    firstGameplayMs: gameplay ? gameplay.ms : null,
    readiness: known ? 'arrival' : 'unverified',
  };
}

/** The `first <device>` row from those times. `budgetMs` is how long the watch lasted (30 s). */
export function judgeFirst(r, { budgetMs = 30_000, slowMs = 10_000 } = {}) {
  const s = (ms) => `${(ms / 1000).toFixed(1)} s`;
  const why = r.seatedMs === null ? `never got a seat in ${s(budgetMs)}`
    : r.firstPaintMs === null ? `no real picture (black or one colour) in ${s(budgetMs)}`
    : r.readiness === 'arrival' && r.coverLiftedMs === null ? `the loading cover never lifted in ${s(budgetMs)}: the page painted at ${s(r.firstPaintMs)} but that picture was the loading card, not the game`
    : r.heartbeatMs === null ? `the game's frame never drew a frame in ${s(budgetMs)} (its frame counter did not move)`
    : r.firstGameplayMs === null ? `no picture of the game itself in ${s(budgetMs)} (the cover lifted${r.coverLiftedMs !== null ? ` at ${s(r.coverLiftedMs)}` : ''}, and every frame after it was black or one colour)`
    : r.seatedMs > slowMs ? `seated only after ${s(r.seatedMs)}`
    : r.firstGameplayMs > slowMs ? `the first picture of the game came at ${s(r.firstGameplayMs)} (the page first painted at ${s(r.firstPaintMs)}: that was the loading card)`
    : undefined;
  const note = r.readiness === 'unverified' && r.firstGameplayMs !== null ? 'this page reports no arrival state, so "first gameplay" is the first picture with the game\'s frames advancing: a loading screen the game draws itself would count. Look at the 1 s / 3 s / 5 s frames.' : undefined;
  return { verdict: why ? 'FAIL' : 'PASS', why, note };
}

/* ---------------------------------------------------------------- the first move */

const OPPOSITE = { right: 'left', left: 'right', up: 'down', down: 'up' };
export const oppositeOf = (dir) => OPPOSITE[dir] ?? 'left';

/**
 * THE FIRST MOVE. `attempts`, in order: { dir, moved, ms, before, after } with `before`/`after` the game's state at
 * the press and when the watch ended (stateOf readings). `waited`: what the wait for a live round came to
 * ({ ok, ms, state }) when no press was made at all.
 *
 *   PASS     the first press moved the body in time
 *   WARN     the first way moved nothing and the opposite way did: what a wall on that side looks like. Both are
 *            reported; it is not called broken controls, and it is not proof the first way works either.
 *   FAIL     the body answered too slowly, or neither way moved it in a live round with a free body
 *   BLOCKED  no press was made wholly inside a live round with a free body (a round break, a dead body, the cover):
 *            the latency of active play was not measured
 */
export function judgeMove(attempts, { maxMs = 1500, waited = null, holdMs = 3000 } = {}) {
  const at = (a) => (a.before?.pose ? ` from (${a.before.pose.x}, ${a.before.pose.y})` : '');
  const line = (a) => `${a.dir}${at(a)}: ${a.moved ? `moved in ${a.ms} ms` : `no movement in ${Math.round(holdMs / 1000)} s`} [${describeState(a.before)}]`;
  const detail = { attempts: attempts.map((a) => ({ dir: a.dir, moved: Boolean(a.moved), ms: a.ms ?? null, at: a.before?.pose ?? null, before: describeState(a.before), after: describeState(a.after) })) };
  if (!attempts.length) {
    return { verdict: 'BLOCKED', controlMs: null, why: `no press was made: ${waited?.state ? `${contextOf(waited.state).why} for the whole ${Math.round((waited.ms ?? 0) / 1000)} s wait` : 'the game never reached a state to press in'}. First-move latency in active play was not measured (the result screen and a spectator are not movement tests)`, ...detail };
  }
  const clean = (a) => activePlay(a.before) !== false && activePlay(a.after) !== false;
  const hit = attempts.find((a) => a.moved);
  if (hit) {
    const slow = hit.ms > maxMs;
    if (hit === attempts[0]) return { verdict: slow ? 'FAIL' : 'PASS', controlMs: hit.ms, why: slow ? `the body answered a press after ${hit.ms} ms (${line(hit)})` : undefined, ...detail };
    const firstTry = attempts[0];
    return {
      verdict: slow ? 'FAIL' : 'WARN', controlMs: hit.ms,
      why: `${slow ? `the body answered after ${hit.ms} ms. ` : ''}pressing ${firstTry.dir}${at(firstTry)} moved nothing, pressing ${hit.dir} moved the body in ${hit.ms} ms: that is what a wall on the ${firstTry.dir} looks like, so this is not called unresponsive controls. It does not prove ${firstTry.dir} works either: the controls row presses every way`,
      ...detail,
    };
  }
  const dirty = attempts.filter((a) => !clean(a));
  if (dirty.length) {
    return { verdict: 'BLOCKED', controlMs: null, why: `no press stayed inside a live round with a free body, so first-move latency was not measured: ${attempts.map(line).join('; ')}${dirty[0].after && contextOf(dirty[0].after).kind !== contextOf(dirty[0].before).kind ? `; by the end of the press ${contextOf(dirty[0].after).why}` : ''}`, ...detail };
  }
  const unknown = attempts.every((a) => activePlay(a.before) === null);
  return { verdict: 'FAIL', controlMs: null, why: `no press moved the body: ${attempts.map(line).join('; ')}${unknown ? '. The game exposes no round phase, so a round break cannot be ruled out' : ''}`, ...detail };
}

/* ---------------------------------------------------------------- UI coverage */

/** The limits of the UI row, said beside its result wherever a person reads it (the report, the row). */
export const UI_CAVEAT = 'DOM coverage only: the game\'s canvas is hidden for this measurement, so a HUD, labels or hints drawn inside the canvas were NOT checked for coverage or overlap. A pass here does not show a clear play area in a canvas game: look at the pictures.';

/** Why two isolation frames are not a pair (the game changed state between them), or null when they are. */
export function pairMismatch(a, b) {
  if (!a || !b) return null;
  const diff = [];
  for (const [k, label] of [['phase', 'round phase'], ['round', 'round'], ['alive', 'alive'], ['busy', 'busy'], ['mode', 'control mode'], ['loadout', 'loadout'], ['cover', 'loading cover'], ['link', 'link']]) {
    if (a[k] !== null && b[k] !== null && a[k] !== b[k]) diff.push(`${label} ${a[k]} → ${b[k]}`);
  }
  return diff.length ? diff.join(', ') : null;
}

/**
 * THE UI ROW. `cov` { cover, opaque, centreOpaque } from the two isolation frames; `before`/`after` the game's state
 * at the black and at the white frame; `thumb` 'held' | 'up' | 'none' (what the instrument's own thumb was doing).
 *
 *   BLOCKED  the two frames are not the same moment (the round ended between them): nothing is counted
 *   N/A      the frames show a results screen, a spectator or the loading cover: measured and labelled, and never
 *            judged against the active-play bar
 *   PASS/FAIL  active play (or a game that exposes no state, said so): the 12% bar and the clear middle
 *   WARN     it would pass, and a HUD element sits under one of the play page's own controls (`overlaps`)
 */
export function judgeUi(cov, { before = null, after = null, thumb = 'none', bar = 0.12, centreBar = 0.02, overlaps = null } = {}) {
  const mismatch = pairMismatch(before, after);
  const state = describeState(before);
  if (mismatch) return { verdict: 'BLOCKED', screen: 'mixed', why: `the game changed between the black frame and the white frame (${mismatch}), so they are not one screen and nothing was counted. Both frames are saved`, state };
  const ctx = contextOf(before);
  const pct = (v) => `${Math.round(v * 100)}%`;
  if (!['live', 'unknown'].includes(ctx.kind)) {
    const screen = { results: 'results screen', spectating: 'spectator view', busy: 'body not steerable', loading: 'loading cover', 'cut-off': 'screen of a browser cut off from its room' }[ctx.kind];
    return { verdict: 'N/A', screen, why: `this is the ${screen}, not active play (${ctx.why}): its DOM UI covers ${pct(cov.cover)} of the screen and ${pct(cov.centreOpaque)} of the middle third, recorded and not judged against the ${pct(bar)} active-play bar. Active-play coverage was not measured in this run`, state };
  }
  const why = cov.cover > bar ? `the DOM UI covers ${pct(cov.cover)} of the screen during play (the bar is ${pct(bar)})` : cov.centreOpaque > centreBar ? `something opaque covers ${pct(cov.centreOpaque)} of the middle third` : undefined;
  const unsure = ctx.kind === 'unknown' ? 'the game exposes no round phase, so this may be a results screen rather than active play: check the saved frames' : undefined;
  const held = thumb === 'up' ? 'measured with the thumb lifted: a held stick can add visible UI' : undefined;
  // The page's own controls over the HUD (shellOverlaps): a HUD element under one that does not fade is a WARN on a
  // row that would otherwise pass (measured, worth a look: the page's control is drawn on top of it). Under one
  // that fades it is a note. A page that reports no layout is said to be unchecked, never clear.
  const under = describeOverlaps(overlaps);
  const hides = Boolean(overlaps?.hidden?.length);
  const unchecked = overlaps && !overlaps.known ? 'the play page reported no layout of its own controls (window.__shell.rects), so the HUD was not checked against them' : undefined;
  return { verdict: why ? 'FAIL' : hides ? 'WARN' : 'PASS', screen: ctx.kind === 'live' ? 'active play' : 'state unknown', why: why ?? (hides ? under : undefined), qualifier: [unsure, held, unchecked, (why || !hides) && under ? under : undefined].filter(Boolean).join('; ') || undefined, state };
}

/* ---------------------------------------------------------------- the page's controls over the game's HUD */

/** The page's controls that stay over the game while it is played (a sheet, the results card and a vote are moments, not layout). */
const STANDING = new Set(['room', 'server', 'chat', 'chip', 'join', 'banner', 'ticker']);

/**
 * A GAME'S HUD UNDER THE PLAY PAGE'S OWN CONTROLS. The page draws its controls over the game's frame (the room
 * button, the server and chat pills, the "3 playing" chip, the banner). A HUD check that only measures inside the
 * frame cannot see them, so a score or a button can sit right under the room button and pass every check.
 *
 *   `layout`  the page's `window.__shell.rects` (or the helper's `net.shell`): { width, height, rects: [{ id, x, y, w, h, fades? }] }
 *             in the frame's own CSS pixels (the frame fills the page)
 *   `hud`     the game's visible DOM HUD elements, in the same pixels: [{ label, x, y, w, h, interactive? }]
 *
 * Returns { known, overlaps: [{ hud, shell, fades, interactive, px, share }], hidden: overlaps under a control that
 * does not fade }. `share` is how much of the HUD element is covered. A sliver (under 4 px either way) is not an
 * overlap. `known: false` when the page said no layout (an older shell): not checked, and said so. A HUD drawn
 * inside the canvas has no DOM element and is not seen here.
 */
export function shellOverlaps(layout, hud, { minPx = 4 } = {}) {
  const rects = Array.isArray(layout?.rects) ? layout.rects.filter((r) => r && STANDING.has(r.id) && r.w > 0 && r.h > 0) : null;
  if (!rects) return { known: false, overlaps: [], hidden: [] };
  const overlaps = [];
  for (const e of Array.isArray(hud) ? hud : []) {
    if (!(e?.w > 0 && e?.h > 0)) continue;
    for (const r of rects) {
      const w = Math.min(e.x + e.w, r.x + r.w) - Math.max(e.x, r.x);
      const h = Math.min(e.y + e.h, r.y + r.h) - Math.max(e.y, r.y);
      if (w < minPx || h < minPx) continue;
      overlaps.push({ hud: String(e.label ?? 'element').slice(0, 80), shell: r.id, fades: r.fades === true, interactive: e.interactive === true, px: Math.round(w * h), share: +((w * h) / (e.w * e.h)).toFixed(2) });
    }
  }
  overlaps.sort((a, b) => Number(a.fades) - Number(b.fades) || b.px - a.px);
  return { known: true, overlaps, hidden: overlaps.filter((o) => !o.fades) };
}

/** Those overlaps in a sentence for a row, or undefined when there are none. */
export function describeOverlaps(o) {
  if (!o?.known || !o.overlaps.length) return undefined;
  const one = (x) => `${x.hud} is under the page's ${x.shell} control (${Math.round(x.share * 100)}% of it covered${x.fades ? '; that control fades after a few seconds' : ''}${x.interactive ? '; it is something to press' : ''})`;
  return `the game's HUD sits under the play page's own controls: ${o.overlaps.slice(0, 4).map(one).join('; ')}${o.overlaps.length > 4 ? `; and ${o.overlaps.length - 4} more` : ''}. Lay the HUD out around them (net.shell / on('shell') says where they are, per device and orientation) or move the page's controls (game.json screen.share, screen.chat)`;
}

/* ---------------------------------------------------------------- the primary action */

const KEY = /^[A-Za-z0-9]{1,24}$/;
const frac = (v) => Number.isFinite(v) && v >= 0 && v <= 1;

/**
 * THE GAME'S PRIMARY ACTION, as game.json declares it (a shooter fires with the mouse; a default of "space, or a
 * tap at a fixed spot" never presses it):
 *
 *   "playtest": { "primary": { "label": "fire",
 *       "computer": { "key": "KeyF" }                      a KeyboardEvent.code
 *                 | { "mouse": "left", "at": [0.5, 0.5] }  a mouse button, at a fraction of the screen (default the middle)
 *       "phone":    { "selector": "[data-action=fire]" }   the game's own control, found in the game's frame
 *                 | { "region": [0.7, 0.7, 0.25, 0.2] }    x, y, w, h as fractions of the screen; the tap lands in its middle
 *   } }
 *
 * Returns { declared, kind: 'key' | 'mouse' | 'selector' | 'region', label, how, ... }. Undeclared (or malformed, with
 * `problem`): the old guess, marked `declared: false` so a score conclusion can say the action was a guess.
 */
export function actionProfile(gameJson, device) {
  const touch = device !== 'desk' && device !== 'computer';
  const fallback = touch
    ? { declared: false, kind: 'region', label: 'action', region: [0.82, 0.78, 0, 0], how: 'a tap at 82% across, 78% down (a guess: game.json declares no playtest.primary)' }
    : { declared: false, kind: 'key', label: 'action', key: 'Space', how: 'the space bar (a guess: game.json declares no playtest.primary)' };
  const p = gameJson?.playtest?.primary;
  if (!p || typeof p !== 'object') return fallback;
  const label = str(p.label) ?? 'primary action';
  const d = touch ? p.phone : p.computer;
  if (!d || typeof d !== 'object') return { ...fallback, how: `${fallback.how.replace(/ \(a guess.*$/, '')} (a guess: playtest.primary has no "${touch ? 'phone' : 'computer'}")` };
  if (!touch && typeof d.key === 'string' && KEY.test(d.key)) return { declared: true, kind: 'key', label, key: d.key, how: `${label}: the ${d.key} key` };
  if (!touch && ['left', 'right', 'middle'].includes(d.mouse)) {
    const at = Array.isArray(d.at) && d.at.length === 2 && d.at.every(frac) ? d.at : [0.5, 0.5];
    return { declared: true, kind: 'mouse', label, button: d.mouse, at, how: `${label}: the ${d.mouse} mouse button at ${Math.round(at[0] * 100)}% across, ${Math.round(at[1] * 100)}% down` };
  }
  if (touch && typeof d.selector === 'string' && d.selector.length <= 200 && d.selector.trim()) return { declared: true, kind: 'selector', label, selector: d.selector.trim(), how: `${label}: a tap on the game's control ${d.selector.trim()}` };
  if (touch && Array.isArray(d.region) && d.region.length === 4 && d.region.every(frac)) return { declared: true, kind: 'region', label, region: d.region, how: `${label}: a tap in the declared region (${d.region.map((v) => Math.round(v * 100)).join('%, ')}%)` };
  return { ...fallback, problem: `game.json playtest.primary.${touch ? 'phone' : 'computer'} is not one of ${touch ? '{ "selector": "<css>" } or { "region": [x, y, w, h] }' : '{ "key": "<KeyboardEvent.code>" } or { "mouse": "left" | "right" | "middle" }'}` };
}

/** What the script really pressed, for the report: "moves 31; fire (the left mouse button …) 9 pressed, 2 missed". */
export function describeActions(a) {
  if (!a) return 'not recorded';
  const p = a.primary ?? {};
  return `direction holds ${a.moves ?? 0}; ${p.how ?? 'primary action'}: ${p.pressed ?? 0} pressed${p.missed ? `, ${p.missed} missed (the control was not on screen)` : ''}`;
}

/* ---------------------------------------------------------------- the round */

/**
 * WHAT A PLAYED ROUND'S SCORES SAY. `me` the row of the browser that played, `them` the one that did nothing,
 * `rows` every result row, `scoring` game.json's ("together": one shared total on every row), `actions` what the
 * script exercised ({ moves, primary: { declared, how, pressed, missed } }).
 *
 * Returns { notes, comparison }. A cooperative game's rows carry one shared total, so comparing them as rivals is
 * `comparison: 'not applicable'`. Nothing here claims more than one scripted round can show.
 */
export function judgeScores({ me, them, rows = [], scoring = null, planned = null, roundSeconds = null, actions = null }) {
  const notes = [];
  const together = scoring === 'together';
  const primary = actions?.primary ?? null;
  const exercised = Boolean(primary?.declared && primary.pressed > 0);
  // What the script did NOT do, said with any conclusion drawn from the scores.
  const scope = !primary ? ''
    : !primary.declared ? ` The script only held directions and pressed ${primary.how}; game.json declares no primary action (playtest.primary), so if the game scores through another input (a mouse button, a fire control) it was never used, and this is not evidence that input does not matter`
    : !exercised ? ` The declared primary action (${primary.how}) was never pressed in this round${primary.missed ? ` (${primary.missed} tries found no control on screen)` : ''}, so this is not evidence that input does not matter`
    : '';
  let comparison;
  if (together) {
    comparison = 'not applicable: game.json says "scoring": "together", so every row carries the room\'s one shared total and an idle player level with an active one is how the game scores. Whether input matters to a cooperative game needs each player\'s contribution, which this row does not measure';
    const total = Math.max(-Infinity, ...rows.map((x) => x.score).filter(Number.isFinite));
    if (Number.isFinite(total) && total === 0) notes.push(`the room's shared total was 0 after a whole round with one person playing.${scope}`);
  } else {
    comparison = 'the player who played against the one who pressed nothing, in one scripted round';
    if (me && them && them.score >= me.score) notes.push(`in this one round the player who pressed nothing scored ${them.score} and the one who played scored ${me.score}.${scope || ' The declared primary action was pressed, so input may matter little to the score: play it again before concluding'}`);
    if (me && me.score === 0 && !(them && them.score >= me.score)) notes.push(`the playing browser scored 0 for a whole round.${scope}`);
    if (rows.length > 1 && rows.every((x) => x.score === rows[0].score)) notes.push('every player finished on the same score');
    const bestBot = Math.max(-Infinity, ...rows.filter((x) => x.bot).map((x) => x.score));
    const bestHuman = Math.max(-Infinity, ...rows.filter((x) => !x.bot).map((x) => x.score));
    if (Number.isFinite(bestBot) && Number.isFinite(bestHuman) && bestBot > Math.max(3 * bestHuman, bestHuman + 10)) {
      notes.push(`a bot outscored every person ${bestBot} to ${bestHuman} in this one scripted round (a gap of ${bestBot - bestHuman}). That is a measured gap, not proof that people cannot win: the script is not a person${exercised ? '' : ' and did not use the game\'s primary action'}. Run the play row a few more times and compare with rounds people played before tuning the bots`);
    }
  }
  if (planned && roundSeconds && Math.abs(planned - roundSeconds) > roundSeconds * 0.2) notes.push(`the round was set to ${planned} s but game.json says ${roundSeconds} s`);
  return { notes, comparison, scoring: together ? 'together' : 'rivals', primaryExercised: exercised };
}

/**
 * A finished round is not an uninterrupted one. `connection`: homie-studio check's
 * [{ browser, reconnects (a number, or null when the page did not report it), cutOff? (link states seen) }].
 * Returns { reconnects, uninterrupted: true | false | null, note }.
 */
export function connectionNote(connection) {
  if (!Array.isArray(connection) || !connection.length) return { reconnects: null, uninterrupted: null, note: 'reconnects were not reported (an older homie-studio): completion says nothing about whether the connection held' };
  const unknown = connection.filter((c) => !Number.isFinite(c.reconnects)).map((c) => c.browser);
  const dropped = connection.filter((c) => c.reconnects > 0);
  const total = dropped.reduce((s, c) => s + c.reconnects, 0);
  // `cutOff`: the link states homie-studio check saw a browser in besides `online` (reconnecting, alone, offline,
  // closed). A browser seen cut off was interrupted whether or not its counter moved.
  const cut = connection.filter((c) => Array.isArray(c.cutOff) && c.cutOff.length && !(c.reconnects > 0));
  if (dropped.length || cut.length) return { reconnects: dropped.length ? total : null, uninterrupted: false, note: `the round finished, and the connection did not hold throughout: ${[...dropped.map((c) => `the ${c.browser} reconnected ${c.reconnects} time${c.reconnects === 1 ? '' : 's'}${Array.isArray(c.cutOff) && c.cutOff.length ? ` (seen ${c.cutOff.join(', ')})` : ''}`), ...cut.map((c) => `the ${c.browser} was seen cut off from the room (${c.cutOff.join(', ')})`)].join(', ')}. No cause is established by one run: run it again and compare` };
  if (unknown.length) return { reconnects: null, uninterrupted: null, note: `reconnects were not reported by the ${unknown.join(' and the ')}: whether the connection held is unknown` };
  return { reconnects: 0, uninterrupted: true, note: 'no reconnects: both connections held from the seat to the results' };
}

/* ---------------------------------------------------------------- measured runtime cost */

/**
 * The renderer's own numbers while the game was played, from samples of `extra.drawCalls` / `extra.triangles` (null
 * entries: the game did not expose them at that moment). MEASURED runtime cost, which the asset inventory's estimate
 * is not: it includes procedural geometry, repeated characters, effects and shadow passes.
 * Returns { samples, drawCalls: { median, max }, triangles: { median, max } }, or null when nothing was exposed.
 */
export function renderCost(samples) {
  const pick = (k) => samples.map((s) => s?.[k]).filter((v) => Number.isFinite(v) && v >= 0);
  const calls = pick('drawCalls'); const tris = pick('triangles');
  if (!calls.length && !tris.length) return null;
  const sum = (xs) => { if (!xs.length) return null; const s = [...xs].sort((a, b) => a - b); return { median: s[Math.floor((s.length - 1) / 2)], max: s[s.length - 1] }; };
  return { samples: Math.max(calls.length, tris.length), drawCalls: sum(calls), triangles: sum(tris) };
}

/* ---------------------------------------------------------------- the review */

/** The kinds of review a run can have had. Only `independent` is a blind review. */
export const REVIEW_KINDS = ['independent', 'local', 'none'];

/**
 * The line a report carries about its review, from review.json in the run folder (or its absence):
 *   independent  a fresh reviewer that never saw the code scored it
 *   local        the session that built the game scored the pictures with the same rubric: NOT independent
 *   none         no review ran: BLOCKED with the reason, never a pass
 */
export function reviewLine(record) {
  if (!record || !REVIEW_KINDS.includes(record.kind)) return { verdict: 'BLOCKED', kind: 'none', line: 'BLOCKED review: no review has been recorded for this run. The instruments are not a review; a run without one has not been reviewed.' };
  const score = Number.isFinite(record.score) ? ` Overall ${record.score}/100.` : '';
  if (record.kind === 'independent') return { verdict: 'DONE', kind: 'independent', line: `Review: independent (a fresh reviewer that never saw the code${record.by ? `: ${record.by}` : ''}).${score}` };
  if (record.kind === 'local') return { verdict: 'WARN', kind: 'local', line: `WARN review: local fallback, NOT independent (the session that made the game scored the contact sheets with the same rubric${record.reason ? `, because ${record.reason}` : ''}).${score} A builder grading its own build is weaker evidence: get an independent review before calling it reviewed.` };
  return { verdict: 'BLOCKED', kind: 'none', line: `BLOCKED review: no review ran${record.reason ? ` (${record.reason})` : ''}. A missing review is not a passed one.` };
}

/* ---------------------------------------------------------------- the report */

/** What is weakest, most important first: failures, then what could not be measured, then warnings. */
export function weakest(rs) {
  const order = { FAIL: 0, BLOCKED: 1, WARN: 2 };
  const weight = { round: 0, play: 1, controls: 2, first: 3, move: 3, sound: 4, look: 5, ui: 6, errors: 7 };
  // N/A is not weak: the row did not apply (a QR on a loopback preview, a results screen under the active-play bar).
  return rs.filter((r) => r.verdict in order).sort((a, b) => order[a.verdict] - order[b.verdict] || (weight[a.name.split(' ')[0]] ?? 9) - (weight[b.name.split(' ')[0]] ?? 9)).map((r) => `${r.verdict} ${r.name}: ${r.why ?? 'see the report'}`);
}

const HIDE = new Set(['shellOverlaps', 'name', 'verdict', 'why', 'shots', 'rows', 'results', 'scoreSamples', 'errors', 'requests', 'note', 'soundJs', 'gaps', 'seats', 'state', 'qualifier', 'comparison', 'actions', 'attempts', 'connection', 'instrument', 'screen', 'frames', 'render', 'stateBlack', 'stateWhite', 'heartbeatFrom', 'action']);

/** REPORT.md. `review` is review.json's content, or null. */
export function reportMd(rep, review = null) {
  const L = [`# Playtest: ${rep.game}`, '', `${rep.url} · ${rep.at} · ${rep.seconds} s · port probe: ${rep.probe ? 'yes' : 'no (owner tests cannot see the body, and no row can tell a live round from its results screen; see the port skill)'}`, ''];
  L.push('## What is weak', '', ...(rep.weak.length ? rep.weak.map((w) => `- ${w}`) : ['- Nothing the instruments can see. That is not the same as fun: read the review.']), '');
  L.push('## Review', '', reviewLine(review).line, '');
  L.push('## Rows', '', 'PASS: measured, and fine. FAIL: measured, and not. WARN: measured, worth a look. BLOCKED: could not be measured (never a pass). N/A: the row did not apply to what was on screen.', '', '| row | verdict | numbers |', '| --- | --- | --- |');
  for (const r of rep.rows) {
    const nums = Object.entries(r).filter(([k, v]) => !HIDE.has(k) && v !== null && v !== undefined && typeof v !== 'object').map(([k, v]) => `${k} ${v}`).join(', ');
    L.push(`| ${r.name} | ${r.verdict} | ${nums.replace(/\|/g, '/')} |`);
  }
  L.push('');
  // What a number alone would overstate, said beside it in words a person reads (not only in report.json).
  const said = [];
  for (const r of rep.rows) {
    const kind = r.name.split(' ')[0];
    const bits = [];
    if (kind === 'ui') bits.push(`${r.screen ? `screen measured: ${r.screen}. ` : ''}${r.stateBlack ? `State at the black frame: ${r.stateBlack}; at the white frame: ${r.stateWhite ?? 'not read'}${r.thumb ? `; thumb ${r.thumb}` : ''}. ` : r.state ? `State at the capture: ${r.state}. ` : ''}${UI_CAVEAT}`);
    if (kind === 'move' && r.attempts?.length) bits.push(r.attempts.map((a) => `pressed ${a.dir}${a.at ? ` from (${a.at.x}, ${a.at.y})` : ''}: ${a.moved ? `moved in ${a.ms} ms` : 'no movement'} [${a.before}]`).join('; '));
    if (kind === 'play') { if (r.comparison) bits.push(`Score comparison: ${r.comparison}.`); if (r.actions) bits.push(`What the script pressed: ${r.actions}.`); bits.push('One scripted round: a gap measured once, not what always happens.'); }
    if (kind === 'round' && r.connection) bits.push(`Completion and connection are separate: ${r.connection}.`);
    if (kind === 'look' && r.render) bits.push(`Measured runtime cost (the renderer's own counters while playing, not the asset inventory's estimate): ${r.render}.`);
    if (r.qualifier) bits.push(r.qualifier);
    if (r.note && kind !== 'ui') bits.push(r.note);
    if (bits.length) said.push(`- **${r.name}** (${r.verdict}): ${bits.join(' ')}`);
  }
  if (said.length) L.push('## What each row does and does not show', '', ...said, '');
  L.push('Pictures: `sheet-*.png` (contact sheets), `*-first-*.png`, `*-look-*.png`, `*-ui-on-black.png` and `*-ui-on-white.png` (the pair the UI row was counted from), `sound-capture.png`, `play-round-over.png`. Look at them before believing any number here.', '');
  return `${L.join('\n')}\n`;
}
