# widget: an HTML widget inside a message

**When:** an interactive card in the message, a live status card, a widget that doesn't answer,
wallet pay or sign inside a message.

## Read

- Runtime, availability, query flow, limits: `references/widgets.md`.
- Tokens, type, states, RTL, accessibility: `references/widget-design-system.md`.
- State architecture, backends, Mini App hand-off, channel-safe variants:
  `references/widget-patterns.md` (§1, §2 and §11-14 first).
- Wallet pay, sign, TON transfers: `references/wallet-and-ton.md`.

## Steps

1. Decide that a widget is the right surface (`widget-patterns.md` §1); production = private
   chats only; always a caption and a text or button path.
2. Start from the kit: `tgui.py widget build ...`; restyle with `tgui.py widget design`.
3. Server handler: answer each query once within 15 s; state only via edits; no secrets in code
   or `public_data`; check rights on every query.
4. `tgui.py check widget <file> --strict`, `tgui.py widget lint`, `tgui.py widget preview`
   (a mock: it proves nothing about real clients).

## Without scripts

Check the size budget by hand (zlib level 9, see the limits in `widgets.md`) and name the
evidence as "static".

## Done

Supported context, caption and fallback, size checked, server-side state, evidence level named.

## Next

`post` a channel-safe variant, or `mini-app` if the widget outgrew its limits.
