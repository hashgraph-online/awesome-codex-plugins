// Coffee pickup Mini App (fictional product): two tabs, list -> detail with BackButton and MainButton,
// pickup form with MainButton, skeleton / empty / error states, both themes. No framework, no packages.
// Recipe 91 (minimal Mini App) and 93 (shop). Build: node build.mjs (strips types into dist/).
import { createTma, parseStartParam, type Tma } from '../_kit/tma.ts';

type Drink = { id: string; name: string; desc: string; category: string; prices: Record<string, number> };
type Line = { key: string; drink: Drink; size: string; milk: string; qty: number };

const tma: Tma = createTma(); // first: saves launch params before anything touches the hash
const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
const user = (tma.tg as unknown as { initDataUnsafe?: { user?: { language_code?: string } } } | null)?.initDataUnsafe?.user;
const money = new Intl.NumberFormat(user?.language_code || 'en', { style: 'currency', currency: 'EUR' });
const SIZES = ['S', 'M', 'L'];
const MILKS = ['Whole', 'Oat', 'No milk'];

/* ---------------------------------------------------------------- data
   Synthetic catalogue. A real app calls its server with `Authorization: tma <initData>` and the server
   verifies initData first (references/mini-apps/security.md, examples/mini-apps/server/). */
const DRINKS: Drink[] = [
  { id: 'flat-white', name: 'Flat white', desc: 'Double ristretto, silky milk', category: 'Espresso', prices: { S: 3.6, M: 4.2, L: 4.8 } },
  { id: 'cappuccino', name: 'Cappuccino', desc: 'Espresso, steamed milk, foam', category: 'Espresso', prices: { S: 3.4, M: 3.9, L: 4.5 } },
  { id: 'cortado', name: 'Cortado', desc: 'Espresso cut with warm milk', category: 'Espresso', prices: { S: 3.2, M: 3.6, L: 4.0 } },
  { id: 'batch', name: 'Batch brew', desc: 'Washed Ethiopia, changes weekly', category: 'Filter', prices: { S: 2.8, M: 3.2, L: 3.6 } },
  { id: 'v60', name: 'Pour-over', desc: 'Brewed to order, about 4 minutes', category: 'Filter', prices: { S: 4.0, M: 4.6, L: 5.2 } },
  { id: 'cold-brew', name: 'Cold brew', desc: 'Steeped 16 hours, served over ice', category: 'Cold', prices: { S: 3.8, M: 4.4, L: 5.0 } },
];
const fail = new URLSearchParams(location.search).has('fail');
function fetchMenu(): Promise<Drink[]> {
  return new Promise((res, rej) => setTimeout(() => (fail ? rej(new Error('offline')) : res(DRINKS)), 450));
}
function placeOrder(lines: Line[], name: string, slot: string): Promise<{ id: number; slot: string }> {
  return new Promise((res) => setTimeout(() => res({ id: 1042, slot }), 700));
}

/* ---------------------------------------------------------------- state */
const cart: Line[] = [];
let drinks: Drink[] = [];
let category = 'All';
let current: { drink: Drink; size: string; milk: string; qty: number } | null = null;
let placed: { id: number; slot: string } | null = null;
let tab: 'menu' | 'order' = 'menu';
const total = () => cart.reduce((s, l) => s + l.drink.prices[l.size] * l.qty, 0);
const count = () => cart.reduce((s, l) => s + l.qty, 0);

/* ---------------------------------------------------------------- tiny DOM helper */
function h(tag: string, attrs: Record<string, string | boolean | ((e: Event) => void)> = {}, ...kids: (Node | string)[]): HTMLElement {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (typeof v === 'function') el.addEventListener(k.slice(2), v as EventListener);
    else if (v === true) el.setAttribute(k, '');
    else if (v !== false) el.setAttribute(k, v);
  }
  el.append(...kids);
  return el;
}
const icon = (id: string, cls = 'tma-icon') => {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', cls);
  svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', `#${id}`);
  svg.append(use);
  return svg;
};

/* ---------------------------------------------------------------- screens */
const screens = ['menu', 'drink', 'order', 'checkout'];
function show(id: string, back = false): void {
  for (const s of screens) $(s).hidden = s !== id;
  $(id).classList.toggle('is-back', back);
  $('tabbar').hidden = id === 'drink' || id === 'checkout';
  window.scrollTo(0, 0);
}

function renderMenu(): void {
  const cats = ['All', ...new Set(drinks.map((d) => d.category))];
  $('categories').replaceChildren(...cats.map((c) => h('button', {
    class: 'tma-chip', type: 'button', role: 'tab', 'aria-pressed': String(c === category),
    onclick: () => { if (c !== category) { category = c; tma.haptic.select(); renderMenu(); } },
  }, c)));
  const list = drinks.filter((d) => category === 'All' || d.category === category);
  $('menu-count').textContent = category === 'All' ? 'Drinks' : category;
  $('menu-list').removeAttribute('aria-busy');
  $('menu-list').replaceChildren(...list.map((d) => h('li', {}, h('button', {
    class: 'tma-cell is-2', type: 'button', onclick: () => openDrink(d),
  }, h('span', { class: 'tma-icon-tile' }, icon('i-cup')),
    h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-cell__title' }, d.name),
      h('span', { class: 'tma-cell__subtitle' }, d.desc)),
    h('span', { class: 'tma-cell__after', 'aria-label': `from ${money.format(d.prices.S)}` }, money.format(d.prices.S)),
    icon('i-chevron', 'tma-cell__chevron')))));
}

function renderSkeleton(): void {
  $('menu-list').replaceChildren(...[0, 1, 2, 3].map(() => h('li', {}, h('div', { class: 'tma-cell is-2' },
    h('span', { class: 'tma-icon-tile tma-skeleton' }),
    h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-skeleton', style: 'width:45%;height:14px' }),
      h('span', { class: 'tma-skeleton', style: 'width:70%;height:12px;margin-top:8px' }))))));
}

function renderMenuError(): void {
  $('menu-list').replaceChildren(h('li', {}, h('div', { class: 'tma-placeholder' },
    h('p', { class: 'tma-placeholder__title' }, 'The menu did not load'),
    h('p', { class: 'tma-placeholder__text' }, 'Telegram is online but our server did not answer. Try again in a moment.'),
    h('button', { class: 'tma-btn is-tonal', type: 'button', onclick: () => void loadMenu() }, 'Try again'))));
}

async function loadMenu(): Promise<void> {
  renderSkeleton();
  try {
    drinks = await fetchMenu();
    renderMenu();
  } catch {
    renderMenuError();
    tma.haptic.error();
  }
}

function openDrink(d: Drink): void {
  current = { drink: d, size: 'M', milk: d.category === 'Filter' ? 'No milk' : 'Whole', qty: 1 };
  renderDrink();
  show('drink');
  tma.nav.push({ id: 'drink', kind: 'screen', onBack: closeDrink });
  updateMainButton();
}
function closeDrink(): void {
  tma.nav.pop('drink');
  current = null;
  show('menu', true);
  updateMainButton();
}
function renderDrink(): void {
  if (!current) return;
  const c = current;
  $('drink-name').textContent = c.drink.name;
  $('drink-desc').textContent = c.drink.desc;
  $('sizes').replaceChildren(...SIZES.map((s) => h('button', {
    type: 'button', role: 'tab', 'aria-selected': String(s === c.size),
    onclick: () => { if (s !== c.size) { c.size = s; tma.haptic.select(); renderDrink(); updateMainButton(); } },
  }, `${s} · ${money.format(c.drink.prices[s])}`)));
  $('milks').replaceChildren(...MILKS.map((m) => h('li', {}, h('label', { class: 'tma-cell' },
    h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-cell__title' }, m)),
    h('input', { class: 'tma-check', type: 'radio', name: 'milk', value: m, checked: m === c.milk,
      onchange: () => { c.milk = m; tma.haptic.select(); } })))));
  $('qty').textContent = String(c.qty);
}

function renderOrder(): void {
  const body = $('order-body');
  if (placed) {
    body.replaceChildren(h('div', { class: 'tma-card' },
      h('p', { class: 'tma-title3' }, `Order ${placed.id} is being prepared`),
      h('p', { class: 'tma-hint', style: 'margin:0' }, `Pick it up at ${placed.slot}. The bot will message you when it is ready.`),
      h('button', { class: 'tma-btn is-tonal', type: 'button', onclick: () => { placed = null; go('menu'); } }, 'Order something else')));
    return;
  }
  if (!cart.length) {
    body.replaceChildren(h('div', { class: 'tma-placeholder' },
      h('span', { class: 'tma-icon-tile', style: 'width:56px;height:56px' }, icon('i-bag')),
      h('p', { class: 'tma-placeholder__title' }, 'Nothing here yet'),
      h('p', { class: 'tma-placeholder__text' }, 'Drinks you add from the menu appear here.'),
      h('button', { class: 'tma-btn is-tonal', type: 'button', onclick: () => go('menu') }, 'Open the menu')));
    return;
  }
  body.replaceChildren(
    h('section', { class: 'tma-section', 'aria-labelledby': 'cart-h' },
      h('h2', { class: 'tma-section__header', id: 'cart-h' }, h('span', {}, `${count()} ${count() === 1 ? 'drink' : 'drinks'}`),
        h('span', { class: 'tma-num' }, money.format(total()))),
      h('ul', { class: 'tma-list' }, ...cart.map((l) => h('li', {}, h('div', { class: 'tma-cell is-2' },
        h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-cell__title' }, l.drink.name),
          h('span', { class: 'tma-cell__subtitle' }, `${l.size} · ${l.milk} · ${money.format(l.drink.prices[l.size])}`)),
        h('span', { class: 'tma-stepper', role: 'group', 'aria-label': `${l.drink.name} quantity` },
          h('button', { type: 'button', 'aria-label': l.qty === 1 ? 'Remove' : 'Fewer', onclick: () => changeQty(l, -1) }, '−'),
          h('output', {}, String(l.qty)),
          h('button', { type: 'button', 'aria-label': 'More', onclick: () => changeQty(l, 1) }, '+'))))))),
    h('button', { class: 'tma-btn is-filled is-lg is-wide', type: 'button', onclick: openCheckout }, 'Continue to pickup'),
  );
}
function changeQty(l: Line, d: number): void {
  l.qty += d;
  if (l.qty <= 0) cart.splice(cart.indexOf(l), 1);
  tma.haptic.select();
  renderOrder();
  renderTabCount();
}
function renderTabCount(): void {
  const n = count();
  const btn = document.querySelector('[data-go="order"] > span') as HTMLElement;
  btn.firstChild!.textContent = n ? `Order · ${n} ` : 'Order ';
  $('tab-count-sr').textContent = n ? `${n} items` : '';
}

/* ---------------------------------------------------------------- checkout form */
let dirty = false;
let slot = '';
function openCheckout(): void {
  const now = new Date();
  const slots = [10, 20, 30].map((m) => new Date(now.getTime() + m * 60000).toTimeString().slice(0, 5));
  slot = slot || slots[0];
  $('slots').replaceChildren(...slots.map((s, i) => h('li', {}, h('label', { class: 'tma-cell' },
    h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-cell__title tma-num' }, s),
      h('span', { class: 'tma-cell__subtitle' }, i === 0 ? 'Earliest' : `In ${[10, 20, 30][i]} minutes`)),
    h('input', { class: 'tma-check', type: 'radio', name: 'slot', value: s, checked: s === slot,
      onchange: () => { slot = s; tma.haptic.select(); } })))));
  show('checkout');
  tma.nav.push({ id: 'checkout', kind: 'screen', onBack: closeCheckout });
  updateMainButton();
}
async function closeCheckout(): Promise<void> {
  if (dirty && !(await tma.confirm('Leave pickup details? What you typed is kept.', async () => true))) return;
  tma.nav.pop('checkout');
  show('order', true);
  updateMainButton();
}
const nameInput = () => $<HTMLInputElement>('f-name');
nameInput().addEventListener('input', () => {
  dirty = true;
  tma.closingConfirmation(true);
  $('f-name-err').hidden = true;
  nameInput().removeAttribute('aria-invalid');
  updateMainButton();
});
$('f-note').addEventListener('input', () => { dirty = true; tma.closingConfirmation(true); });

async function submitOrder(): Promise<void> {
  const name = nameInput().value.trim();
  if (!name) {
    $('f-name-err').hidden = false;
    nameInput().setAttribute('aria-invalid', 'true');
    nameInput().focus();
    tma.haptic.error();
    return;
  }
  placed = await placeOrder(cart, name, slot);
  cart.length = 0;
  dirty = false;
  tma.closingConfirmation(false);
  tma.haptic.success();
  tma.nav.reset();
  renderTabCount();
  go('order');
}

/* ---------------------------------------------------------------- native buttons per screen */
function updateMainButton(): void {
  if (current) {
    const c = current;
    tma.mainButton({
      text: `Add to order · ${money.format(c.drink.prices[c.size] * c.qty)}`,
      onClick: () => {
        const key = `${c.drink.id}:${c.size}:${c.milk}`;
        const same = cart.find((l) => l.key === key);
        if (same) same.qty += c.qty; else cart.push({ key, drink: c.drink, size: c.size, milk: c.milk, qty: c.qty });
        tma.haptic.success();
        renderTabCount();
        toast(`${c.drink.name} added`);
        closeDrink();
      },
    });
  } else if (!$('checkout').hidden) {
    tma.mainButton({ text: `Place order · ${money.format(total())}`, onClick: submitOrder, active: nameInput().value.trim().length > 0 });
  } else {
    tma.mainButton(null); // tab roots: no MainButton, the tab bar stays
  }
}

function toast(text: string): void {
  const s = $('snackbar');
  s.textContent = text;
  s.hidden = false;
  clearTimeout((toast as unknown as { t?: number }).t);
  (toast as unknown as { t?: number }).t = window.setTimeout(() => { s.hidden = true; }, 2200);
}

function go(t: 'menu' | 'order'): void {
  tab = t;
  for (const b of document.querySelectorAll<HTMLButtonElement>('[data-go]')) b.setAttribute('aria-selected', String(b.dataset.go === t));
  if (t === 'order') renderOrder();
  show(t);
  updateMainButton();
}
for (const b of document.querySelectorAll<HTMLButtonElement>('[data-go]')) {
  b.addEventListener('click', () => { if (b.dataset.go !== tab) { tma.haptic.select(); go(b.dataset.go as 'menu' | 'order'); } });
}
$('qty-dec').addEventListener('click', () => { if (current && current.qty > 1) { current.qty--; tma.haptic.select(); renderDrink(); updateMainButton(); } });
$('qty-inc').addEventListener('click', () => { if (current && current.qty < 9) { current.qty++; tma.haptic.select(); renderDrink(); updateMainButton(); } });

/* ---------------------------------------------------------------- start: chrome, first screen, ready() */
tma.chrome({ header: 'secondary_bg_color', background: 'secondary_bg_color', bottomBar: 'secondary_bg_color' });
renderTabCount();
const start = parseStartParam(tma.launch.tgWebAppStartParam, { order: /^tab-order$/, drink: /^drink-([a-z0-9-]{1,32})$/ });
void loadMenu().then(() => {
  if (start?.route === 'drink') {
    const d = drinks.find((x) => x.id === start.match[1]);
    if (d) openDrink(d);
  }
});
if (start?.route === 'order') go('order'); else go('menu');
tma.ready(); // the first screen (with skeletons) is drawn: hide Telegram's loading screen
