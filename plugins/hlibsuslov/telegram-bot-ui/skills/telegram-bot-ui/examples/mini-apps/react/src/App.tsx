// The coffee pickup scenario of examples/mini-apps/vanilla in React: Menu and Order tabs, a drink screen with
// Telegram's BackButton and MainButton, and an order screen whose MainButton places the order.
// Native buttons are driven from effects that clean up their listeners when the screen changes.
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { backButton, mainButton } from '@tma.js/sdk-react';
import { Cell, List, Placeholder, Section, Segmented } from './kit';
import ICONS from '../../_kit/icons.svg?url';

type Drink = { id: string; name: string; desc: string; prices: Record<'S' | 'M' | 'L', number> };
type Line = { drink: Drink; size: 'S' | 'M' | 'L'; qty: number };
type Haptic = { selectionChanged: { (): void; isAvailable(): boolean }; notificationOccurred: { (t: 'success' | 'error' | 'warning'): void; isAvailable(): boolean } };

const DRINKS: Drink[] = [
  { id: 'flat-white', name: 'Flat white', desc: 'Double ristretto, silky milk', prices: { S: 3.6, M: 4.2, L: 4.8 } },
  { id: 'cappuccino', name: 'Cappuccino', desc: 'Espresso, steamed milk, foam', prices: { S: 3.4, M: 3.9, L: 4.5 } },
  { id: 'cold-brew', name: 'Cold brew', desc: 'Steeped 16 hours, served over ice', prices: { S: 3.8, M: 4.4, L: 5.0 } },
];
const money = new Intl.NumberFormat('en', { style: 'currency', currency: 'EUR' });

/** One MainButton configuration per screen; null hides it. Listeners are removed on change. */
function useMainButton(spec: { text: string; enabled?: boolean; onClick: () => void } | null) {
  useEffect(() => {
    if (!mainButton.setParams.isAvailable()) return;
    if (!spec) { mainButton.setParams({ isVisible: false }); return; }
    mainButton.setParams({ text: spec.text, isVisible: true, isEnabled: spec.enabled !== false });
    const off = mainButton.onClick(spec.onClick);
    return () => off();
  }, [spec?.text, spec?.enabled, spec?.onClick]); // eslint-disable-line react-hooks/exhaustive-deps
}

/** BackButton visible while `onBack` is set. */
function useBackButton(onBack: (() => void) | null) {
  useEffect(() => {
    if (!backButton.show.isAvailable()) return;
    if (!onBack) { backButton.hide(); return; }
    backButton.show();
    const off = backButton.onClick(onBack);
    return () => off();
  }, [onBack]);
}

export function App({ haptic }: { haptic: Haptic }) {
  const [tab, setTab] = useState<'menu' | 'order'>('menu');
  const [drink, setDrink] = useState<Drink | null>(null);
  const [size, setSize] = useState<'S' | 'M' | 'L'>('M');
  const [cart, setCart] = useState<Line[]>([]);
  const [placed, setPlaced] = useState<number | null>(null);
  const [placing, setPlacing] = useState(false);
  const select = () => haptic.selectionChanged.isAvailable() && haptic.selectionChanged();
  const total = useMemo(() => cart.reduce((s, l) => s + l.drink.prices[l.size] * l.qty, 0), [cart]);

  // Each tab, and the list under the drink screen, comes back where the user left it; a new screen starts at the top.
  const view = drink ? 'drink' : tab;
  const scrolls = useRef<Record<string, number>>({});
  const remember = () => { scrolls.current[view] = window.scrollY; };
  useLayoutEffect(() => { window.scrollTo(0, view === 'drink' ? 0 : scrolls.current[view] ?? 0); }, [view]);

  const back = useMemo(() => (drink ? () => setDrink(null) : null), [drink]);
  useBackButton(back);

  const add = useMemo(() => () => {
    if (!drink) return;
    setCart((c) => [...c, { drink, size, qty: 1 }]);
    setPlaced(null); // a new order starts once something is added after the last one
    if (haptic.notificationOccurred.isAvailable()) haptic.notificationOccurred('success');
    setDrink(null);
  }, [drink, size, haptic]);
  const place = useMemo(() => async () => {
    if (placing) return; // one order per tap: ignore taps while the request runs
    setPlacing(true);
    if (mainButton.showLoader.isAvailable()) mainButton.showLoader();
    try {
      await new Promise((r) => setTimeout(r, 500)); // your API, with Authorization: tma <initData>
      setPlaced(1042); setCart([]);
      if (haptic.notificationOccurred.isAvailable()) haptic.notificationOccurred('success');
    } finally {
      if (mainButton.hideLoader.isAvailable()) mainButton.hideLoader();
      setPlacing(false);
    }
  }, [haptic, placing]);

  useMainButton(
    drink ? { text: `Add to order · ${money.format(drink.prices[size])}`, onClick: add }
      : tab === 'order' && cart.length ? { text: `Place order · ${money.format(total)}`, enabled: !placing, onClick: place }
        : null,
  );

  if (drink) {
    return (
      <main className="tma-page tma-screen">
        <header className="tma-header"><h1 className="tma-title2">{drink.name}</h1><p className="tma-subhead tma-hint">{drink.desc}</p></header>
        <Section title="Size">
          <Segmented label="Size" value={size} onChange={(v) => { setSize(v); select(); }}
            options={(['S', 'M', 'L'] as const).map((s) => [s, `${s} · ${money.format(drink.prices[s])}`])} />
        </Section>
      </main>
    );
  }

  return (
    <>
      <main className="tma-page">
        <header className="tma-header"><h1 className="tma-large-title">{tab === 'menu' ? 'Menu' : 'Order'}</h1></header>
        {tab === 'menu' && (
          <Section title="Drinks">
            <List>{DRINKS.map((d) => (
              <Cell key={d.id} title={d.name} subtitle={d.desc} after={money.format(d.prices.S)} chevron onClick={() => { remember(); setSize('M'); setDrink(d); }} />
            ))}</List>
          </Section>
        )}
        {tab === 'order' && (placed ? (
          <div className="tma-card"><p className="tma-title3">Order {placed} is being prepared</p><p className="tma-hint">The bot will message you when it is ready.</p></div>
        ) : cart.length ? (
          <Section title={`${cart.length} ${cart.length === 1 ? 'drink' : 'drinks'}`} aside={<span className="tma-num">{money.format(total)}</span>}>
            <List>{cart.map((l, i) => <Cell key={i} title={l.drink.name} subtitle={`${l.size} · ${money.format(l.drink.prices[l.size])}`} />)}</List>
          </Section>
        ) : (
          <Placeholder title="Nothing here yet" text="Drinks you add from the menu appear here."
            action={<button type="button" className="tma-btn is-tonal" onClick={() => { remember(); setTab('menu'); }}>Open the menu</button>} />
        ))}
      </main>
      <nav className="tma-tabbar tma-glass" role="tablist" aria-label="Sections">
        {(['menu', 'order'] as const).map((t) => (
          <button key={t} type="button" role="tab" aria-selected={tab === t}
            onClick={() => { if (t !== tab) { remember(); setTab(t); select(); } else window.scrollTo(0, 0); }}>
            <svg className="tma-icon" aria-hidden="true"><use href={`${ICONS}#${t === 'menu' ? 'i-cup' : 'i-bag'}`} /></svg>
            <span>{t === 'menu' ? 'Menu' : `Order${cart.length ? ` · ${cart.length}` : ''}`}</span>
          </button>
        ))}
      </nav>
    </>
  );
}
