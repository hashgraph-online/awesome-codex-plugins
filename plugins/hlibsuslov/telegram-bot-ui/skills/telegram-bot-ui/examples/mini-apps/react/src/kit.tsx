// Thin React components over the kit's CSS (../_kit/tma.css). No logic, no colours: the classes carry the
// design system, so the same markup works in every style preset and theme.
import type { ReactNode } from 'react';

export function Section({ title, aside, footer, children }: { title?: string; aside?: ReactNode; footer?: string; children: ReactNode }) {
  return (
    <section className="tma-section">
      {title && <h2 className="tma-section__header"><span>{title}</span>{aside}</h2>}
      {children}
      {footer && <p className="tma-section__footer">{footer}</p>}
    </section>
  );
}

export function List({ children }: { children: ReactNode }) {
  return <ul className="tma-list">{children}</ul>;
}

export function Cell({ title, subtitle, after, before, onClick, chevron }: {
  title: string; subtitle?: string; after?: ReactNode; before?: ReactNode; onClick?: () => void; chevron?: boolean;
}) {
  const body = (
    <>
      {before}
      <span className="tma-cell__body">
        <span className="tma-cell__title">{title}</span>
        {subtitle && <span className="tma-cell__subtitle">{subtitle}</span>}
      </span>
      {after !== undefined && <span className="tma-cell__after">{after}</span>}
      {chevron && <svg className="tma-cell__chevron" aria-hidden="true" viewBox="0 0 8 13"><path d="m1.5 1.5 5 5-5 5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>}
    </>
  );
  return (
    <li>
      {onClick
        ? <button type="button" className={`tma-cell${subtitle ? ' is-2' : ''}`} onClick={onClick}>{body}</button>
        : <div className={`tma-cell${subtitle ? ' is-2' : ''}`}>{body}</div>}
    </li>
  );
}

export function Segmented<T extends string>({ value, options, label, onChange }: {
  value: T; options: Array<[T, string]>; label: string; onChange: (v: T) => void;
}) {
  return (
    <div className="tma-segmented" role="tablist" aria-label={label}>
      {options.map(([v, text]) => (
        <button key={v} type="button" role="tab" aria-selected={v === value} onClick={() => v !== value && onChange(v)}>{text}</button>
      ))}
    </div>
  );
}

export function Placeholder({ title, text, action }: { title: string; text: string; action?: ReactNode }) {
  return (
    <div className="tma-placeholder">
      <p className="tma-placeholder__title">{title}</p>
      <p className="tma-placeholder__text">{text}</p>
      {action}
    </div>
  );
}
