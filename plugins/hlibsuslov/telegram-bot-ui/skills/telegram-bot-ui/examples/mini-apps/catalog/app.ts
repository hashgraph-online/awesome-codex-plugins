// Catalogue patterns: three content types laid out by the rules in data/mini-apps/layouts.json.
//   Books    - grid tiles, 2:3 covers contained (L02, L03), title -> author -> price (L05, L06), sold out dimmed (L08)
//   Trainers - rows with round photos; detail with a 4:5 portrait, gallery grid (L12), day strip + slot grid (L16)
//   Workouts - 16:9 media cards with a duration badge, members-only lock; detail with the video on top (L11)
// Data and images are fictional. Text goes through textContent only.
import { createTma, parseStartParam } from '../_kit/tma.ts';

type Book = { id: string; title: string; author: string; price: number; old?: number; format: string[]; rating: number; reviews: number; genre: string; soldOut?: boolean; cover: number; about: string; pages: number; year: number };
type Trainer = { id: string; name: string; specialty: string; years: number; rating: number; reviews: number; price: number; photo: number; langs: string; about: string; tags: string[] };
type Workout = { id: string; title: string; level: string; minutes: number; equipment: string; kind: string; members?: boolean; img: number; steps: string[] };

const tma = createTma();
const $ = (id: string) => document.getElementById(id) as HTMLElement;
const user = (tma.tg as unknown as { initDataUnsafe?: { user?: { language_code?: string } } } | null)?.initDataUnsafe?.user;
const money = new Intl.NumberFormat(user?.language_code || 'en', { style: 'currency', currency: 'EUR' });
const ICONS = '../_kit/icons.svg';

const BOOKS: Book[] = [
  { id: 'quiet-harbour', title: 'The Quiet Harbour', author: 'Mira Kovac', price: 12.9, format: ['Paper', 'E-book', 'Audio'], rating: 4.6, reviews: 2140, genre: 'Fiction', cover: 1, about: 'A lighthouse keeper finds letters that were never sent and follows them across three summers on the coast.', pages: 312, year: 2025 },
  { id: 'small-teams', title: 'Small Teams, Big Releases', author: 'Andrii Rudenko', price: 18.5, old: 24, format: ['Paper', 'E-book'], rating: 4.8, reviews: 860, genre: 'Business', cover: 2, about: 'How four-person product teams plan, ship and support software without burning out.', pages: 248, year: 2026 },
  { id: 'night-garden', title: 'The Night Garden Club', author: 'Lena Ortiz', price: 9.9, format: ['Paper'], rating: 4.4, reviews: 410, genre: 'Kids', cover: 3, about: 'Four friends start a garden that only blooms after dark.', pages: 96, year: 2024 },
  { id: 'cold-numbers', title: 'Cold Numbers', author: 'Tom Hale', price: 14, format: ['Paper', 'E-book'], rating: 4.2, reviews: 1290, genre: 'Fiction', soldOut: true, cover: 4, about: 'An auditor finds a pattern in a city budget and cannot stop counting.', pages: 288, year: 2023 },
  { id: 'pricing-plain', title: 'Pricing, Plainly', author: 'Sara Lind', price: 21, format: ['Paper', 'E-book', 'Audio'], rating: 4.7, reviews: 530, genre: 'Business', cover: 5, about: 'Set and change prices for a subscription product, with worked examples.', pages: 204, year: 2026 },
  { id: 'maps-moon', title: 'Maps of the Moon', author: 'Iris Novak', price: 11.5, format: ['Paper'], rating: 4.9, reviews: 95, genre: 'Kids', cover: 6, about: 'A picture book about the people who first drew the far side of the Moon.', pages: 48, year: 2025 },
];
const TRAINERS: Trainer[] = [
  { id: 'olena', name: 'Olena Marchenko', specialty: 'Strength', years: 8, rating: 4.9, reviews: 212, price: 30, photo: 1, langs: 'English, Ukrainian', about: 'Barbell basics and progressive plans for people who sit all day. First session includes a movement check.', tags: ['Strength'] },
  { id: 'marco', name: 'Marco Bellini', specialty: 'Boxing', years: 11, rating: 4.8, reviews: 340, price: 35, photo: 2, langs: 'English, Italian', about: 'Technique-first boxing: footwork, combinations, conditioning. Gloves provided.', tags: ['Boxing'] },
  { id: 'aiko', name: 'Aiko Tanaka', specialty: 'Yoga and mobility', years: 6, rating: 5.0, reviews: 98, price: 25, photo: 3, langs: 'English, Japanese', about: 'Slow flows for mobility and recovery. Good for runners and desk workers.', tags: ['Yoga'] },
  { id: 'david', name: 'David Okafor', specialty: 'Strength and conditioning', years: 4, rating: 4.7, reviews: 61, price: 28, photo: 4, langs: 'English', about: 'Circuits and kettlebells. Bring water.', tags: ['Strength'] },
];
const WORKOUTS: Workout[] = [
  { id: 'full-body-20', title: 'Full body in 20 minutes', level: 'Beginner', minutes: 20, equipment: 'No equipment', kind: 'Strength', img: 1, steps: ['Warm-up, 3 min', 'Squats and push-ups, 3 rounds', 'Plank series', 'Cool-down'] },
  { id: 'kettlebell-flow', title: 'Kettlebell flow', level: 'Intermediate', minutes: 32, equipment: 'Kettlebell', kind: 'Strength', members: true, img: 2, steps: ['Swings', 'Goblet squats', 'Clean and press', 'Carries'] },
  { id: 'hips-and-back', title: 'Hips and lower back', level: 'All levels', minutes: 15, equipment: 'Mat', kind: 'Mobility', img: 3, steps: ['Cat-cow', 'Hip flexor stretch', 'Pigeon', 'Breathing'] },
  { id: 'evening-unwind', title: 'Evening unwind', level: 'All levels', minutes: 25, equipment: 'Mat', kind: 'Mobility', members: true, img: 4, steps: ['Neck and shoulders', 'Forward folds', 'Twists', 'Rest'] },
];

/* ---------------------------------------------------------------- DOM helper: text only, never markup from data */
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
function icon(name: string, size?: number): SVGSVGElement {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'tma-icon'); svg.setAttribute('aria-hidden', 'true');
  if (size) svg.setAttribute('style', `width:${size}px;height:${size}px`);
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', `${ICONS}#i-${name}`);
  svg.append(use);
  return svg;
}
const img = (src: string, alt: string, cls = '') => h('img', { src, alt, loading: 'lazy', class: cls });
const media = (ratio: string, src: string, alt: string, extra: Kid[] = [], cls = '') =>
  h('figure', { class: `tma-media ${cls}`, style: `--tma-ratio:${ratio}` }, img(src, alt), ...extra);
const priceEl = (p: number, old?: number, from = false) =>
  h('span', { class: 'tma-price' }, from ? h('span', { class: 'tma-price__from' }, 'from') : null, money.format(p),
    old ? h('span', { class: 'tma-price__old' }, money.format(old)) : null);
const glyph = (cls: string, name: string): SVGSVGElement => {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', cls); svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', `../_kit/icons.svg#i-${name}`);
  svg.append(use);
  return svg;
};
// ratings and Stars prices draw SVG glyphs, never emoji characters (anti-slop MA13)
const stars = (r: number, n: number) => h('span', { class: 'tma-rating-inline', 'aria-label': `Rated ${r} of 5 by ${n} people` },
  glyph('tma-rating-inline__star', 'stars-gold'), `${r.toFixed(1)} (${n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n})`);
const starsPrice = (amount: string) => h('span', { class: 'tma-amount is-stars' }, glyph('tma-star', 'stars-gold'), amount,
  h('span', { class: 'tma-sr-only' }, ' Stars')); // screen readers hear "120 Stars"

/* ---------------------------------------------------------------- state and navigation */
let tab: 'books' | 'trainers' | 'workouts' = 'books';
const filter: Record<string, string> = { books: 'All', trainers: 'All', workouts: 'All' };
let query = '';
const favs = new Set<string>();
function setTab(t: typeof tab): void {
  tab = t;
  for (const b of document.querySelectorAll<HTMLButtonElement>('[data-tab]')) b.setAttribute('aria-selected', String(b.dataset.tab === t));
  renderRoot();
}
for (const b of document.querySelectorAll<HTMLButtonElement>('[data-tab]')) {
  b.onclick = () => { if (b.dataset.tab !== tab) { tma.haptic.select(); setTab(b.dataset.tab as typeof tab); } };
}
function openScreen(id: 'detail' | 'viewer', render: (el: HTMLElement) => void, onBack: () => void): void {
  const el = $(id);
  el.replaceChildren(); render(el);
  for (const s of ['root', 'detail', 'viewer']) $(s).hidden = s !== id;
  el.classList.remove('is-back');
  $('tabbar').hidden = true;
  tma.nav.push({ id, kind: 'screen', onBack });
  window.scrollTo(0, 0);
}
function back(id: 'detail' | 'viewer', to: 'root' | 'detail'): void {
  tma.nav.pop(id);
  for (const s of ['root', 'detail', 'viewer']) $(s).hidden = s !== to;
  $(to).classList.add('is-back');
  if (to === 'root') { $('tabbar').hidden = false; tma.mainButton(null); }
}

/* ---------------------------------------------------------------- roots */
function header(title: string, placeholder: string): Kid[] {
  const search = h('input', { type: 'search', placeholder: 'Search', 'aria-label': placeholder, value: query }) as HTMLInputElement;
  search.oninput = () => { query = search.value.trim().toLowerCase(); renderList(); };
  return [h('header', { class: 'tma-header' }, h('h1', { class: 'tma-large-title' }, title)),
    h('label', { class: 'tma-search' }, icon('search'), search)];
}
function chips(options: string[]): HTMLElement {
  const row = h('div', { class: 'tma-scroll-x', role: 'tablist', 'aria-label': 'Filter', style: 'margin-top:var(--tma-s3)' });
  for (const o of options) {
    row.append(h('button', { class: 'tma-chip', type: 'button', 'aria-pressed': String(filter[tab] === o),
      onclick: (() => { if (filter[tab] !== o) { filter[tab] = o; tma.haptic.select(); renderRoot(); } }) as EventListener }, o));
  }
  return row;
}
function renderRoot(): void {
  const root = $('root');
  const titles = { books: ['Books', 'Search books'], trainers: ['Trainers', 'Search trainers'], workouts: ['Workouts', 'Search workouts'] };
  const opts = { books: ['All', 'Fiction', 'Business', 'Kids'], trainers: ['All', 'Strength', 'Boxing', 'Yoga'], workouts: ['All', 'Strength', 'Mobility'] };
  root.replaceChildren(...header(titles[tab][0], titles[tab][1]), chips(opts[tab]), h('div', { id: 'list', style: 'margin-top:var(--tma-gap-section)' }));
  renderList();
}
function count(n: number, noun: string): HTMLElement {
  return h('p', { class: 'tma-footnote', style: 'margin:0 0 var(--tma-s3)', 'aria-live': 'polite' }, `${n} ${noun}${n === 1 ? '' : 's'}`);
}
function empty(): HTMLElement {
  return h('div', { class: 'tma-placeholder' }, h('p', { class: 'tma-placeholder__title' }, 'Nothing matches'),
    h('p', { class: 'tma-placeholder__text' }, 'Try another word or clear the filter.'),
    h('button', { class: 'tma-btn is-tonal', type: 'button', onclick: (() => { query = ''; filter[tab] = 'All'; renderRoot(); }) as EventListener }, 'Clear search and filter'));
}
const match = (text: string) => !query || text.toLowerCase().includes(query);

function renderList(): void {
  const list = $('list');
  if (tab === 'books') {
    const items = BOOKS.filter((b) => (filter.books === 'All' || b.genre === filter.books) && match(`${b.title} ${b.author}`));
    if (!items.length) { list.replaceChildren(empty()); return; }
    list.replaceChildren(count(items.length, 'book'), h('div', { class: 'tma-grid' }, ...items.map((b) =>
      h('a', { class: 'tma-tile', href: `#book-${b.id}`, 'aria-disabled': b.soldOut ? 'true' : false,
        onclick: ((e: Event) => { e.preventDefault(); openBook(b); }) as EventListener },
        media('2 / 3', `media/cover-${b.cover}.svg`, `Cover of ${b.title}`, b.old ? [h('span', { class: 'tma-media__tag' }, `−${Math.round((1 - b.price / b.old) * 100)} %`)] : [], 'is-contain'),
        h('span', { class: 'tma-tile__title' }, b.title),
        h('span', { class: 'tma-meta' }, b.author),
        priceEl(b.price, b.old),
        b.soldOut ? h('span', { class: 'tma-avail is-out' }, 'Sold out') : h('span', { class: 'tma-meta' }, b.format.join(' · '))))));
  } else if (tab === 'trainers') {
    const items = TRAINERS.filter((t) => (filter.trainers === 'All' || t.tags.includes(filter.trainers) || t.specialty.includes(filter.trainers)) && match(`${t.name} ${t.specialty}`));
    if (!items.length) { list.replaceChildren(empty()); return; }
    list.replaceChildren(count(items.length, 'trainer'), h('ul', { class: 'tma-list' }, ...items.map((t) => h('li', {},
      h('button', { class: 'tma-cell is-2', type: 'button', onclick: (() => openTrainer(t)) as EventListener },
        img(`media/trainer-${t.photo}.svg`, '', 'tma-row-thumb is-round'),
        h('span', { class: 'tma-cell__body' }, h('span', { class: 'tma-cell__title' }, t.name),
          h('span', { class: 'tma-cell__subtitle' }, `${t.specialty} · ${t.years} years`)),
        h('span', { class: 'tma-cell__after' }, h('strong', {}, priceEl(t.price, undefined, true)), stars(t.rating, t.reviews)))))));
  } else {
    const items = WORKOUTS.filter((w) => (filter.workouts === 'All' || w.kind === filter.workouts) && match(w.title));
    if (!items.length) { list.replaceChildren(empty()); return; }
    list.replaceChildren(count(items.length, 'workout'), h('div', { class: 'tma-stack' }, ...items.map((w) => {
      const fav = h('button', { class: 'tma-fav', type: 'button', 'aria-label': `Save ${w.title}`, 'aria-pressed': String(favs.has(w.id)),
        onclick: ((e: Event) => { e.stopPropagation(); e.preventDefault(); if (favs.has(w.id)) favs.delete(w.id); else favs.add(w.id); (e.currentTarget as HTMLElement).setAttribute('aria-pressed', String(favs.has(w.id))); tma.haptic.select(); }) as EventListener }, icon('heart'));
      return h('a', { class: 'tma-tile is-wide', href: `#workout-${w.id}`, onclick: ((e: Event) => { e.preventDefault(); openWorkout(w); }) as EventListener },
        media('16 / 9', `media/workout-${w.img}.svg`, w.title, [h('span', { class: 'tma-media__badge' }, `${w.minutes} min`),
          w.members ? h('span', { class: 'tma-media__tag' }, icon('lock', 12), ' Members') : null, fav]),
        h('span', { class: 'tma-tile__title' }, w.title),
        h('span', { class: 'tma-meta' }, `${w.level} · ${w.minutes} min · ${w.equipment}`));
    })));
  }
}

/* ---------------------------------------------------------------- book detail (L11 order) */
function openBook(b: Book): void {
  let format = b.format[0];
  const priceOf = (f: string) => (f === 'E-book' ? b.price * 0.6 : f === 'Audio' ? b.price * 0.8 : b.price);
  openScreen('detail', (el) => {
    const seg = h('div', { class: 'tma-segmented', role: 'tablist', 'aria-label': 'Format' });
    const priceLine = h('p', { style: 'margin:0' });
    const drawPrice = () => priceLine.replaceChildren(priceEl(priceOf(format), format === 'Paper' ? b.old : undefined));
    const drawSeg = () => seg.replaceChildren(...b.format.map((f) => h('button', { type: 'button', role: 'tab', 'aria-selected': String(f === format),
      onclick: (() => { if (f !== format) { format = f; tma.haptic.select(); drawSeg(); drawPrice(); updateMain(); } }) as EventListener }, f)));
    drawSeg(); drawPrice();
    const about = h('p', { class: 'tma-clamp-3', style: 'margin:0' }, b.about);
    el.append(
      h('div', { style: 'width:min(160px,42vw);margin:var(--tma-s2) auto var(--tma-s4)' }, media('2 / 3', `media/cover-${b.cover}.svg`, `Cover of ${b.title}`, [], 'is-contain')),
      h('h1', { class: 'tma-title2', style: 'text-align:center' }, b.title),
      h('p', { class: 'tma-subhead tma-hint', style: 'text-align:center;margin:var(--tma-s1) 0 0' }, b.author, ' · ', stars(b.rating, b.reviews)),
      h('div', { class: 'tma-stack', style: 'margin-top:var(--tma-gap-section)' },
        h('section', { class: 'tma-card' }, seg, priceLine,
          b.soldOut ? h('span', { class: 'tma-avail is-out' }, 'Sold out in paper. The e-book is available.') : h('span', { class: 'tma-avail' }, 'In stock · ships in 2 days')),
        h('section', { class: 'tma-card', 'aria-labelledby': 'about-h' }, h('h2', { class: 'tma-headline', id: 'about-h', style: 'margin:0' }, 'About'), about,
          h('button', { class: 'tma-btn is-plain', type: 'button', onclick: ((e: Event) => { about.classList.remove('tma-clamp-3'); (e.currentTarget as HTMLElement).remove(); }) as EventListener }, 'More')),
        h('dl', { class: 'tma-kv' }, h('div', {}, h('dt', {}, 'Pages'), h('dd', {}, String(b.pages))), h('div', {}, h('dt', {}, 'Published'), h('dd', {}, String(b.year))), h('div', {}, h('dt', {}, 'Genre'), h('dd', {}, b.genre))),
        h('section', { class: 'tma-section', 'aria-labelledby': 'sim-h' }, h('h2', { class: 'tma-section__header', id: 'sim-h' }, 'Similar books'),
          h('div', { class: 'tma-carousel', style: '--x:0' }, ...BOOKS.filter((x) => x.id !== b.id && x.genre === b.genre).concat(BOOKS.filter((x) => x.genre !== b.genre)).slice(0, 4).map((x) =>
            h('a', { class: 'tma-tile', href: `#book-${x.id}`, style: 'flex:0 0 38%', onclick: ((e: Event) => { e.preventDefault(); back('detail', 'root'); openBook(x); }) as EventListener },
              media('2 / 3', `media/cover-${x.cover}.svg`, `Cover of ${x.title}`, [], 'is-contain'), h('span', { class: 'tma-tile__title' }, x.title), priceEl(x.price)))))));
    const updateMain = () => {
      const out = b.soldOut && format === 'Paper';
      tma.mainButton({ text: out ? 'Sold out in paper' : `Add to cart · ${money.format(priceOf(format))}`, active: !out,
        onClick: () => { tma.haptic.success(); toast(`${b.title} (${format.toLowerCase()}) added`); } });
    };
    updateMain();
  }, () => back('detail', 'root'));
}

/* ---------------------------------------------------------------- trainer detail: portrait, gallery, booking (L16) */
function openTrainer(t: Trainer): void {
  const days = [...Array(7)].map((_, i) => new Date(Date.now() + i * 86400000));
  let day = Math.max(0, days.findIndex((d) => d.getDay() !== 0)); // never start on a closed day
  let slot = '';
  const taken = (d: number, s: string) => (d * 7 + s.charCodeAt(1) + s.charCodeAt(3)) % 4 === 0;
  const SLOTS = ['07:00', '08:00', '09:00', '12:00', '13:00', '17:00', '18:00', '19:00'];
  openScreen('detail', (el) => {
    const dayFmt = new Intl.DateTimeFormat(user?.language_code || 'en', { weekday: 'short' });
    const strip = h('div', { class: 'tma-days', role: 'group', 'aria-label': 'Day' });
    const grid = h('div', { class: 'tma-slots', role: 'group', 'aria-label': 'Time' });
    const summary = h('p', { class: 'tma-summary', 'aria-live': 'polite', style: 'margin:0' }, 'Choose a day and a time');
    const draw = () => {
      strip.replaceChildren(...days.map((d, i) => h('button', { type: 'button', 'aria-pressed': String(i === day), disabled: d.getDay() === 0,
        'aria-label': d.toDateString(), onclick: (() => { day = i; slot = ''; tma.haptic.select(); draw(); }) as EventListener },
        h('span', {}, dayFmt.format(d)), h('span', {}, String(d.getDate())))));
      grid.replaceChildren(...SLOTS.map((s) => h('button', { type: 'button', 'aria-pressed': String(s === slot), disabled: taken(day, s),
        'aria-label': taken(day, s) ? `${s}, taken` : s, onclick: (() => { slot = s; tma.haptic.select(); draw(); }) as EventListener }, s)));
      summary.textContent = slot ? `${dayFmt.format(days[day])} ${days[day].getDate()}, ${slot} · 60 min · ${money.format(t.price)}` : 'Choose a day and a time';
      tma.mainButton(slot
        ? { text: `Book ${dayFmt.format(days[day])} ${slot} · ${money.format(t.price)}`, onClick: async () => { await new Promise((r) => setTimeout(r, 500)); tma.haptic.success(); toast('Booked. The bot will remind you an hour before.'); } }
        : { text: 'Choose a time', active: false, onClick: () => {} });
    };
    const gallery = h('div', { class: 'tma-gallery' }, ...[1, 2, 3, 4, 2, 3].map((n, i) => h('button', { type: 'button', style: 'padding:0;border:0;background:none',
      'aria-label': `Session photo ${i + 1} of 6`, onclick: (() => openViewer(t, i, draw)) as EventListener }, img(`media/workout-${n}.svg`, ''))));
    el.append(
      media('4 / 5', `media/trainer-${t.photo}.svg`, `${t.name}, ${t.specialty.toLowerCase()} trainer`, [], ''),
      h('div', { class: 'tma-header' }, h('h1', { class: 'tma-title2' }, t.name),
        h('p', { class: 'tma-subhead tma-hint', style: 'margin:var(--tma-s1) 0 0' }, `${t.specialty} · `, stars(t.rating, t.reviews))),
      h('div', { class: 'tma-stack' },
        h('dl', { class: 'tma-kv' }, h('div', {}, h('dt', {}, 'Experience'), h('dd', {}, `${t.years} years`)), h('div', {}, h('dt', {}, 'Languages'), h('dd', {}, t.langs)), h('div', {}, h('dt', {}, 'Session'), h('dd', {}, `60 min · ${money.format(t.price)}`))),
        h('section', { class: 'tma-card' }, h('h2', { class: 'tma-headline', style: 'margin:0' }, 'About'), h('p', { class: 'tma-hint', style: 'margin:0' }, t.about)),
        h('section', { class: 'tma-section', 'aria-labelledby': 'gal-h' }, h('h2', { class: 'tma-section__header', id: 'gal-h' }, 'Sessions'), gallery),
        h('section', { class: 'tma-section', 'aria-labelledby': 'book-h' }, h('h2', { class: 'tma-section__header', id: 'book-h' }, h('strong', {}, 'Book a session')),
          h('div', { style: 'display:grid;gap:var(--tma-s3)' }, strip, grid, summary))));
    draw();
  }, () => back('detail', 'root'));
}
function openViewer(t: Trainer, start: number, restore: () => void): void {
  const photos = [1, 2, 3, 4, 2, 3];
  let i = start;
  openScreen('viewer', (el) => {
    const frame = h('div', {});
    const counter = h('p', { class: 'tma-viewer__count', 'aria-live': 'polite' });
    const draw = () => { frame.replaceChildren(media('16 / 9', `media/workout-${photos[i]}.svg`, `Session with ${t.name}, photo ${i + 1}`, [], 'is-contain')); counter.textContent = `${i + 1} / ${photos.length}`; };
    const nav = h('div', { style: 'display:flex;justify-content:center;gap:var(--tma-s3)' },
      h('button', { class: 'tma-icon-btn', type: 'button', 'aria-label': 'Previous photo', onclick: (() => { i = (i + photos.length - 1) % photos.length; draw(); }) as EventListener }, icon('chevron-left')),
      h('button', { class: 'tma-icon-btn', type: 'button', 'aria-label': 'Next photo', onclick: (() => { i = (i + 1) % photos.length; draw(); }) as EventListener }, icon('chevron-right')));
    el.append(h('div', { class: 'tma-viewer' }, frame, counter, nav));
    draw();
    tma.mainButton(null);
  }, () => { back('viewer', 'detail'); restore(); }); // the detail screen and its chosen slot are still there
}

/* ---------------------------------------------------------------- workout detail */
function openWorkout(w: Workout): void {
  openScreen('detail', (el) => {
    el.append(
      media('16 / 9', `media/workout-${w.img}.svg`, `${w.title}, video cover`, [h('button', { class: 'tma-media__play', type: 'button', 'aria-label': `Play ${w.title}, ${w.minutes} minutes` }, icon('play')), h('span', { class: 'tma-media__badge' }, `${w.minutes} min`)]),
      h('div', { class: 'tma-header' }, h('h1', { class: 'tma-title2' }, w.title)),
      h('div', { style: 'display:flex;flex-wrap:wrap;gap:var(--tma-s2)' }, ...[w.level, `${w.minutes} min`, w.equipment].map((m) => h('span', { class: 'tma-chip' }, m))),
      h('div', { class: 'tma-stack', style: 'margin-top:var(--tma-gap-section)' },
        h('section', { class: 'tma-section', 'aria-labelledby': 'prog-h' }, h('h2', { class: 'tma-section__header', id: 'prog-h' }, 'Program'),
          h('ol', { class: 'tma-steps' }, ...w.steps.map((s) => h('li', {}, h('span', {}, s)))))));
    tma.mainButton(w.members
      ? { text: 'See membership plans', onClick: () => openPlans() }
      : { text: 'Start workout', onClick: () => { tma.haptic.tap(); toast('Starting'); } });
  }, () => back('detail', 'root'));
}

/* ---------------------------------------------------------------- membership plans (L25): stacked cards, one recommended */
const PLANS = [
  { id: 'basic', name: 'Basic', who: 'Videos for training at home', month: 150, features: ['All on-demand workouts', 'Weekly plan'], missing: ['Group classes'] },
  { id: 'club', name: 'Club', who: 'For regulars', month: 250, features: ['All on-demand workouts', 'Weekly plan', '4 group classes a month'], missing: [] as string[], recommended: true },
  { id: 'coach', name: 'Coach', who: 'With a personal trainer', month: 900, features: ['Everything in Club', '2 personal sessions a month', 'Progress reviews'], missing: [] as string[] },
];
function openPlans(): void {
  let yearly = false;
  let chosen = 'club';
  const draw = (el: HTMLElement) => {
    const price = (m: number) => (yearly ? Math.round(m * 10) : m);
    const period = () => (yearly ? '/ year' : '/ month');
    const periods: Array<[string, boolean]> = [['Monthly', false], ['Yearly · 2 months free', true]];
    el.replaceChildren(
      h('header', { class: 'tma-header' }, h('h1', { class: 'tma-title2' }, 'Membership'),
        h('p', { class: 'tma-subhead tma-hint', style: 'margin:var(--tma-s1) 0 0' }, 'Cancel any time in Settings')),
      h('div', { class: 'tma-segmented', role: 'tablist', 'aria-label': 'Billing period' },
        ...periods.map(([label, y]) => h('button', { type: 'button', role: 'tab', 'aria-selected': String(yearly === y),
          onclick: (() => { if (yearly !== y) { yearly = y; tma.haptic.select(); draw(el); } }) as EventListener }, label))),
      h('div', { class: 'tma-stack', role: 'radiogroup', 'aria-label': 'Plan', style: 'margin-top:var(--tma-gap-section)' }, ...PLANS.map((p) =>
        h('div', { class: 'tma-card tma-plan', role: 'radio', tabindex: '0', 'aria-checked': String(p.id === chosen),
          onclick: (() => { if (p.id !== chosen) { chosen = p.id; tma.haptic.select(); draw(el); } }) as EventListener },
          h('div', { style: 'display:flex;justify-content:space-between;align-items:baseline;gap:var(--tma-s2)' },
            h('span', { class: 'tma-headline' }, p.name), p.recommended ? h('span', { class: 'tma-tag' }, 'Most chosen') : null),
          h('span', { class: 'tma-meta' }, p.who),
          h('span', { class: 'tma-price is-lg' }, starsPrice(price(p.month)), h('span', { class: 'tma-price__period' }, period())),
          h('ul', { class: 'tma-checks' }, ...p.features.map((f) => h('li', {}, f)),
            ...p.missing.map((f) => h('li', { class: 'is-no' }, 'No ' + f.toLowerCase())))))),
      h('p', { class: 'tma-footnote', style: 'padding:0 var(--tma-s4)' }, 'Paid in Telegram Stars and renewed automatically until you cancel.'));
    const plan = PLANS.find((p) => p.id === chosen)!;
    tma.mainButton({ text: `Subscribe · ⭐ ${price(plan.month)} ${period()}`,
      onClick: () => toast('The bot creates the subscription invoice: see payments-and-stars.md') });
  };
  if (tma.nav.top?.id === 'detail') tma.nav.pop('detail');
  openScreen('detail', draw, () => back('detail', 'root'));
}

let toastTimer = 0;
function toast(text: string): void {
  const s = $('snackbar'); s.textContent = text; s.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { s.hidden = true; }, 2400);
}

tma.chrome({ header: 'secondary_bg_color', background: 'secondary_bg_color', bottomBar: 'secondary_bg_color' });
const start = parseStartParam(tma.launch.tgWebAppStartParam, { tab: /^tab-(books|trainers|workouts)$/, trainer: /^trainer-([a-z]{2,20})$/ });
setTab(start?.route === 'tab' ? (start.match[1] as typeof tab) : start?.route === 'trainer' ? 'trainers' : 'books');
if (start?.route === 'trainer') { const t = TRAINERS.find((x) => x.id === start.match[1]); if (t) openTrainer(t); }
tma.ready();
