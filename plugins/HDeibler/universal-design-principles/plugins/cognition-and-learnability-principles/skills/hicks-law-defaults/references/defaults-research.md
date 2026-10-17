# Defaults: research and ethical guidance

A reference complementing `hicks-law-defaults` with research on default acceptance rates and the ethics of choice architecture.

## Research grounding

- **Thaler, R. & Sunstein, C.** (2008). *Nudge: Improving Decisions About Health, Wealth, and Happiness*. The foundational text on choice architecture; coined "libertarian paternalism" — defaults that nudge users toward better choices while preserving the option to choose otherwise.
- **Johnson, E. J. & Goldstein, D.** (2003). "Do defaults save lives?" *Science*. Showed organ-donation rates differ dramatically (~85% vs. ~15%) between countries with opt-in vs. opt-out defaults — same humans, same forms, different framing.
- **Madrian, B. C. & Shea, D. F.** (2001). On 401(k) enrollment: changing from opt-in to opt-out raised participation from ~37% to ~86%. Defaults are powerful.
- **Park, C. W. et al.** (2000). On consumer product defaults: pre-selected accessories or upgrades increase acceptance dramatically over equivalent opt-in offers.

The pattern: defaults shape behavior more than persuasion does. A well-chosen default is among the highest-leverage design decisions available.

## Acceptance rates

Empirical observations across many products:

- **Sensible defaults**: 60–85% acceptance.
- **Well-defaulted (with explicit "Recommended" badge)**: 75–90%.
- **Poorly-chosen defaults**: < 50% — and often *worse* than no default, because users don't trust the system afterward.

Periodically test by flipping the default; if acceptance drops dramatically, the default was matching genuine preferences. If acceptance stays high, the default may have been driving behavior more than fitting it.

## The ethics of defaults

### Honest defaults

A default is honest when:

- It serves the user's interest, plausibly more than the average alternative.
- The user is shown what they're accepting.
- The user can change it without penalty.

Examples: defaulting auto-save to ON, defaulting two-factor authentication to ON for new accounts.

### Manipulative defaults

A default is manipulative when:

- It serves the business at the user's expense.
- The user can't easily tell what's defaulted.
- Changing it requires friction (deep menus, multiple confirmations).

Examples: pre-checked email subscriptions; "remember me" defaulted on shared devices; auto-renew at full price defaulted.

The legal landscape is shifting: GDPR, CCPA, and increasing FTC enforcement penalize manipulative defaults. The product safe move and the long-term trust move are the same: honest defaults only.

### "Defaults" as legal default-rules

Note that the "default" idea predates UX — in contract law, default rules are the terms that apply absent explicit agreement. Behavioral economics translates this: defaults are the "law" of a product's choice space.

## Cross-domain examples

### Government policy

- **Organ donation** opt-out countries (Spain, Austria, France) vs. opt-in (US, UK historically): consistent ~5–10x higher donation rates with opt-out, no significant difference in survey-stated preferences.
- **Retirement savings**: opt-out 401(k) enrollment raised US savings rates measurably; the US Pension Protection Act (2006) explicitly enabled this.
- **Vaccination scheduling** by default appointment vs. opt-in: defaulting raises uptake.

These are not gamification tricks; they are structural design choices with large welfare effects.

### Industrial product design

- **Cars**: seatbelts auto-tightened on engine start (some models) increase wearing rates.
- **Appliances**: factory-default to energy-efficient modes; users override only when needed.
- **Smart thermostats**: default to schedules learned from past behavior.

### Consumer software

- **macOS / iOS** ship with strong privacy defaults. Apps must request permissions; defaults are restrictive. This is a default-driven privacy posture.
- **Chrome** historically defaulted permissive (cookies, notifications). Has shifted toward stricter defaults under regulatory pressure.

## When *not* to use a strong default

- Material commitments (purchases, account changes, data sharing) — require explicit choice.
- High-stakes irreversible decisions — confirm explicitly.
- When the system can't reasonably guess — ask.
- When the user community has strongly varied preferences — ask, or offer a one-question setup wizard.

## Closing

Defaults are the most efficient Hick's Law mitigation — they collapse the decision for most users without removing it for anyone. Used honestly, they improve outcomes; used manipulatively, they erode trust and increasingly invite regulation. Pick your defaults as if you'd be willing to defend them in front of your users.
