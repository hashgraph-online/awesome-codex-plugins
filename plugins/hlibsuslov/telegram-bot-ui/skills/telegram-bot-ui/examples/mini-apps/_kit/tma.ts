/* Mini App kit: a thin, dependency-free layer over window.Telegram.WebApp ("TMA profile 1").
   Erasable TypeScript only (no enums, namespaces or parameter properties): Node >= 22.18 runs it
   directly in tests, and build.mjs strips the types for the browser.
   What it does: saves launch params before a router can erase them; mirrors scheme, platform and the
   Android performance class onto <html>; gates every call by version; drives the MainButton,
   SecondaryButton and BackButton from a screen stack; haptics by meaning; storage with fallbacks;
   typed events gated by the version that added them, with unsubscribe; a state snapshot.
   Reference: references/mini-apps/design-system.md, webapp-api.md (§5 Events and state). */

export type Scheme = 'light' | 'dark';
export type PlatformClass = 'ios' | 'android' | 'desktop' | 'web' | 'unknown';
export type Perf = 'low' | 'average' | 'high' | 'unknown';
export type SurfaceColor = 'bg_color' | 'secondary_bg_color' | `#${string}`;
/** setBottomBarColor also takes bottom_bar_bg_color (7.10). */
export type ChromeColor = SurfaceColor | 'bottom_bar_bg_color';

export interface BottomButtonLike {
  setParams(p: Record<string, unknown>): unknown;
  onClick(cb: () => void): unknown;
  offClick(cb: () => void): unknown;
  showProgress(leaveActive?: boolean): unknown;
  hideProgress(): unknown;
  /** Sets the button text; the kit passes text through setParams together with the other fields. */
  setText?(text: string): unknown;
  isVisible?: boolean;
  /** Read-only: the loading indicator is showing. The kit tracks its own busy state per button. */
  readonly isProgressVisible?: boolean;
}

/** WebAppUser fields the kit reads; display only, never for decisions (initData is verified on the server). */
export interface WebAppUserLike {
  allows_write_to_pm?: true;
  language_code?: string;
  /** .jpeg or .svg; absent when privacy settings hide it. */
  photo_url?: string;
  /** 6.9: the user added the bot to the attachment menu. */
  added_to_attachment_menu?: true;
}

/** shareToStory params (7.8): a caption, and a link widget that only Premium users can post. */
export interface StoryShareParams {
  text?: string;
  widget_link?: { url: string; name?: string };
}

export interface WebAppLike {
  initData: string;
  version: string;
  platform?: string;
  colorScheme?: Scheme;
  themeParams?: Record<string, string>;
  isVersionAtLeast(v: string): boolean;
  ready(): void;
  expand?(): void;
  close?(): void;
  /** 8.0: fullscreen; the result comes as fullscreenChanged or fullscreenFailed. */
  requestFullscreen?(): void;
  exitFullscreen?(): void;
  /** 7.7: swipe down on the content minimises or closes the app unless disabled. */
  enableVerticalSwipes?(): void;
  disableVerticalSwipes?(): void;
  onEvent(name: string, cb: (...a: unknown[]) => void): void;
  offEvent(name: string, cb: (...a: unknown[]) => void): void;
  setHeaderColor?(c: string): void;
  setBackgroundColor?(c: string): void;
  setBottomBarColor?(c: string): void;
  enableClosingConfirmation?(): void;
  disableClosingConfirmation?(): void;
  showConfirm?(msg: string, cb: (ok: boolean) => void): void;
  showPopup?(p: Record<string, unknown>, cb: (id: string) => void): void;
  openInvoice?(url: string, cb: (status: string) => void): void;
  requestWriteAccess?(cb: (allowed: boolean) => void): void;
  /** 9.6: reqId is a PreparedKeyboardButton id from the bot's savePreparedKeyboardButton. */
  requestChat?(reqId: string, cb?: (ok: boolean) => void): void;
  shareToStory?(mediaUrl: string, params?: StoryShareParams): void;
  hideKeyboard?(): void;
  /** Current state, read through state(): versions in MEMBER_SINCE. Colours are #RRGGBB. */
  isFullscreen?: boolean;
  isOrientationLocked?: boolean;
  isVerticalSwipesEnabled?: boolean;
  isClosingConfirmationEnabled?: boolean;
  headerColor?: string;
  backgroundColor?: string;
  bottomBarColor?: string;
  /** chat.photo_url: only for launches from the attachment menu. */
  initDataUnsafe?: { user?: WebAppUserLike; chat?: { photo_url?: string } };
  MainButton?: BottomButtonLike;
  SecondaryButton?: BottomButtonLike;
  BackButton?: { show(): void; hide(): void; onClick(cb: () => void): void; offClick(cb: () => void): void };
  SettingsButton?: { show(): void; hide(): void; onClick(cb: () => void): void; offClick(cb: () => void): void };
  HapticFeedback?: {
    impactOccurred(s: string): void;
    notificationOccurred(t: string): void;
    selectionChanged(): void;
  };
  Accelerometer?: MotionSensorLike;
  Gyroscope?: MotionSensorLike;
  DeviceOrientation?: MotionSensorLike;
  LocationManager?: {
    isInited: boolean; isLocationAvailable: boolean; isAccessGranted: boolean;
    init(cb?: () => void): void;
    getLocation(cb: (data: LocationData | null) => void): void;
    openSettings(): void;
  };
  CloudStorage?: CloudStorageLike;
  DeviceStorage?: StorageLike;
  SecureStorage?: SecureStorageLike;
}

interface MotionSensorLike {
  isStarted: boolean;
  start(params: Record<string, unknown>, cb?: (ok: boolean) => void): void;
  stop(cb?: (ok: boolean) => void): void;
  x?: number; y?: number; z?: number;
  alpha?: number; beta?: number; gamma?: number; absolute?: boolean;
}

/** WebApp.LocationManager data (8.0); null fields mean the device does not report them. */
export interface LocationData {
  latitude: number; longitude: number; altitude: number | null; course: number | null; speed: number | null;
  horizontal_accuracy: number | null; vertical_accuracy: number | null;
  /** Degrees and m/s. */
  course_accuracy: number | null; speed_accuracy: number | null;
}

export type ImpactStyle = 'light' | 'medium' | 'heavy' | 'rigid' | 'soft';
export type NotificationType = 'success' | 'warning' | 'error';
export type MotionSensor = 'accelerometer' | 'gyroscope' | 'orientation';
/** One reading: x/y/z for the accelerometer (m/s^2) and gyroscope (rad/s), alpha/beta/gamma for orientation (rad). */
export type MotionReading = { x?: number; y?: number; z?: number; alpha?: number; beta?: number; gamma?: number; absolute?: boolean };

interface StorageLike {
  setItem(k: string, v: string, cb?: (err: unknown, ok?: unknown) => void): void;
  /** SecureStorage passes a third argument for a missing key: whether restoreItem can bring it back. */
  getItem(k: string, cb: (err: unknown, v?: string | null, canBeRestored?: boolean) => void): void;
  removeItem(k: string, cb?: (err: unknown, ok?: unknown) => void): void;
}

/** CloudStorage batch methods (6.9). The page calls getItems' result only "the values": the kit reads it as
 *  an object keyed by key, like getItem's ('' for a missing key). */
interface CloudStorageLike extends StorageLike {
  getItems?(keys: string[], cb: (err: unknown, values?: Record<string, string>) => void): void;
  getKeys?(cb: (err: unknown, keys?: string[]) => void): void;
  removeItems?(keys: string[], cb?: (err: unknown, removed?: boolean) => void): void;
}

/** restoreItem (9.0) asks the user before it restores a key this device had. */
interface SecureStorageLike extends StorageLike {
  restoreItem?(k: string, cb?: (err: unknown, v?: string | null) => void): void;
}

/* ------------------------------------------------------------ events and versions (webapp-api.md §5) */

type StatusOf<A extends string> = { status: A };
type SensorFailure = { error: 'UNSUPPORTED' };

/** What each Telegram.WebApp event hands its handler (void: no parameters; read the WebApp object instead).
 *  Fields and values from data/mini-apps/webapp-catalog.json. */
export interface TmaEventMap {
  themeChanged: void;
  viewportChanged: { isStateStable: boolean };
  mainButtonClicked: void;
  secondaryButtonClicked: void;
  backButtonClicked: void;
  settingsButtonClicked: void;
  invoiceClosed: { url: string; status: 'paid' | 'cancelled' | 'failed' | 'pending' };
  popupClosed: { button_id: string | null };
  qrTextReceived: { data: string };
  scanQrPopupClosed: void;
  /** '' when the clipboard holds no text, null when the app has no access. */
  clipboardTextReceived: { data: string | null };
  writeAccessRequested: StatusOf<'allowed' | 'cancelled'>;
  contactRequested: StatusOf<'sent' | 'cancelled'>;
  biometricManagerUpdated: void;
  /** biometricToken only when isAuthenticated is true. */
  biometricAuthRequested: { isAuthenticated: boolean; biometricToken?: string };
  biometricTokenUpdated: { isUpdated: boolean };
  activated: void;
  deactivated: void;
  safeAreaChanged: void;
  contentSafeAreaChanged: void;
  fullscreenChanged: void;
  fullscreenFailed: { error: 'UNSUPPORTED' | 'ALREADY_FULLSCREEN' };
  homeScreenAdded: void;
  homeScreenChecked: StatusOf<'unsupported' | 'unknown' | 'added' | 'missed'>;
  accelerometerStarted: void;
  accelerometerStopped: void;
  accelerometerChanged: void;
  accelerometerFailed: SensorFailure;
  deviceOrientationStarted: void;
  deviceOrientationStopped: void;
  deviceOrientationChanged: void;
  deviceOrientationFailed: SensorFailure;
  gyroscopeStarted: void;
  gyroscopeStopped: void;
  gyroscopeChanged: void;
  gyroscopeFailed: SensorFailure;
  locationManagerUpdated: void;
  locationRequested: { locationData: LocationData };
  shareMessageSent: void;
  shareMessageFailed: { error: 'UNSUPPORTED' | 'MESSAGE_EXPIRED' | 'MESSAGE_SEND_FAILED' | 'USER_DECLINED' | 'UNKNOWN_ERROR' };
  emojiStatusSet: void;
  emojiStatusFailed: {
    error: 'UNSUPPORTED' | 'SUGGESTED_EMOJI_INVALID' | 'DURATION_INVALID' | 'USER_DECLINED' | 'SERVER_ERROR' | 'UNKNOWN_ERROR';
  };
  emojiStatusAccessRequested: StatusOf<'allowed' | 'cancelled'>;
  fileDownloadRequested: StatusOf<'downloading' | 'cancelled'>;
}
export type TmaEventName = keyof TmaEventMap;

/** The Bot API version that added each event (the catalog's; a test keeps them equal). An older client never
 *  fires it, so listen() refuses it there and the app takes the method's callback or its fallback. */
export const EVENT_SINCE: Readonly<Record<TmaEventName, string>> = {
  themeChanged: '6.0', viewportChanged: '6.0', mainButtonClicked: '6.0', secondaryButtonClicked: '7.10',
  backButtonClicked: '6.1', settingsButtonClicked: '6.1', invoiceClosed: '6.1', popupClosed: '6.2',
  qrTextReceived: '6.4', scanQrPopupClosed: '7.7', clipboardTextReceived: '6.4',
  writeAccessRequested: '6.9', contactRequested: '6.9',
  biometricManagerUpdated: '7.2', biometricAuthRequested: '7.2', biometricTokenUpdated: '7.2',
  activated: '8.0', deactivated: '8.0', safeAreaChanged: '8.0', contentSafeAreaChanged: '8.0',
  fullscreenChanged: '8.0', fullscreenFailed: '8.0', homeScreenAdded: '8.0', homeScreenChecked: '8.0',
  accelerometerStarted: '8.0', accelerometerStopped: '8.0', accelerometerChanged: '8.0', accelerometerFailed: '8.0',
  deviceOrientationStarted: '8.0', deviceOrientationStopped: '8.0', deviceOrientationChanged: '8.0',
  deviceOrientationFailed: '8.0',
  gyroscopeStarted: '8.0', gyroscopeStopped: '8.0', gyroscopeChanged: '8.0', gyroscopeFailed: '8.0',
  locationManagerUpdated: '8.0', locationRequested: '8.0', shareMessageSent: '8.0', shareMessageFailed: '8.0',
  emojiStatusSet: '8.0', emojiStatusFailed: '8.0', emojiStatusAccessRequested: '8.0', fileDownloadRequested: '8.0',
};

/** Catalog versions of the other members the kit gates by name (checked against the catalog in a test). */
export const MEMBER_SINCE = {
  'WebApp.headerColor': '6.1',
  'WebApp.backgroundColor': '6.1',
  'WebApp.isClosingConfirmationEnabled': '6.2',
  'WebApp.isVerticalSwipesEnabled': '7.7',
  'WebApp.bottomBarColor': '7.10',
  'WebApp.isFullscreen': '8.0',
  'WebApp.isOrientationLocked': '8.0',
  'WebApp.requestChat': '9.6',
  'CloudStorage.getItems': '6.9',
  'CloudStorage.getKeys': '6.9',
  'CloudStorage.removeItems': '6.9',
  'SecureStorage.restoreItem': '9.0',
} as const;

/** WebApp's current state; null where the client is older than the field or does not report it. */
export interface TmaState {
  isFullscreen: boolean | null;
  isOrientationLocked: boolean | null;
  isVerticalSwipesEnabled: boolean | null;
  isClosingConfirmationEnabled: boolean | null;
  headerColor: string | null;
  backgroundColor: string | null;
  bottomBarColor: string | null;
}

export interface RootLike {
  dataset: Record<string, string | undefined>;
  lang?: string;
  dir?: string;
  style: { setProperty(name: string, value: string): void; colorScheme?: string };
}

export interface FallbackButtonLike {
  hidden: boolean;
  textContent: string | null;
  disabled?: boolean;
  onclick: ((ev?: unknown) => unknown) | null;
}

/** The page's vertical scroll, for keeping each screen and tab where the user left it (tests inject one). */
export interface ScrollerLike {
  /** Where the user was: the current position, or the last one a scroll event saw when the app has already
   *  reset the view in the same tap (hid the list, called scrollTo(0, 0)) before pushing. */
  y(): number;
  to(y: number): void;
  /** Runs after the app has shown the screen it returns to. */
  frame(cb: () => void): void;
}

export interface Env {
  webApp?: WebAppLike | null;
  /** Shown instead of the MainButton outside Telegram (plain browser); default: [data-tma-fallback="main-button"]. */
  fallbackButton?: FallbackButtonLike | null;
  /** Shown instead of Telegram's BackButton where there is none (plain browser, clients before 6.1) while a screen
   *  or sheet is open; default: [data-tma-fallback="back-button"]. */
  fallbackBack?: FallbackButtonLike | null;
  scroller?: ScrollerLike | null;
  root?: RootLike;
  location?: { hash: string; search: string };
  userAgent?: string;
  /** Clock for the haptic burst guard (tests). */
  now?: () => number;
  /** Browser languages, most preferred first (default: navigator.languages). */
  languages?: readonly string[];
  /** fetch and a sleep for api() (tests). */
  fetch?: (url: string, init: Record<string, unknown>) => Promise<ResponseLike>;
  sleep?: (ms: number) => Promise<void>;
}

/** The part of a fetch Response that api() reads. */
export interface ResponseLike {
  ok: boolean;
  status: number;
  text(): Promise<string>;
}

/** What went wrong, in the terms the screen needs (references/mini-apps/forms-and-data.md §6):
 *  offline / timeout - nothing reached the server or no answer came: "try again", keep the input;
 *  session - initData too old or refused (401/403): reopen the app from the chat;
 *  rejected - the server said no (4xx): show its reason, let the user fix the input;
 *  server - the server failed (5xx): try again later, nothing was done (with an idempotency key). */
export type ApiErrorKind = 'offline' | 'timeout' | 'session' | 'rejected' | 'server';

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number;
  readonly body: unknown;
  constructor(kind: ApiErrorKind, status = 0, body: unknown = null) {
    super(kind + (status ? ` ${status}` : ''));
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
    this.body = body;
  }
  /** The server's own words for a rejection ({"reason": "..."}), if it sent any. */
  get reason(): string | null {
    const b = this.body as { reason?: unknown } | null;
    return b && typeof b.reason === 'string' ? b.reason : null;
  }
}

export interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  /** Abort and fail with "timeout" after this long (default 10 s). */
  timeoutMs?: number;
  /** Sent as Idempotency-Key: the server does the action once however often it arrives. Makes retries safe. */
  idempotencyKey?: string;
  /** Extra attempts after offline / timeout / 5xx. Default 2 for GET and for writes with an idempotency key,
   *  0 for other writes: a retried write without a key can charge or book twice. */
  retries?: number;
}

/** A fresh key for one user action (one tap of Pay, Book, Send). Keep it for that action's retries. */
export function idempotencyKey(): string {
  const c = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
  if (c?.randomUUID) return c.randomUUID();
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

/* ------------------------------------------------------------ pure helpers (unit-tested) */

/** Base languages written right to left (Telegram ships Arabic, Persian and Hebrew; the rest come from
 *  language_code values users can have). "iw" is the legacy code for Hebrew. */
export const RTL_LANGUAGES = ['ar', 'fa', 'he', 'iw', 'ur', 'ps', 'ckb', 'sd', 'ug', 'yi', 'dv'] as const;

/** "ar", "fa-IR", "he_IL" -> rtl; everything else ltr. */
export function textDirection(tag: string): 'ltr' | 'rtl' {
  const base = tag.trim().toLowerCase().split(/[-_]/)[0];
  return (RTL_LANGUAGES as readonly string[]).includes(base) ? 'rtl' : 'ltr';
}

/** The first candidate the app has strings for: an exact tag ("pt-BR") wins, then the base language
 *  ("pt-BR" -> "pt"); candidates are tried in order, so the user's own choice goes first. */
export function pickLanguage(candidates: ReadonlyArray<string | null | undefined>, supported: readonly string[],
                             fallback: string): string {
  const norm = (t: string) => t.trim().replace(/_/g, '-').toLowerCase();
  const table = supported.map((t) => [norm(t), t] as const);
  for (const c of candidates) {
    if (!c) continue;
    const tag = norm(c);
    const exact = table.find(([n]) => n === tag);
    if (exact) return exact[1];
    const base = tag.split('-')[0];
    const byBase = table.find(([n]) => n === base) ?? table.find(([n]) => n.split('-')[0] === base);
    if (byBase) return byBase[1];
  }
  return fallback;
}

/** "7.10" >= "7.2": numeric per part, like Telegram.WebApp.isVersionAtLeast. */
export function versionAtLeast(have: string, need: string): boolean {
  const a = have.split('.').map(Number);
  const b = need.split('.').map(Number);
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const x = a[i] || 0;
    const y = b[i] || 0;
    if (x !== y) return x > y;
  }
  return true;
}

/** Android's User-Agent ends with "Telegram-Android/<ver> (<maker model>; Android <v>; SDK <n>; <CLASS>)". */
export function perfClass(userAgent: string): Perf {
  const m = userAgent.match(/Telegram-Android\/\S+ \([^)]*;\s*(LOW|AVERAGE|HIGH)\)/);
  return m ? (m[1].toLowerCase() as Perf) : 'unknown';
}

export function platformClass(platform: string | undefined): PlatformClass {
  if (!platform) return 'unknown';
  if (platform === 'ios') return 'ios';
  if (platform === 'android' || platform === 'android_x') return 'android';
  if (platform === 'tdesktop' || platform === 'macos' || platform === 'unigram') return 'desktop';
  if (platform.startsWith('web')) return 'web';
  return 'unknown';
}

/** Launch params live in location.hash (tgWebApp*) and start_param also in the query. Read them once,
    on the first line of the app, before a hash router rewrites the hash. */
export function readLaunchParams(loc: { hash: string; search: string }): Record<string, string> {
  const out: Record<string, string> = {};
  const hash = new URLSearchParams(loc.hash.replace(/^#/, ''));
  hash.forEach((v, k) => { if (k.startsWith('tgWebApp')) out[k] = v; });
  const start = new URLSearchParams(loc.search).get('tgWebAppStartParam');
  if (start !== null && !out.tgWebAppStartParam) out.tgWebAppStartParam = start;
  return out;
}

/** start_param is attacker-controlled text: accept only the patterns the app routes. */
export function parseStartParam(raw: string | undefined, routes: Record<string, RegExp>): { route: string; match: RegExpMatchArray } | null {
  if (!raw || !/^[A-Za-z0-9_-]{1,512}$/.test(raw)) return null;
  for (const [route, re] of Object.entries(routes)) {
    const match = raw.match(re);
    if (match) return { route, match };
  }
  return null;
}

/* ------------------------------------------------------------ the kit */

export interface MainButtonSpec {
  text: string;
  onClick: () => void | Promise<void>;
  active?: boolean;
  color?: string;
  textColor?: string;
  shine?: boolean;
  iconCustomEmojiId?: string; // 9.5+; ignored on older clients
}

export interface SecondaryButtonSpec extends MainButtonSpec {
  position?: 'left' | 'right' | 'top' | 'bottom';
}

/** Telegram's invoice status: a HINT only. The order is paid when the server says so (successful_payment). */
export type InvoiceStatus = 'paid' | 'cancelled' | 'failed' | 'pending' | 'unsupported';

export interface WatchOptions {
  timeoutMs?: number;                       // stop polling after this long (default 60 s)
  sleep?: (ms: number) => Promise<void>;    // injectable for tests
}

export interface Layer {
  id: string;
  kind: 'screen' | 'sheet';
  onBack?: () => void;
  /** Written by nav.push for screens: where the view underneath was scrolled. nav.pop scrolls back there. */
  scrollY?: number;
}

/** How the app asks to open (references/mini-apps/launch-and-lifecycle.md):
 *  'mobile' - fullscreen on iOS and Android (8.0+), the expanded sheet elsewhere; the skill's default;
 *  'always' - fullscreen on desktop too (games, video, maps); 'never' - the expanded sheet everywhere. */
export type FullscreenMode = 'mobile' | 'always' | 'never';
/** <html data-tma-fullscreen>: on, off (asked for the sheet, or the user left fullscreen), unsupported. */
export type FullscreenState = 'on' | 'off' | 'unsupported';

export interface LaunchOptions {
  fullscreen?: FullscreenMode;
}

export function createTma(env: Env = {}) {
  const w = (typeof window !== 'undefined' ? window : undefined) as unknown as
    { Telegram?: { WebApp?: WebAppLike }; location?: Location; navigator?: Navigator; document?: Document } | undefined;
  const tg: WebAppLike | null = env.webApp !== undefined ? env.webApp : (w?.Telegram?.WebApp ?? null);
  const root: RootLike | undefined = env.root ?? (w?.document?.documentElement as unknown as RootLike | undefined);
  const launch = readLaunchParams(env.location ?? w?.location ?? { hash: '', search: '' });
  const ua = env.userAgent ?? w?.navigator?.userAgent ?? '';
  const inTelegram = !!tg && typeof tg.initData === 'string' && tg.initData.length > 0;
  const has = (v: string): boolean => !!tg && typeof tg.isVersionAtLeast === 'function' && tg.isVersionAtLeast(v);
  const subs: Array<() => void> = [];

  /** Raw onEvent for any name, no version gate; a no-op outside Telegram or without onEvent / offEvent. */
  function on(name: string, cb: (...a: unknown[]) => void): () => void {
    if (!tg || typeof tg.onEvent !== 'function' || typeof tg.offEvent !== 'function') return () => {};
    tg.onEvent(name, cb);
    const off = () => tg.offEvent(name, cb);
    subs.push(off);
    return off;
  }

  /** Typed onEvent gated by the event's version (6.0 events need no gate). Returns the unsubscribe, or null when
   *  the event will never come here (older client, outside Telegram, no onEvent): take the fallback path.
   *  Subscribe before calling the method that triggers the event. */
  function listen<E extends TmaEventName>(name: E, cb: (payload: TmaEventMap[E]) => void): (() => void) | null {
    if (!tg || typeof tg.onEvent !== 'function' || typeof tg.offEvent !== 'function') return null;
    const since = EVENT_SINCE[name];
    if (since !== '6.0' && !has(since)) return null;
    return on(name, cb as (...a: unknown[]) => void);
  }

  /** A snapshot of the WebApp state fields; re-read it after fullscreenChanged, themeChanged or your own setter call. */
  function state(): TmaState {
    const read = <T>(key: keyof TmaState, type: 'boolean' | 'string'): T | null => {
      const v = tg?.[key];
      return typeof v === type && has(MEMBER_SINCE[`WebApp.${key}`]) ? (v as T) : null;
    };
    return {
      isFullscreen: read<boolean>('isFullscreen', 'boolean'),
      isOrientationLocked: read<boolean>('isOrientationLocked', 'boolean'),
      isVerticalSwipesEnabled: read<boolean>('isVerticalSwipesEnabled', 'boolean'),
      isClosingConfirmationEnabled: read<boolean>('isClosingConfirmationEnabled', 'boolean'),
      headerColor: read<string>('headerColor', 'string'),
      backgroundColor: read<string>('backgroundColor', 'string'),
      bottomBarColor: read<string>('bottomBarColor', 'string'),
    };
  }

  /* -- scheme, platform, performance class on <html> */
  function syncRoot(): void {
    if (!root) return;
    const scheme = tg?.colorScheme;
    if (scheme) {
      root.dataset.tmaScheme = scheme;
      root.style.colorScheme = scheme;
    }
    root.dataset.tmaPlatform = platformClass(tg?.platform);
    root.dataset.tmaPerf = perfClass(ua);
  }

  /* -- chrome colours: keywords follow the theme; literals are re-applied on themeChanged */
  let chromeSpec: { header?: SurfaceColor; background?: SurfaceColor; bottomBar?: ChromeColor } = {};
  const isHex = (c: string) => c.startsWith('#');
  /** One failing setter must not stop the others or the caller (a throw would also repeat on every themeChanged). */
  const attempt = (fn: () => void) => { try { fn(); } catch (err) { console.warn('[tma] chrome colour not applied', err); } };
  function applyChrome(): void {
    if (!tg) return;
    const { header, background, bottomBar } = chromeSpec;
    // setHeaderColor takes any #RRGGBB only from 6.9; before that only the bg / secondary_bg keywords.
    if (header && has('6.1') && (!isHex(header) || has('6.9'))) attempt(() => tg.setHeaderColor?.(header));
    if (background && has('6.1')) attempt(() => tg.setBackgroundColor?.(background));
    if (bottomBar && has('7.10')) attempt(() => tg.setBottomBarColor?.(bottomBar));
  }
  function chrome(spec: typeof chromeSpec): void {
    chromeSpec = { ...chromeSpec, ...spec };
    applyChrome();
  }

  syncRoot();
  on('themeChanged', () => { syncRoot(); applyChrome(); });

  /* -- haptics (the Taptic Engine on iPhone) by meaning: references/mini-apps/haptics-and-device.md.
     Silent below 6.1, outside Telegram and when the app turned them off; a burst of the same pattern within
     the gap plays once, so a drag or a fast list never buzzes continuously. */
  const HAPTIC_GAP_MS = 80;
  let hapticOn = true;
  let lastHaptic = { key: '', at: -Infinity };
  const now = env.now ?? (() => Date.now());
  function play(key: string, fire: (h: NonNullable<WebAppLike['HapticFeedback']>) => void): boolean {
    const h = tg?.HapticFeedback;
    if (!hapticOn || !h || !has('6.1')) return false;
    const t = now();
    if (key === lastHaptic.key && t - lastHaptic.at < HAPTIC_GAP_MS) return false;
    lastHaptic = { key, at: t };
    fire(h);
    return true;
  }
  const haptic = {
    /** The selection changed (picker, segmented control, toggle, chip, slider step). Not on confirming it. */
    select: (): boolean => play('select', (h) => h.selectionChanged()),
    /** A light impact: a tap that commits something small (a quick action, a stepper). */
    tap: (): boolean => play('impact:light', (h) => h.impactOccurred('light')),
    /** An impact of a given weight: light, medium, heavy, rigid (hard snap) or soft (elastic). */
    impact: (style: ImpactStyle): boolean => play(`impact:${style}`, (h) => h.impactOccurred(style)),
    /** The outcome of a task: success, warning or error. */
    notify: (type: NotificationType): boolean => play(`notify:${type}`, (h) => h.notificationOccurred(type)),
    success: (): boolean => play('notify:success', (h) => h.notificationOccurred('success')),
    warning: (): boolean => play('notify:warning', (h) => h.notificationOccurred('warning')),
    error: (): boolean => play('notify:error', (h) => h.notificationOccurred('error')),
    /** An in-app switch for people who find vibration distracting (games, long sessions). */
    setEnabled(on: boolean): void { hapticOn = on; },
    get enabled(): boolean { return hapticOn; },
  };

  /* -- motion sensors (8.0): one subscription per sensor; stops when the app is hidden and on dispose */
  const SENSORS: Record<MotionSensor, { obj: 'Accelerometer' | 'Gyroscope' | 'DeviceOrientation'; event: string }> = {
    accelerometer: { obj: 'Accelerometer', event: 'accelerometerChanged' },
    gyroscope: { obj: 'Gyroscope', event: 'gyroscopeChanged' },
    orientation: { obj: 'DeviceOrientation', event: 'deviceOrientationChanged' },
  };
  /** Starts a sensor (refresh 20-1000 ms, default 100) and calls onData with each reading. Returns stop(), or
   *  null when the client is older than 8.0 or has no such sensor: the app keeps a non-motion fallback. */
  function motion(sensor: MotionSensor, onData: (r: MotionReading) => void,
                  opts: { refreshMs?: number; absolute?: boolean } = {}): (() => void) | null {
    const spec = SENSORS[sensor];
    const s = tg?.[spec.obj];
    if (!s || !has('8.0')) return null;
    const rate = Math.min(1000, Math.max(20, Math.round(opts.refreshMs ?? 100)));
    const params: Record<string, unknown> = { refresh_rate: rate };
    if (sensor === 'orientation' && opts.absolute) params.need_absolute = true;
    const read = () => onData(sensor === 'orientation'
      ? { alpha: s.alpha, beta: s.beta, gamma: s.gamma, absolute: s.absolute }
      : { x: s.x, y: s.y, z: s.z });
    const offData = on(spec.event, read);
    const offHide = on('deactivated', () => { if (s.isStarted) s.stop(); });
    const offShow = on('activated', () => { if (!s.isStarted) s.start(params); });
    s.start(params);
    let stopped = false;
    return () => {
      if (stopped) return;
      stopped = true;
      offData(); offHide(); offShow();
      if (s.isStarted) s.stop();
    };
  }

  /** Asks for the location (8.0) after init. Resolves null when unavailable or refused; the app then offers a
   *  manual choice. Call it from a user action that explains why. */
  function location(): Promise<LocationData | null> {
    const lm = tg?.LocationManager;
    if (!lm || !has('8.0')) return Promise.resolve(null);
    const ask = () => new Promise<LocationData | null>((resolve) => {
      if (!lm.isLocationAvailable) { resolve(null); return; }
      lm.getLocation((d) => resolve(d ?? null));
    });
    return lm.isInited ? ask() : new Promise((resolve) => lm.init(() => { void ask().then(resolve); }));
  }

  /* -- bottom buttons: one spec per screen; progress while the handler runs */
  type Slot = { cb: (() => void) | null; spec: MainButtonSpec | null; busy: boolean };
  function bindBottom(btn: BottomButtonLike | undefined, spec: MainButtonSpec | null, extra: Record<string, unknown>,
                      prev: Slot, flag?: string): void {
    prev.spec = spec;
    if (!btn) return;
    if (prev.cb) btn.offClick(prev.cb);
    prev.cb = null;
    if (!spec) {
      btn.setParams({ is_visible: false });
      if (flag && root) root.dataset[flag] = 'hidden';
      return;
    }
    const params: Record<string, unknown> = { text: spec.text, is_visible: true, is_active: spec.active !== false, ...extra };
    if (spec.color) params.color = spec.color;
    if (spec.textColor) params.text_color = spec.textColor;
    if (spec.shine !== undefined && has('7.10')) params.has_shine_effect = spec.shine;
    if (spec.iconCustomEmojiId && has('9.5')) params.icon_custom_emoji_id = spec.iconCustomEmojiId;
    btn.setParams(params);
    const cb = async () => {
      if (prev.busy) return; // a second tap while the first one runs (double orders) is ignored
      prev.busy = true;
      haptic.tap();
      btn.showProgress(false);
      try { await spec.onClick(); } finally {
        btn.hideProgress();
        // hideProgress() re-enables the button in Telegram's script: restore what the CURRENT spec wants,
        // which the handler (or a tap meanwhile) may have changed.
        if (prev.spec) btn.setParams({ is_active: prev.spec.active !== false });
        prev.busy = false;
      }
    };
    prev.cb = () => { void cb(); };
    btn.onClick(prev.cb);
    if (flag && root) root.dataset[flag] = 'visible';
  }
  const fallback: FallbackButtonLike | null = env.fallbackButton !== undefined ? env.fallbackButton
    : ((w?.document?.querySelector('[data-tma-fallback="main-button"]') as unknown as FallbackButtonLike | null) ?? null);
  function bindFallback(spec: MainButtonSpec | null): void {
    if (!fallback) return;
    fallback.hidden = !spec;
    fallback.textContent = spec ? spec.text : '';
    fallback.disabled = spec ? spec.active === false : true;
    fallback.onclick = spec ? async () => {
      if (fallbackBusy) return;
      fallbackBusy = true;
      fallback.disabled = true;
      try { await spec.onClick(); } finally {
        fallbackBusy = false;
        fallback.disabled = mainPrev.spec ? mainPrev.spec.active === false : true;
      }
    } : null;
  }
  let fallbackBusy = false;
  const mainPrev: Slot = { cb: null, spec: null, busy: false };
  const secondaryPrev: Slot = { cb: null, spec: null, busy: false };
  function mainButton(spec: MainButtonSpec | null): void {
    bindBottom(tg?.MainButton, spec, {}, mainPrev, 'tmaMainButton');
    if (!inTelegram) bindFallback(spec);
  }
  /** SecondaryButton is 7.10+. Returns false on older clients: render the action in the content instead. */
  function secondaryButton(spec: SecondaryButtonSpec | null): boolean {
    if (!has('7.10')) return false;
    bindBottom(tg?.SecondaryButton, spec, spec?.position ? { position: spec.position } : {}, secondaryPrev);
    return true;
  }

  /* -- scroll positions: a screen or tab comes back where the user left it */
  let lastY = 0;
  const win = w as unknown as {
    scrollY?: number; scrollTo?(x: number, y: number): void; requestAnimationFrame?(cb: () => void): number;
    addEventListener?(t: string, cb: () => void, o?: unknown): void; removeEventListener?(t: string, cb: () => void): void;
  } | undefined;
  const scroller: ScrollerLike | null = env.scroller !== undefined ? env.scroller : win?.scrollTo ? (() => {
    lastY = win.scrollY ?? 0;
    const track = () => { lastY = win.scrollY ?? 0; };
    win.addEventListener?.('scroll', track, { passive: true });
    subs.push(() => win.removeEventListener?.('scroll', track));
    return {
      // Where the page is now; 0 here while the last scroll event saw more means the app already reset the view
      // in this tap (hid the list, scrollTo(0, 0)) before telling the kit: the position before that counts.
      y: () => (win.scrollY ?? 0) || lastY,
      to: (y: number) => win.scrollTo!(0, y),
      frame: (cb: () => void) => { if (win.requestAnimationFrame) win.requestAnimationFrame(cb); else setTimeout(cb, 0); },
    };
  })() : null;
  /** Per-key positions for tabs: leave(tab) before switching, enter(tab) after showing it; top() for a tap on
   *  the tab that is already selected (it scrolls that tab to the top, as native tab bars do). */
  function scrollMemory() {
    const pos = new Map<string, number>();
    return {
      top(): void { scroller?.to(0); },
      leave(key: string): void { if (scroller) pos.set(key, scroller.y()); },
      enter(key: string): void {
        if (!scroller) return;
        const y = pos.get(key) ?? 0;
        scroller.frame(() => scroller.to(y));
      },
    };
  }

  /* -- one navigation stack: screens and sheets; BackButton mirrors its depth.
     Telegram's BackButton (6.1+) also receives Android's system back. Where there is none (plain browser, older
     clients) the [data-tma-fallback="back-button"] element stands in, so no screen is a dead end. */
  const stack: Layer[] = [];
  const nativeBack = inTelegram && !!tg?.BackButton && has('6.1');
  const backHandler = () => {
    const top = stack[stack.length - 1];
    if (top) top.onBack?.();
  };
  if (nativeBack) tg!.BackButton!.onClick(backHandler); // nativeBack implies both
  subs.push(() => { if (nativeBack) tg!.BackButton!.offClick(backHandler); });
  const fallbackBack: FallbackButtonLike | null = nativeBack ? null : env.fallbackBack !== undefined ? env.fallbackBack
    : ((w?.document?.querySelector('[data-tma-fallback="back-button"]') as unknown as FallbackButtonLike | null) ?? null);
  if (fallbackBack) fallbackBack.onclick = backHandler;

  /* -- vertical swipes (7.7): a sheet's own drag and scroll must not minimise the app, so swipes are off while a
     sheet is open; verticalSwipes(false) keeps them off for apps with their own vertical gestures. */
  let swipesWanted = true;
  let swipesApplied = true; // Telegram's default
  function applySwipes(): void {
    const on = swipesWanted && !stack.some((l) => l.kind === 'sheet');
    if (on === swipesApplied || !has('7.7')) return;
    swipesApplied = on;
    if (on) tg?.enableVerticalSwipes?.(); else tg?.disableVerticalSwipes?.();
  }
  function verticalSwipes(on: boolean): boolean {
    swipesWanted = on;
    applySwipes();
    return has('7.7');
  }

  function syncBack(): void {
    applySwipes();
    if (fallbackBack) fallbackBack.hidden = stack.length === 0;
    if (!nativeBack) return;
    if (stack.length > 0) tg!.BackButton!.show();
    else tg!.BackButton!.hide();
  }
  const nav = {
    /** Push before switching the view: the kit notes the scroll position of the screen underneath. */
    push(layer: Layer): void {
      if (layer.kind === 'screen' && scroller && layer.scrollY === undefined) layer.scrollY = scroller.y();
      stack.push(layer);
      syncBack();
    },
    /** Removes the layer (the top one without an id). A screen's view underneath scrolls back to where it was. */
    pop(id?: string): Layer | undefined {
      const i = id ? stack.map((l) => l.id).lastIndexOf(id) : stack.length - 1;
      const [removed] = i >= 0 ? stack.splice(i, 1) : [];
      syncBack();
      const y = removed?.kind === 'screen' ? removed.scrollY : undefined;
      if (y !== undefined && scroller) scroller.frame(() => scroller.to(y));
      return removed;
    },
    /** Drops every layer without restoring scroll: a finished flow (order placed) starts its next screen fresh. */
    reset(): void { stack.length = 0; syncBack(); },
    /** What the BackButton does: the top layer's onBack. */
    back(): void { backHandler(); },
    get depth(): number { return stack.length; },
    get top(): Layer | undefined { return stack[stack.length - 1]; },
  };

  /* -- launch: fullscreen on phones where the client has it, the expanded sheet everywhere else */
  let fullscreenState: FullscreenState = 'unsupported';
  function markFullscreen(s: FullscreenState): void {
    fullscreenState = s;
    if (root) root.dataset.tmaFullscreen = s;
  }
  /** Call once at start, before ready(). expand() first, so a half-height or compact launch (and every client
   *  older than 8.0 or without fullscreen) still gets the full height; then requestFullscreen where the mode asks
   *  for it. Telegram's safe-area variables follow (the kit's --tma-safe-* already add them). */
  function start(opts: LaunchOptions = {}): void {
    const mode = opts.fullscreen ?? 'mobile';
    if (!tg || !inTelegram) { markFullscreen('unsupported'); return; }
    attempt(() => tg.expand?.());
    if (!has('8.0') || typeof tg.requestFullscreen !== 'function') { markFullscreen('unsupported'); return; }
    const sync = () => markFullscreen(tg.isFullscreen ? 'on' : 'off');
    listen('fullscreenChanged', sync);
    listen('fullscreenFailed', (e) => { if (e?.error === 'UNSUPPORTED') markFullscreen('unsupported'); else sync(); });
    const platform = platformClass(tg.platform);
    const wanted = mode === 'always' || (mode === 'mobile' && (platform === 'ios' || platform === 'android'));
    sync();
    if (!wanted || tg.isFullscreen) return;
    try { tg.requestFullscreen(); } catch { markFullscreen('unsupported'); }
  }

  /* -- settings item in the ⋯ menu (7.0+) */
  let settingsCb: (() => void) | null = null;
  function settings(cb: (() => void) | null): void {
    if (!tg?.SettingsButton || !has('7.0')) return;
    if (settingsCb) tg.SettingsButton.offClick(settingsCb); // one handler at a time
    settingsCb = cb;
    if (cb) { tg.SettingsButton.onClick(cb); tg.SettingsButton.show(); }
    else tg.SettingsButton.hide();
  }
  subs.push(() => { if (settingsCb) tg?.SettingsButton?.offClick(settingsCb); });

  /* -- unsaved input */
  function closingConfirmation(on: boolean): void {
    if (!has('6.2')) return;
    if (on) tg?.enableClosingConfirmation?.();
    else tg?.disableClosingConfirmation?.();
  }

  /* -- native confirm (6.2+); the caller supplies an in-content fallback */
  function confirm(message: string, fallback: () => Promise<boolean>): Promise<boolean> {
    if (tg?.showConfirm && has('6.2')) {
      return new Promise((resolve) => tg.showConfirm!(message, (ok) => resolve(!!ok)));
    }
    return fallback();
  }

  /** True when the bot may message the user (receipts, reminders): already allowed, or allowed now (6.9). */
  function writeAccess(): Promise<boolean> {
    if (tg?.initDataUnsafe?.user?.allows_write_to_pm) return Promise.resolve(true);
    if (!tg?.requestWriteAccess || !has('6.9')) return Promise.resolve(false);
    return new Promise((resolve) => tg.requestWriteAccess!((ok) => resolve(!!ok)));
  }

  /** Telegram's dialog to pick or create a chat for a PreparedKeyboardButton the bot saved (9.6). Resolves the
   *  client's boolean, or null below 9.6: then the bot sends a request_chat reply keyboard instead. */
  function requestChat(reqId: string): Promise<boolean | null> {
    const ask = tg?.requestChat;
    if (!ask || !has(MEMBER_SINCE['WebApp.requestChat'])) return Promise.resolve(null);
    return new Promise((resolve) => {
      try { ask.call(tg, reqId, (ok) => resolve(!!ok)); } catch { resolve(false); } // e.g. an unknown or expired id
    });
  }

  /* -- storage: promise wrappers; null when the client has no such storage */
  function wrap(s: StorageLike | undefined, since: string) {
    if (!s || !has(since)) return null;
    return {
      // CloudStorage returns '' for a missing key: normalise to null like the in-memory fallback
      get: (k: string) => new Promise<string | null>((res, rej) => s.getItem(k, (e, v) => (e ? rej(e) : res(v ? v : null)))),
      set: (k: string, v: string) => new Promise<void>((res, rej) => s.setItem(k, v, (e) => (e ? rej(e) : res()))),
      remove: (k: string) => new Promise<void>((res, rej) => s.removeItem(k, (e) => (e ? rej(e) : res()))),
    };
  }
  /* Several keys at once: getMany -> { key: value | null }, removeMany -> removed, keys -> every key or null
     when the storage cannot list them. Without a batch method the kit makes one call per key. */
  type Single = NonNullable<ReturnType<typeof wrap>>;
  const pick = (keys: readonly string[], values: Record<string, unknown> | null | undefined) =>
    Object.fromEntries(keys.map((k) => {
      const v = values?.[k];
      return [k, typeof v === 'string' && v ? v : null];
    })) as Record<string, string | null>;
  const getEach = async (one: Single, keys: readonly string[]) =>
    pick(keys, Object.fromEntries(await Promise.all(keys.map(async (k) => [k, await one.get(k)] as const))));
  const removeEach = async (one: Single, keys: readonly string[]) => {
    await Promise.all(keys.map((k) => one.remove(k)));
    return true;
  };
  function batch(s: CloudStorageLike, one: Single) {
    const getItems = s.getItems && has(MEMBER_SINCE['CloudStorage.getItems']) ? s.getItems.bind(s) : null;
    const getKeys = s.getKeys && has(MEMBER_SINCE['CloudStorage.getKeys']) ? s.getKeys.bind(s) : null;
    const removeItems = s.removeItems && has(MEMBER_SINCE['CloudStorage.removeItems']) ? s.removeItems.bind(s) : null;
    return {
      getMany: (keys: string[]): Promise<Record<string, string | null>> => {
        if (!keys.length) return Promise.resolve({});
        if (!getItems) return getEach(one, keys);
        return new Promise((res, rej) => getItems(keys, (e, v) => (e ? rej(e) : res(pick(keys, v)))));
      },
      removeMany: (keys: string[]): Promise<boolean> => {
        if (!keys.length) return Promise.resolve(true);
        if (!removeItems) return removeEach(one, keys);
        // false only when the client says so: the page gives the boolean, a missing one is not a refusal
        return new Promise((res, rej) => removeItems(keys, (e, removed) => (e ? rej(e) : res(removed !== false))));
      },
      keys: (): Promise<string[] | null> => {
        if (!getKeys) return Promise.resolve(null);
        return new Promise((res, rej) => getKeys((e, k) => (e ? rej(e) : res(Array.isArray(k) ? k : []))));
      },
    };
  }

  /** Non-secret data synced across the user's devices: CloudStorage (6.9); in memory outside Telegram.
      Never localStorage. DeviceStorage (9.0) and SecureStorage (9.0) are below. */
  const mem = new Map<string, string>();
  function store() {
    const cloud = tg?.CloudStorage;
    const native = wrap(cloud, '6.9');
    if (cloud && native) return { ...native, ...batch(cloud, native) };
    const local: Single = {
      get: async (k: string) => mem.get(k) || null, // '' reads as missing, as CloudStorage returns it
      set: async (k: string, v: string) => { mem.set(k, v); },
      remove: async (k: string) => { mem.delete(k); },
    };
    return {
      ...local,
      getMany: async (keys: string[]) => getEach(local, keys),
      removeMany: async (keys: string[]) => removeEach(local, keys),
      keys: async (): Promise<string[] | null> => [...mem.keys()],
    };
  }
  const deviceStore = () => wrap(tg?.DeviceStorage, '9.0');
  /** Secrets in the Keychain / Keystore (9.0). lookup() tells a missing key that restore() can bring back; restore()
   *  asks the user and rejects when they decline, resolves null when the client has no restoreItem. */
  function secureStore() {
    const s = tg?.SecureStorage;
    const one = wrap(s, '9.0');
    if (!s || !one) return null;
    const restoreItem = s.restoreItem && has(MEMBER_SINCE['SecureStorage.restoreItem']) ? s.restoreItem.bind(s) : null;
    return {
      ...one,
      lookup: (k: string) => new Promise<{ value: string | null; canRestore: boolean }>((res, rej) =>
        s.getItem(k, (e, v, canBeRestored) => (e ? rej(e) : res({ value: v ? v : null, canRestore: !v && canBeRestored === true })))),
      restore: (k: string): Promise<string | null> => {
        if (!restoreItem) return Promise.resolve(null);
        return new Promise((res, rej) => restoreItem(k, (e, v) => (e ? rej(e) : res(v ? v : null))));
      },
    };
  }

  /* -- payments (references/mini-apps/payments.md): open the server's invoice link, then ask the server */
  /** Opens an invoice link from a tap. Resolves with Telegram's status, which is only a hint: never unlock
      anything from it; call watchOrder() and draw the server's order state. */
  function pay(link: string): Promise<InvoiceStatus> {
    if (!tg?.openInvoice || !has('6.1')) return Promise.resolve('unsupported');
    return new Promise((resolve) => {
      try {
        tg.openInvoice!(link, (status) => {
          resolve((['paid', 'cancelled', 'failed', 'pending'] as const).includes(status as InvoiceStatus)
            ? (status as InvoiceStatus) : 'failed');
        });
      } catch {
        resolve('failed'); // invalid link or an old client: the caller shows the server's state anyway
      }
    });
  }

  /** Polls the server's view of an order until `isFinal` holds or the timeout passes. Backs off from 1 s to
      10 s; a return to the app (activated) triggers an immediate check. */
  async function watchOrder<T>(fetchState: () => Promise<T>, isFinal: (state: T) => boolean,
                               opts: WatchOptions = {}): Promise<{ state: T | null; timedOut: boolean }> {
    const timeout = opts.timeoutMs ?? 60000;
    let wake: (() => void) | null = null;
    const nap = opts.sleep ?? ((ms: number) => new Promise<void>((r) => { const t = setTimeout(r, ms); wake = () => { clearTimeout(t); r(); }; }));
    const offActive = on('activated', () => wake?.());
    const started = Date.now();
    let delay = 1000;
    let state: T | null = null;
    try {
      while (true) {
        try { state = await fetchState(); } catch { /* a failed check is retried, not fatal */ }
        if (state !== null && isFinal(state)) return { state, timedOut: false };
        if (Date.now() - started + delay > timeout) return { state, timedOut: true };
        await nap(delay);
        delay = Math.min(delay * 2, 10000);
      }
    } finally {
      offActive();
    }
  }

  /* -- language and direction: references/mini-apps/accessibility-and-language.md §7.
     Order: the user's choice in the app, Telegram's language_code, the browser's languages, the fallback.
     Sets <html lang dir> so screen readers pick the voice and the kit's logical properties mirror. */
  function locale(supported: readonly string[], opts: { fallback?: string; override?: string | null } = {}):
      { lang: string; dir: 'ltr' | 'rtl' } {
    const browser = env.languages ?? (w?.navigator?.languages as readonly string[] | undefined) ?? [];
    const lang = pickLanguage([opts.override, tg?.initDataUnsafe?.user?.language_code, ...browser],
                              supported, opts.fallback ?? supported[0] ?? 'en');
    const dir = textDirection(lang);
    if (root) { root.lang = lang; root.dir = dir; }
    return { lang, dir };
  }

  /* -- the app's own server: references/mini-apps/forms-and-data.md §5-6.
     Every request carries the raw initData (the server verifies it; security.md §2), fails in one of five
     kinds the screen can explain, times out, and retries only what is safe to repeat. */
  const doFetch = env.fetch ?? ((url: string, init: Record<string, unknown>) =>
    (globalThis.fetch as unknown as (u: string, i: Record<string, unknown>) => Promise<ResponseLike>)(url, init));
  const sleep = env.sleep ?? ((ms: number) => new Promise<void>((r) => setTimeout(r, ms)));
  async function api<T = unknown>(path: string, opts: ApiOptions = {}): Promise<T> {
    const method = opts.method ?? (opts.body === undefined ? 'GET' : 'POST');
    const safe = method === 'GET' || !!opts.idempotencyKey;
    const retries = Math.max(0, opts.retries ?? (safe ? 2 : 0));
    const headers: Record<string, string> = { Authorization: `tma ${tg?.initData ?? ''}` };
    if (opts.body !== undefined) headers['Content-Type'] = 'application/json';
    if (opts.idempotencyKey) headers['Idempotency-Key'] = opts.idempotencyKey;
    let last: ApiError = new ApiError('offline');
    for (let attempt = 0; attempt <= retries; attempt++) {
      if (attempt > 0) await sleep(attempt === 1 ? 600 : 1800);
      const ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
      let timedOut = false;
      const timer = setTimeout(() => { timedOut = true; ctl?.abort(); }, opts.timeoutMs ?? 10000);
      try {
        const res = await doFetch(path, {
          method, headers, signal: ctl?.signal,
          body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
        });
        const text = await res.text();
        let data: unknown = null;
        try { data = text ? JSON.parse(text) : null; } catch { data = text; }
        if (res.ok) return data as T;
        if (res.status === 401 || res.status === 403) throw new ApiError('session', res.status, data);
        if (res.status < 500 && res.status !== 408 && res.status !== 429) throw new ApiError('rejected', res.status, data);
        last = new ApiError('server', res.status, data);
      } catch (err) {
        if (err instanceof ApiError && err.kind !== 'server') throw err;
        last = err instanceof ApiError ? err : new ApiError(timedOut ? 'timeout' : 'offline');
      } finally {
        clearTimeout(timer);
      }
    }
    throw last;
  }

  /** Closes the on-screen keyboard after a submit (9.1); below 9.1 blurs the field. */
  function hideKeyboard(): void {
    if (tg?.hideKeyboard && has('9.1')) { tg.hideKeyboard(); return; }
    (w?.document?.activeElement as { blur?: () => void } | null | undefined)?.blur?.();
  }

  /** Call once the first useful screen is drawn (Telegram then hides its loading screen). */
  function ready(): void { tg?.ready(); }

  function dispose(): void {
    mainButton(null);
    if (has('7.10')) secondaryButton(null);
    while (subs.length) subs.pop()!();
  }

  return {
    tg, inTelegram, launch, start, has, on, listen, state, chrome, haptic, mainButton, secondaryButton,
    nav, scrollMemory, verticalSwipes, settings,
    closingConfirmation, confirm, store, deviceStore, secureStore, pay, watchOrder, writeAccess, requestChat, motion, location,
    locale, api, hideKeyboard, ready, dispose,
    get initData(): string { return tg?.initData ?? ''; },
    get fullscreen(): FullscreenState { return fullscreenState; },
  };
}

export type Tma = ReturnType<typeof createTma>;
