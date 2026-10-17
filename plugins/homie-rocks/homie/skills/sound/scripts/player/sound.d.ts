/** Types for sound.js (the Homie plugin's sound skill): a game's effects and music from sound.json. */
export interface PlayOptions { volume?: number; pitch?: number; pan?: number; jitter?: number }
export interface SoundState { unlocked: boolean; running: boolean; loaded: number; music: { name: string; section: string; since: number } | null; missing: string[]; errors: string[] }
export interface Sound {
  /** Resolves once sound.json and every file it lists have loaded (or failed, which state().errors names). */
  ready: Promise<unknown>;
  /** Play an effect by name: a random variant, a little pitch jitter, at most a few of one name at once. Dropped before the first gesture. */
  play(name: string, options?: PlayOptions): AudioBufferSourceNode | null;
  /** Start a score's loops (its first section unless one is named); it starts on the first touch or key. */
  music(name: string, options?: { section?: string; fade?: number }): void;
  /** Switch to another section's loop exactly on the next bar line. */
  section(name: string, options?: { fade?: number }): void;
  stopMusic(options?: { fade?: number }): void;
  /** Music down to `to` (0..1) for `seconds`, then back. */
  duck(to?: number, seconds?: number): void;
  volume(levels: { master?: number; sfx?: number; music?: number }): void;
  mute(on?: boolean): void;
  readonly context: AudioContext | null;
  state(): SoundState;
}
export function createSound(options?: { base?: string; manifest?: string; maxPerName?: number; maxVoices?: number }): Sound;
/**
 * The capture log (see the head of sound.js): a frame-by-frame recorder sets `window.__homieSoundCapture = { events: [] }`
 * before the page's scripts run, and every sound scheduled is pushed onto `events`. `t` is performance.now() in ms,
 * `delay` and `fade` are seconds, `url` is absolute. A game with its own audio code may push the same events.
 */
export type SoundCaptureEvent =
  | { t: number; type: 'start'; id: number; bus: 'sfx' | 'music'; name: string; url: string; gain: number; rate: number; pan: number; loop: boolean; delay: number; fadeIn: number; bar?: number }
  | { t: number; type: 'stop'; id: number; delay: number; fade: number; curve: 'cut' | 'linear' | 'target' }
  | { t: number; type: 'duck'; to: number; seconds: number }
  | { t: number; type: 'levels'; master: number; sfx: number; music: number; muted: boolean }
  | { t: number; type: 'drop'; name: string; why: 'locked' | 'missing' | 'loading' | 'voices' };
declare global { interface Window { __homieSoundCapture?: { events: SoundCaptureEvent[] } } }
