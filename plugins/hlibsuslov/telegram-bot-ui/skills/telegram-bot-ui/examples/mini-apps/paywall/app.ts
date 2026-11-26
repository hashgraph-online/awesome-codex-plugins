// Road Theory (fictional driving-theory trainer): a Premium paywall built to references/mini-apps/payments.md
// section 9 (P1-P12) and the surface rules S1-S6 (design-system.md section 5).
// Tabs Learn / Tests / Profile; level 2: Premium (the paywall) -> Confirming -> Premium is on.
// The server owns the offer, the prices and the order; the app never unlocks anything from invoiceClosed.
import { ApiError, createTma, idempotencyKey, parseStartParam, type Tma } from '../_kit/tma.ts';

type PlanId = 'month' | 'quarter';
type Plan = { id: PlanId; kind: 'subscription' | 'once'; stars: number; days: number; save_percent?: number };
type Tier = { tests: number; signs: number; review: boolean };
type Offer = { free: Tier; premium: Tier; plans: Plan[] };
type Status = { active: boolean; plan?: PlanId; until?: string; renews?: boolean };
type Order = { id: string; status: 'paid' | 'failed' | 'open'; plan?: PlanId; until?: string; renews?: boolean };

const tma: Tma = createTma(); // first: saves launch params before anything touches the hash
const $ = (id: string) => document.getElementById(id) as HTMLElement;
const ICONS = '../_kit/icons.svg';

/* ---------------------------------------------------------------- DOM helpers: text only, never markup from data */
type Kid = Node | string | null | false | undefined;
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
function icon(name: string, cls = 'tma-icon'): SVGSVGElement {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', cls); svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', `${ICONS}#i-${name}`);
  svg.append(use);
  return svg;
}
/** Stars amount in content: the SVG glyph (never the emoji), read as "50 Stars". */
const stars = (n: number) => h('span', { class: 'tma-amount is-stars' }, icon('stars-gold', 'tma-star'), String(n),
  h('span', { class: 'tma-sr-only' }, ' Stars'));
const date = (iso: string) => new Date(iso + 'T12:00:00').toLocaleDateString('en', { day: 'numeric', month: 'long' });
const cell = (title: string, subtitle?: string, after?: Kid, lead?: string) => h('li', {}, h('div', { class: `tma-cell${subtitle ? ' is-2' : ''}` },
  lead ? h('span', { class: 'tma-icon-tile' }, icon(lead)) : null,
  h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-cell__title' }, title), subtitle ? h('span', { class: 'tma-cell__subtitle' }, subtitle) : null),
  after ? h('span', { class: 'tma-cell__after' }, after) : null));
/** replaceChildren without the empty slots (null would be drawn as the text "null"). */
const put = (el: HTMLElement, ...kids: Kid[]) => el.replaceChildren(...kids.filter((k): k is Node | string => !!k));
const section = (title: string | null, ...kids: Kid[]) => h('section', { class: 'tma-section' },
  title ? h('h2', { class: 'tma-section__header' }, title) : null, ...kids);

/* ---------------------------------------------------------------- server */
let offer: Offer | null = null;
let status: Status = { active: false };
const loadOffer = async () => { offer = await tma.api<Offer>('/api/premium/offer'); return offer; };
const loadStatus = async () => { status = await tma.api<Status>('/api/premium/status'); return status; };
const why = (e: unknown) => (e instanceof ApiError ? (e.reason ?? ({ offline: 'No connection.', timeout: 'The server did not answer.',
  session: 'The session expired: reopen the app from the chat.', rejected: 'The server refused the request.', server: 'The server failed.' })[e.kind]) : 'Something failed.');

/* ---------------------------------------------------------------- tabs */
type Tab = 'learn' | 'tests' | 'profile';
let tab: Tab = 'learn';
const tabScroll = tma.scrollMemory();
function setTab(t: Tab): void {
  if (t !== tab) tabScroll.leave(tab);
  tab = t;
  for (const s of ['learn', 'tests', 'profile', 'premium']) $(s).hidden = s !== t;
  for (const b of document.querySelectorAll<HTMLButtonElement>('[data-tab]')) b.setAttribute('aria-selected', String(b.dataset.tab === t));
  $('tabbar').hidden = false;
  if (t === 'tests') renderTests();
  if (t === 'profile') renderProfile();
  tma.mainButton(null);
  tabScroll.enter(t);
}
for (const b of document.querySelectorAll<HTMLButtonElement>('[data-tab]')) {
  b.addEventListener('click', () => { if (b.dataset.tab !== tab) { tma.haptic.select(); setTab(b.dataset.tab as Tab); } else tabScroll.top(); });
}

/* Learn: the settings group from the review, rebuilt (one group, its footnote, the progress card apart) */
let perSession = 10;
function renderSessionSize(): void {
  $('session-size').replaceChildren(...[10, 20, 30, 50].map((n) => h('button', { type: 'button', role: 'tab', 'aria-selected': String(n === perSession),
    onclick: (() => { if (n !== perSession) { perSession = n; tma.haptic.select(); renderSessionSize(); } }) as EventListener }, String(n))));
}

/* Tests: the free test is usable here; the locked tests are visible, and one quiet card leads to Premium */
function renderTests(): void {
  const body = $('tests-body');
  const premium = status.active;
  const total = offer?.premium.tests ?? 40;
  const free = h('ul', { class: 'tma-list' },
    cell('Practice test 1', '45 questions · 30 minutes · free', icon('chevron-right', 'tma-cell__chevron'), 'trophy'));
  const locked = h('ul', { class: 'tma-list', 'aria-label': 'Premium tests' },
    ...[2, 3, 4].map((n) => cell(`Practice test ${n}`, '45 questions · 30 minutes', premium ? icon('chevron-right', 'tma-cell__chevron') : icon('lock'), 'trophy')));
  put(body, 
    section('Free', free),
    section(premium ? `All ${total} tests` : `Premium · ${total} tests`, locked,
      premium ? null : h('div', { class: 'tma-card' },
        h('p', { class: 'tma-headline', style: 'margin:0' }, `Unlock all ${total} timed tests`),
        h('p', { class: 'tma-subhead tma-hint', style: 'margin:0' }, 'Every wrong answer explained with the rule it breaks.'),
        h('button', { class: 'tma-btn is-tonal is-wide', type: 'button', onclick: (() => openPremium()) as EventListener }, 'See Premium'))),
  );
}

/* Profile: "My plan" from the server's state (payments.md section 5) */
function renderProfile(): void {
  const body = $('profile-body');
  const plan = offer?.plans.find((p) => p.id === status.plan);
  const rows: Kid[] = status.active
    ? [cell('Premium', status.renews ? `Renews on ${date(status.until ?? '')}` : `Active until ${date(status.until ?? '')}`, null, 'trophy'),
      plan ? cell('Price', plan.kind === 'subscription' ? 'every 30 days' : 'one payment, no renewal', stars(plan.stars)) : null]
    : [cell('Free plan', '1 practice test, 50 sign cards', null, 'person')];
  const actions = status.active && status.renews
    ? h('ul', { class: 'tma-list' }, h('li', {}, h('button', { class: 'tma-cell is-danger', type: 'button', onclick: (() => void turnOffRenewal()) as EventListener }, 'Turn off renewal')))
    : status.active ? null
      : h('ul', { class: 'tma-list' }, h('li', {}, h('button', { class: 'tma-cell is-button', type: 'button', onclick: (() => openPremium()) as EventListener }, 'Get Premium')));
  put(body, section('My plan', h('ul', { class: 'tma-list' }, ...rows), actions,
    status.active && status.renews ? h('p', { class: 'tma-section__footer' }, 'Premium stays on until the end of the paid period.') : null));
}
async function turnOffRenewal(): Promise<void> {
  const ok = await tma.confirm(`Turn off renewal? Premium stays on until ${date(status.until ?? '')}.`, async () => true);
  if (!ok) return;
  // The server calls editUserStarSubscription(is_canceled: true) and answers with the new state: the screen
  // draws that answer, never its own guess (a client-only "off" would let Telegram keep charging).
  try {
    status = await tma.api<Status>('/api/premium/renewal', { body: { renews: false }, idempotencyKey: idempotencyKey() });
  } catch (e) {
    tma.haptic.error();
    toast(`Renewal is still on. ${why(e)}`);
    return;
  }
  tma.haptic.success();
  renderProfile();
  toast(status.renews ? 'Renewal is still on' : 'Renewal is off');
}

/* ---------------------------------------------------------------- the paywall (level 2) */
let chosen: PlanId = 'month';
let notice: { kind: 'failed' | 'unsupported'; text: string } | null = null;
/* An order the server has not settled yet (the poll timed out, the app was closed): kept across launches so a
   return resumes it instead of creating a second order and a second charge (P9). */
const PENDING_KEY = 'premium-pending-order';
let pendingOrder: string | null = null;
const remember = (id: string | null) => { pendingOrder = id; void (id ? tma.store().set(PENDING_KEY, id) : tma.store().remove(PENDING_KEY)).catch(() => {}); };

function openPremium(): void {
  if (status.active) { setTab('profile'); return; } // P9: a subscriber never sees a paywall
  tabScroll.leave(tab);
  for (const s of ['learn', 'tests', 'profile']) $(s).hidden = true;
  $('premium').hidden = false;
  $('tabbar').hidden = true;
  notice = null;
  tma.nav.push({ id: 'premium', kind: 'screen', onBack: closePremium });
  window.scrollTo(0, 0);
  if (pendingOrder) void confirmOrder(pendingOrder); // no new checkout while one is unresolved
  else void drawPremium();
}
function closePremium(): void {
  tma.nav.pop('premium');
  tma.mainButton(null);
  $('premium').hidden = true;
  for (const s of ['learn', 'tests', 'profile']) $(s).hidden = s !== tab;
  $('tabbar').hidden = false;
}

async function drawPremium(): Promise<void> {
  const el = $('premium');
  if (!offer) {
    put(el, intro(), h('ul', { class: 'tma-list', 'aria-busy': 'true' }, ...[0, 1, 2].map(() => h('li', {}, h('div', { class: 'tma-cell is-2' },
      h('span', { class: 'tma-icon-tile tma-skeleton' }), h('span', { class: 'tma-cell__body' },
        h('span', { class: 'tma-skeleton', style: 'width:55%;height:14px' }), h('span', { class: 'tma-skeleton', style: 'width:75%;height:12px;margin-top:8px' })))))));
    tma.mainButton(null);
    try { await loadOffer(); } catch (e) {
      put(el, intro(), h('div', { class: 'tma-card' }, h('div', { class: 'tma-placeholder' },
        h('p', { class: 'tma-placeholder__title' }, 'The offer did not load'), h('p', { class: 'tma-placeholder__text' }, why(e)),
        h('button', { class: 'tma-btn is-tonal', type: 'button', onclick: (() => void drawPremium()) as EventListener }, 'Try again'))));
      tma.haptic.error();
      return;
    }
  }
  const o = offer as Offer;
  const plan = o.plans.find((p) => p.id === chosen) ?? o.plans[0];
  put(el, 
    notice ? h('div', { class: 'tma-banner', role: 'alert' }, h('div', {}, h('p', { class: 'tma-headline', style: 'margin:0' },
      notice.kind === 'failed' ? 'The payment did not go through' : 'Open the app in Telegram to pay'),
      h('p', { class: 'tma-subhead tma-hint', style: 'margin:0' }, notice.text))) : null,
    // P1-P2: what you get, in numbers from the server
    intro(),
    h('div', { class: 'tma-stack' },
      section('What you get', h('ul', { class: 'tma-list' },
        cell(`${o.premium.tests} timed tests`, '45 questions and 30 minutes, like the real exam', null, 'trophy'),
        cell('Every mistake explained', 'The rule behind each wrong answer', null, 'help'),
        cell(`All ${o.premium.signs} sign cards`, 'With spaced repetition', null, 'book'),
        cell('Same progress in the chat', 'Reminders and streaks from the bot', null, 'chat'))),
      // P3: what stays free, side by side
      section('Free and Premium', h('div', { class: 'tma-table-wrap' }, h('table', { class: 'tma-table is-compact' },
        h('thead', {}, h('tr', {}, h('th', { scope: 'col' }, ''), h('th', { scope: 'col', class: 'is-num' }, 'Free'), h('th', { scope: 'col', class: 'is-num' }, 'Premium'))),
        h('tbody', {},
          h('tr', {}, h('th', { scope: 'row' }, 'Practice tests'), h('td', { class: 'is-num' }, String(o.free.tests)), h('td', { class: 'is-num' }, String(o.premium.tests))),
          h('tr', {}, h('th', { scope: 'row' }, 'Sign cards'), h('td', { class: 'is-num' }, String(o.free.signs)), h('td', { class: 'is-num' }, String(o.premium.signs))),
          h('tr', {}, h('th', { scope: 'row' }, 'Mistake review'), h('td', { class: 'is-num' }, o.free.review ? 'Yes' : '—'), h('td', { class: 'is-num' }, o.premium.review ? 'Yes' : '—')))))),
      // P4-P5: plans as one radio group, the price with its period and how it renews; P7: the terms right under it
      section('Plan', h('ul', { class: 'tma-list', role: 'radiogroup', 'aria-label': 'Plan' }, ...o.plans.map((p) => h('li', {},
        h('label', { class: 'tma-cell is-2' },
          h('span', { class: 'tma-cell__body' },
            h('span', { class: 'tma-cell__title' }, p.kind === 'subscription' ? 'Monthly' : `${Math.round(p.days / 30)} months`),
            h('span', { class: 'tma-cell__subtitle' }, p.kind === 'subscription' ? 'Renews every 30 days'
              : `No renewal${p.save_percent ? ` · ${p.save_percent}% less than monthly` : ''}`)),
          h('span', { class: 'tma-cell__after' }, stars(p.stars), p.kind === 'subscription' ? ' / month' : ''),
          h('input', { class: 'tma-check', type: 'radio', name: 'plan', value: p.id, checked: p.id === plan.id,
            onchange: (() => { chosen = p.id; tma.haptic.select(); void drawPremium(); }) as EventListener }))))),
        h('p', { class: 'tma-section__footer' },
          'Paid with Telegram Stars. The monthly plan renews every 30 days until you turn it off in Profile or in Telegram settings. By paying you accept the ',
          h('a', { href: 'https://telegram.org/tos/stars', onclick: ((e: Event) => { e.preventDefault(); if (tma.has('6.1')) (tma.tg as { openLink?: (u: string) => void } | null)?.openLink?.('https://telegram.org/tos/stars'); }) as EventListener }, 'Terms'), '.')),
      // P7: the questions people ask before paying
      section('Questions', h('div', { class: 'tma-accordion' },
        h('details', {}, h('summary', {}, 'How do I cancel?'), h('p', {}, 'Profile → My plan → Turn off renewal, or in Telegram settings. Premium stays on until the end of the paid period.')),
        h('details', {}, h('summary', {}, 'What happens to my progress?'), h('p', {}, 'Nothing is lost. Without Premium you keep your history and the free test.')),
        h('details', {}, h('summary', {}, 'Can I pay for three months at once?'), h('p', {}, 'Yes: one payment for 90 days that does not renew. Telegram Stars subscriptions renew every 30 days.'))))),
  );
  // P6: the MainButton names the verb, the exact price and the period of the selected plan
  const months = Math.round(plan.days / 30);
  tma.mainButton(plan.kind === 'subscription'
    ? { text: `Subscribe · ⭐ ${plan.stars} / month`, onClick: () => buy(plan) }
    : { text: `Pay ⭐ ${plan.stars} for ${months} months`, onClick: () => buy(plan) });
}

function intro(): HTMLElement {
  return h('header', { class: 'tma-intro' },
    h('span', { class: 'tma-intro__mark' }, icon('trophy')),
    h('h1', { class: 'tma-title1' }, 'Road Theory Premium'),
    h('p', { class: 'tma-subhead' }, 'Practise every part of the theory test until it feels routine.'));
}

/* P9-P10: one tap creates one order on the server; the invoice status is a hint; the server's order decides */
async function buy(plan: Plan): Promise<void> {
  let order: { order_id: string; link: string };
  try {
    order = await tma.api('/api/premium/invoice', { body: { plan: plan.id }, idempotencyKey: idempotencyKey() });
  } catch (e) {
    notice = { kind: 'failed', text: `${why(e)} No Stars were taken.` };
    tma.haptic.error();
    return drawPremium();
  }
  const result = await tma.pay(order.link);
  if (result === 'paid' || result === 'pending') remember(order.order_id); // settled only by the server
  if (result === 'cancelled') return; // quiet: the user changed their mind; the screen stays as it was
  if (result === 'unsupported') { notice = { kind: 'unsupported', text: 'Payments open in Telegram only.' }; return drawPremium(); }
  if (result === 'failed') { notice = { kind: 'failed', text: 'Telegram did not complete the payment. No Stars were taken.' }; tma.haptic.error(); return drawPremium(); }
  await confirmOrder(order.order_id); // paid or pending: ask the server
}

async function confirmOrder(orderId: string): Promise<void> {
  tma.mainButton(null);
  put($('premium'), h('div', { class: 'tma-card', role: 'status' }, h('div', { class: 'tma-placeholder' },
    h('span', { class: 'tma-spinner', 'aria-hidden': 'true' }),
    h('p', { class: 'tma-placeholder__title' }, 'Confirming the payment'),
    h('p', { class: 'tma-placeholder__text' }, 'This takes a few seconds. Do not pay again.'))));
  const { state, timedOut } = await tma.watchOrder(() => tma.api<Order>(`/api/premium/orders/${encodeURIComponent(orderId)}`),
    (o) => o.status === 'paid' || o.status === 'failed', { timeoutMs: 60000 });
  if (state?.status === 'paid') {
    remember(null);
    status = { active: true, plan: state.plan, until: state.until, renews: state.renews };
    tma.haptic.success();
    return success();
  }
  if (state?.status === 'failed') {
    remember(null);
    notice = { kind: 'failed', text: 'The payment was declined. No Stars were taken.' };
    tma.haptic.error();
    return drawPremium();
  }
  if (timedOut) {
    put($('premium'), h('div', { class: 'tma-card' }, h('div', { class: 'tma-placeholder' },
      h('p', { class: 'tma-placeholder__title' }, 'Still confirming'),
      h('p', { class: 'tma-placeholder__text' }, 'We will message you in the chat as soon as Telegram confirms the payment. Do not pay again.'))));
    tma.mainButton({ text: 'Back to tests', onClick: () => { tma.nav.reset(); setTab('tests'); } });
  }
}

function success(): void {
  const o = offer as Offer;
  put($('premium'), 
    h('header', { class: 'tma-intro' }, h('span', { class: 'tma-intro__mark' }, icon('success')),
      h('h1', { class: 'tma-title1' }, 'Premium is on'),
      h('p', { class: 'tma-subhead' }, status.renews ? `Renews on ${date(status.until ?? '')}. Turn it off any time in Profile.` : `Active until ${date(status.until ?? '')}.`)),
    section('Unlocked', h('ul', { class: 'tma-list' },
      cell(`${o.premium.tests} timed tests`, undefined, null, 'trophy'),
      cell('Mistake review', undefined, null, 'help'),
      cell(`${o.premium.signs} sign cards`, undefined, null, 'book'))));
  tma.mainButton({ text: 'Start a test', onClick: () => { tma.nav.reset(); setTab('tests'); } });
}

/* ---------------------------------------------------------------- snackbar */
let toastTimer = 0;
function toast(text: string): void {
  const s = $('snackbar'); s.textContent = text; s.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { s.hidden = true; }, 2200);
}

/* ---------------------------------------------------------------- start */
tma.start(); // fullscreen on iOS / Android (8.0+), the expanded sheet elsewhere
tma.chrome({ header: 'secondary_bg_color', background: 'secondary_bg_color', bottomBar: 'secondary_bg_color' });
renderSessionSize();
const route = parseStartParam(tma.launch.tgWebAppStartParam, { premium: /^premium$/, tests: /^tab-tests$/ });
setTab(route?.route === 'tests' ? 'tests' : 'learn');
tma.ready();
void Promise.allSettled([loadStatus(), loadOffer(), tma.store().get(PENDING_KEY).then((v) => { pendingOrder = v; })]).then(() => {
  if (tab === 'tests') renderTests();
  if (tab === 'profile') renderProfile();
  if (route?.route === 'premium') { setTab('tests'); openPremium(); } // deep link: the paywall on top of its tab root
});
