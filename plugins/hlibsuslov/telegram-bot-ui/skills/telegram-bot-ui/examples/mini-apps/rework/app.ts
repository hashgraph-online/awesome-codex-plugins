// FitHub, reworked: the gym-booking app of tests/fixtures/miniapp_rework/before on the kit, native style.
//   Classes    - schedule rows, time first (class entity, L21), full classes listed and dimmed (L08)
//   Class      - detail with key facts; MainButton "Book 07:00 class · ⭐ 120" (L01, L16)
//   Trainers   - rows with a round avatar; detail lists the trainer's classes
//   Membership - plan rows; plan detail with features and "Subscribe · ⭐ N / month" (L25)
//   Profile    - name from Telegram, notifications switch in CloudStorage
// Kept from the original: the class and trainer data, POST /api/checkout, openInvoice, the CloudStorage
// keys "lastClass" and "notif". Changed: the request sends ids only and initData in the header; the
// result comes from the server's order (GET /api/orders/<id>), not from the invoice status.
// Text goes through textContent only.
import { createTma, parseStartParam } from '../_kit/tma.ts';
import { starsText } from '../_kit/tg-values.ts';

type Cls = { id: string; title: string; time: string; trainer: string; price: number; spots: number };
type Trainer = { name: string; tag: string };
type Plan = { id: string; name: string; price: number; features: string[]; recommended?: boolean };
type Order = { id: string; status: 'open' | 'paid' | 'delivered' | 'failed' | 'expired' | 'refunded'; reason?: string };

const tma = createTma();
const $ = (id: string) => document.getElementById(id) as HTMLElement;
const ICONS = '../_kit/icons.svg';
// Display only: the server identifies the user from the verified initData, never from this.
const user = (tma.tg as unknown as { initDataUnsafe?: { user?: { first_name?: string; last_name?: string } } } | null)?.initDataUnsafe?.user;

const CLASSES: Cls[] = [
  { id: 'hiit', title: 'HIIT Blast', time: '07:00', trainer: 'Mira', price: 120, spots: 3 },
  { id: 'yoga', title: 'Morning Yoga', time: '08:30', trainer: 'Leo', price: 90, spots: 0 },
  { id: 'box', title: 'Boxing Basics', time: '18:00', trainer: 'Sam', price: 150, spots: 8 },
];
const TRAINERS: Trainer[] = [{ name: 'Mira', tag: 'Strength' }, { name: 'Leo', tag: 'Yoga' }, { name: 'Sam', tag: 'Boxing' }];
const PLANS: Plan[] = [
  { id: 'basic', name: 'Basic', price: 250, features: ['8 classes a month'] },
  { id: 'pro', name: 'Pro', price: 450, features: ['Unlimited classes'], recommended: true },
];

/* ---------------------------------------------------------------- DOM helpers: text only */
type Kid = Node | string | null | false;
function h(tag: string, attrs: Record<string, string | boolean | EventListener> = {}, ...kids: Kid[]): HTMLElement {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (typeof v === 'function') el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, '');
    else if (v !== false) el.setAttribute(k, v);
  }
  for (const kid of kids) if (kid) el.append(kid);
  return el;
}
function svgUse(cls: string, name: string): SVGSVGElement {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', cls); svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', `${ICONS}#i-${name}`);
  svg.append(use);
  return svg;
}
const chevron = () => svgUse('tma-cell__chevron', 'chevron-right');
/** T1: the Stars sign before a whole number; screen readers hear "120 Stars". */
// aria-label on a plain span is ignored by some screen readers (ARIA: generic role), so the words are hidden text.
const stars = (n: number, period = '') => h('span', { class: 'tma-amount is-stars' },
  svgUse('tma-star', 'stars-gold'), String(n), h('span', { class: 'tma-sr-only' }, ' Stars'),
  period ? h('span', { class: 'tma-price__period' }, ` ${period}`) : null);
const initials = (name: string, cls = '') => h('span', { class: `tma-avatar ${cls}`, 'aria-hidden': 'true' }, name.slice(0, 1).toUpperCase());
const spotsText = (c: Cls) => (c.spots === 0 ? 'Full' : c.spots === 1 ? '1 spot left' : `${c.spots} spots left`);

/* ---------------------------------------------------------------- navigation: tab roots, one stack of screens */
type Tab = 'classes' | 'trainers' | 'membership' | 'profile';
let tab: Tab = 'classes';
const screens: Array<() => void> = []; // render functions of the pushed screens, top last

const tabScroll = tma.scrollMemory(); // each tab comes back where the user left it
function setTab(t: Tab): void {
  if (t !== tab) tabScroll.leave(tab);
  tab = t;
  for (const b of document.querySelectorAll<HTMLButtonElement>('[data-tab]')) b.setAttribute('aria-selected', String(b.dataset.tab === t));
  renderRoot();
  tabScroll.enter(t);
}
for (const b of document.querySelectorAll<HTMLButtonElement>('[data-tab]')) {
  b.onclick = () => { if (b.dataset.tab !== tab) { tma.haptic.select(); setTab(b.dataset.tab as Tab); } else tabScroll.top(); };
}
function show(id: 'root' | 'detail', back = false): void {
  $('root').hidden = id !== 'root';
  $('detail').hidden = id !== 'detail';
  $(id).classList.toggle('is-back', back);
  $('tabbar').hidden = id !== 'root';
  window.scrollTo(0, 0);
}
/** Pushes a level-2 screen; BackButton (and Android back) pops it. */
function push(render: () => void): void {
  screens.push(render);
  tma.nav.push({ id: `screen-${screens.length}`, kind: 'screen', onBack: pop });
  render();
  show('detail');
}
function pop(): void {
  screens.pop();
  tma.nav.pop();
  tma.mainButton(null);
  const prev = screens[screens.length - 1];
  if (prev) { prev(); show('detail', true); } else { renderRoot(); show('root', true); }
}
function detail(...kids: Kid[]): void {
  $('detail').replaceChildren(...kids.filter(Boolean) as Node[]);
}

/* ---------------------------------------------------------------- tab roots */
function renderRoot(): void {
  tma.mainButton(null); // tab roots have no primary action; the tab bar stays visible
  const root = $('root');
  const title = (t: string) => h('header', { class: 'tma-header' }, h('h1', { class: 'tma-large-title' }, t));
  if (tab === 'classes') {
    root.replaceChildren(title('Classes'), section('Today', classList(CLASSES)));
  } else if (tab === 'trainers') {
    root.replaceChildren(title('Trainers'), section('', h('ul', { class: 'tma-list' }, ...TRAINERS.map((t) => {
      const today = CLASSES.filter((c) => c.trainer === t.name).length;
      return h('li', {}, h('button', { class: 'tma-cell is-2', type: 'button', onclick: (() => push(() => trainerScreen(t))) as EventListener },
        initials(t.name, 'is-48'),
        h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-cell__title' }, t.name),
          h('span', { class: 'tma-cell__subtitle' }, `${t.tag} · ${today === 1 ? '1 class' : `${today} classes`} today`)),
        chevron()));
    }))));
  } else if (tab === 'membership') {
    root.replaceChildren(title('Membership'), section('Plans', h('ul', { class: 'tma-list' }, ...PLANS.map((p) =>
      h('li', {}, h('button', { class: 'tma-cell is-2', type: 'button', onclick: (() => push(() => planScreen(p))) as EventListener },
        h('span', { class: 'tma-cell__body' },
          h('span', { class: 'tma-cell__title' }, p.recommended ? `${p.name} · Most chosen` : p.name),
          h('span', { class: 'tma-cell__subtitle' }, p.features[0])),
        h('span', { class: 'tma-cell__after' }, stars(p.price, '/ month')), chevron())))),
      'Paid in Telegram Stars, renewed monthly until you cancel.'));
  } else {
    root.replaceChildren(title('Profile'), profile());
  }
}
function section(header: string, body: HTMLElement, footer = ''): HTMLElement {
  return h('section', { class: 'tma-section' },
    header ? h('h2', { class: 'tma-section__header' }, header) : null, body,
    footer ? h('p', { class: 'tma-section__footer' }, footer) : null);
}
function classList(items: Cls[]): HTMLElement {
  if (!items.length) {
    return h('div', { class: 'tma-placeholder' }, h('p', { class: 'tma-placeholder__title' }, 'No classes today'),
      h('p', { class: 'tma-placeholder__text' }, 'New classes appear here when the schedule opens.'));
  }
  return h('ul', { class: 'tma-list' }, ...items.map((c) => h('li', {},
    h('button', { class: 'tma-cell is-2', type: 'button', 'aria-disabled': c.spots === 0 ? 'true' : false,
      onclick: (() => push(() => classScreen(c))) as EventListener },
      h('span', { class: 'tma-cell__time' }, c.time),
      h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-cell__title' }, c.title),
        h('span', { class: 'tma-cell__subtitle' }, `${c.trainer} · ${spotsText(c)}`)),
      h('span', { class: 'tma-cell__after' }, stars(c.price)), chevron()))));
}

/* ---------------------------------------------------------------- profile: name and a setting */
function profile(): HTMLElement {
  const name = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || 'Athlete';
  const sw = h('input', { class: 'tma-switch', type: 'checkbox', role: 'switch', 'aria-describedby': 'notif-f' }) as HTMLInputElement;
  const store = tma.store();
  void store.get('notif').then((v) => { sw.checked = v === 'true'; }).catch(() => {});
  sw.onchange = () => {
    tma.haptic.select();
    store.set('notif', String(sw.checked)).catch(() => { sw.checked = !sw.checked; toast('Not saved. Try again.'); });
  };
  return h('div', { class: 'tma-stack' },
    h('ul', { class: 'tma-list' }, h('li', {}, h('div', { class: 'tma-cell is-2' }, initials(name, 'is-56'),
      h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-cell__title tma-headline' }, name),
        h('span', { class: 'tma-cell__subtitle' }, 'Your Telegram name'))))),
    h('section', { class: 'tma-section' },
      h('ul', { class: 'tma-list' }, h('li', {}, h('label', { class: 'tma-cell' },
        h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-cell__title' }, 'Notifications')), sw))),
      h('p', { class: 'tma-section__footer', id: 'notif-f' }, 'Booking confirmations and a reminder an hour before class, in the chat with the bot.')));
}

/* ---------------------------------------------------------------- class detail and booking */
function classScreen(c: Cls): void {
  const status = h('p', { class: 'tma-footnote', role: 'status', style: 'margin:0;padding:0 var(--tma-s4)' });
  detail(
    h('header', { class: 'tma-header' }, h('h1', { class: 'tma-title2' }, c.title),
      h('p', { class: 'tma-subhead tma-hint', style: 'margin:var(--tma-s1) 0 0' }, `Today · ${c.time} · with ${c.trainer}`)),
    h('div', { class: 'tma-stack' },
      h('dl', { class: 'tma-kv' },
        h('div', {}, h('dt', {}, 'Time'), h('dd', {}, `Today, ${c.time}`)),
        h('div', {}, h('dt', {}, 'Trainer'), h('dd', {}, c.trainer)),
        h('div', {}, h('dt', {}, 'Spots'), h('dd', {}, c.spots === 0 ? 'Full' : spotsText(c))),
        h('div', {}, h('dt', {}, 'Price'), h('dd', {}, stars(c.price)))),
      c.spots === 0
        ? h('p', { class: 'tma-footnote', style: 'margin:0;padding:0 var(--tma-s4)' }, 'This class is full. Pick another time on the Classes tab.')
        : h('p', { class: 'tma-footnote', style: 'margin:0;padding:0 var(--tma-s4)' }, 'Paid in Telegram Stars. The bot sends the receipt and a reminder an hour before.'),
      status));
  if (c.spots === 0) {
    tma.mainButton({ text: 'Class is full', active: false, onClick: () => {} });
    return;
  }
  tma.mainButton({
    text: `Book ${c.time} class · ${starsText(c.price)}`,
    onClick: async () => {
      void tma.store().set('lastClass', c.id).catch(() => {});
      await checkout({ classId: c.id }, status, `Booked: ${c.title}, today at ${c.time}.`);
    },
  });
}

/* ---------------------------------------------------------------- trainer detail */
function trainerScreen(t: Trainer): void {
  detail(
    h('header', { class: 'tma-header', style: 'display:flex;gap:var(--tma-s4);align-items:center' }, initials(t.name, 'is-56'),
      h('div', {}, h('h1', { class: 'tma-title2' }, t.name), h('p', { class: 'tma-subhead tma-hint', style: 'margin:2px 0 0' }, t.tag))),
    section('Classes today', classList(CLASSES.filter((c) => c.trainer === t.name))));
}

/* ---------------------------------------------------------------- plan detail */
function planScreen(p: Plan): void {
  const status = h('p', { class: 'tma-footnote', role: 'status', style: 'margin:0;padding:0 var(--tma-s4)' });
  detail(
    h('header', { class: 'tma-header' }, h('h1', { class: 'tma-title2' }, p.name),
      p.recommended ? h('p', { class: 'tma-subhead tma-hint', style: 'margin:var(--tma-s1) 0 0' }, 'Most chosen') : null),
    h('div', { class: 'tma-stack' },
      h('section', { class: 'tma-card tma-plan' },
        h('p', { class: 'tma-price is-lg', style: 'margin:0' }, stars(p.price, '/ month')),
        h('ul', { class: 'tma-checks' }, ...p.features.map((f) => h('li', {}, f)))),
      h('p', { class: 'tma-footnote', style: 'margin:0;padding:0 var(--tma-s4)' }, 'Paid in Telegram Stars and renewed monthly until you cancel in Telegram.'),
      status));
  tma.mainButton({
    text: `Subscribe · ${starsText(p.price, { period: '/ month' })}`,
    onClick: () => checkout({ planId: p.id }, status, `${p.name} membership is active.`),
  });
}

/* ---------------------------------------------------------------- payment: server order + invoice link (payments.md §2-3) */
const api = (path: string, init: RequestInit = {}) => fetch(path, {
  ...init, headers: { Authorization: `tma ${tma.initData}`, 'Content-Type': 'application/json', ...(init.headers || {}) },
});
async function checkout(lines: Record<string, string>, status: HTMLElement, done: string): Promise<void> {
  if (!tma.inTelegram) { status.textContent = 'Open FitHub in Telegram to pay.'; return; }
  status.textContent = '';
  let order: { order_id: string; link: string };
  try {
    const res = await api('/api/checkout', { method: 'POST', body: JSON.stringify(lines) }); // ids only: the server prices
    if (!res.ok) {
      const why = await res.json().catch(() => ({})) as { reason?: string };
      status.textContent = why.reason || 'Booking is not available right now. Try again in a minute.';
      tma.haptic.error();
      return;
    }
    order = await res.json();
  } catch {
    status.textContent = 'No connection. Nothing was charged. Try again when you are online.';
    tma.haptic.error();
    return;
  }
  await tma.writeAccess(); // so the receipt and the reminder can reach the chat (payments.md step 9)
  const hint = await tma.pay(order.link);
  if (hint === 'cancelled') return; // quietly back; the MainButton is restored by the kit
  if (hint === 'unsupported') { status.textContent = 'Update Telegram to pay in this app.'; return; }
  status.textContent = hint === 'pending'
    ? "The payment is processing. Don't pay again: the bot will message you."
    : 'Checking the payment…';
  const { state, timedOut } = await tma.watchOrder(
    async () => { const r = await api(`/api/orders/${encodeURIComponent(order.order_id)}`); if (!r.ok) throw new Error(String(r.status)); return r.json() as Promise<Order>; },
    (o) => o.status !== 'open');
  if (state && (state.status === 'paid' || state.status === 'delivered')) {
    tma.haptic.success();
    success(done);
  } else if (timedOut) {
    status.textContent = "We're still checking the payment and will message you in the chat. Questions: /paysupport.";
  } else {
    status.textContent = state?.reason || 'The payment did not go through. You were not charged.';
    tma.haptic.error();
  }
}
function success(text: string): void {
  screens[screens.length - 1] = () => success(text); // Back from here never offers to pay again
  detail(h('div', { class: 'tma-placeholder' },
    svgUse('tma-icon', 'success'),
    h('p', { class: 'tma-placeholder__title' }, text),
    h('p', { class: 'tma-placeholder__text' }, 'The receipt is in the chat with the bot.')));
  tma.mainButton({ text: 'Done', onClick: () => { while (screens.length) { screens.pop(); tma.nav.pop(); } tma.mainButton(null); renderRoot(); show('root', true); } });
}

let toastTimer = 0;
function toast(text: string): void {
  const s = $('snackbar'); s.textContent = text; s.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { s.hidden = true; }, 2400);
}

/* ---------------------------------------------------------------- start */
tma.start(); // fullscreen on iOS / Android (8.0+), the expanded sheet elsewhere
tma.chrome({ header: 'secondary_bg_color', background: 'secondary_bg_color', bottomBar: 'secondary_bg_color' });
const start = parseStartParam(tma.launch.tgWebAppStartParam, {
  tab: /^tab-(classes|trainers|membership|profile)$/, cls: /^class-(hiit|yoga|box)$/,
});
setTab(start?.route === 'tab' ? (start.match[1] as Tab) : 'classes');
if (start?.route === 'cls') { const c = CLASSES.find((x) => x.id === start.match[1]); if (c) push(() => classScreen(c)); }
tma.ready();
