# Cultural mapping — working icon vocabulary

A reference catalog of dominant icon conventions, organized by function. Use this as a starting point, not a final word — convention strengths shift over time and across audiences.

## Universally recognized (in industrialized cultures)

These conventions are strong enough that the icon alone communicates the function for most adult users. Pair with a label only when usage is infrequent or the cost of misinterpretation is high.

- **Magnifying glass — search.** Strongly established. The single dominant convention.
- **House — home / homepage.** Strong. A few interfaces use a dot or globe instead, but the house is by far the most recognized.
- **Gear / cog — settings or preferences.** Strong. A wrench is a weaker variant.
- **Trash can — delete or discard.** Strong. The "X" is sometimes used as a competitor and confuses users.
- **Plus sign — add or create.** Universal mathematical convention.
- **Minus sign — remove or subtract.** Universal mathematical convention.
- **Pencil — edit.** Strong. Sometimes confused with "draw" or "annotate" in design tools.
- **Camera — take photo.** Strong, but the "video camera" variant means video, not photo.
- **Envelope — email or messages.** Strong, slightly weakening as messaging app conventions diversify.
- **Lock — security, locked state, private.** Strong. The "open lock" means unlocked or public.
- **Bell — notifications.** Strong, recently dominant.
- **Heart — favorite or like.** Strong. The "star" is a competitor with overlapping but slightly different connotations (favorite vs. quality rating).
- **Star — rating or favorite.** Strong. Often used for quality ratings (1-5 stars).
- **Question mark — help.** Strong.
- **Exclamation mark — warning or alert.** Strong.
- **Checkmark — confirm, done, or success.** Strong.
- **X mark — close, cancel, or dismiss.** Strong, but ambiguous between "cancel this dialog" and "delete this item." Usually disambiguated by position (X in the corner of a panel = close panel; X next to an item = remove item).
- **Arrow (left/right) — navigation back/forward.** Strong, supported by browser convention.
- **Arrow (up/down) — sort order, scroll direction, or value change.** Context-dependent.
- **Eye — visibility or preview.** Strong. The "eye with slash" means hidden.
- **Sun / moon — light/dark mode, or brightness.** Strongly established in recent years.
- **Speaker icon — audio output / volume.** Strong. The "speaker with slash" means muted.
- **Microphone — audio input / record.** Strong.
- **Refresh / circular arrow — reload or refresh.** Strong.
- **Hamburger (three horizontal lines) — main menu.** Strong on mobile, weaker on desktop.
- **Kebab (three vertical dots) — more options / context menu.** Strong on mobile, becoming dominant on desktop.
- **Calendar — date picker or scheduling.** Strong.
- **Clock — time picker or recent activity.** Strong.

## Strong but with regional / domain variation

These conventions are well-established within a context but vary significantly across cultures, regions, or audiences.

- **Floppy disk — save.** Strong for adult users in industrialized cultures, but a generation that has never used floppies finds it bewildering. Some products are migrating to a downward-arrow-into-tray icon, which has not yet reached convention strength.
- **Telephone handset — call or contact.** Strong, but the handset shape is increasingly anachronistic; a younger audience may interpret it as "old phone."
- **Speech bubble — chat or comment.** Strong, with multiple variants (rectangular vs. cloud-shaped vs. with tail) that all read as "talk-related."
- **Globe — internet, international, or external.** Used inconsistently for these three meanings. Always pair with a label.
- **Share icon — share content.** No dominant cross-platform convention; Apple and Android use different shapes. Use the platform-native icon and pair with a label on first encounter.
- **Currency symbol ($, €, £, ¥) — money or pricing.** Local. International products use a generic "coin stack" or "wallet" icon.
- **Mailbox — physical mail.** Country-specific shape.
- **Shopping cart — e-commerce purchase.** Strong in supermarket cultures; less recognizable in markets where supermarket carts are less common.

## Weak or domain-specific

These conventions exist within a specific user community but should not be assumed universal. Always label.

- **Wrench / spanner — tools or developer settings.** Conflicts with "gear" for general settings.
- **Database (cylinder stack) — data or storage.** Recognized by technical users; opaque to general audiences.
- **Network (nodes-and-edges) — graph, connection, or sharing.** Highly variable in interpretation.
- **Beaker / flask — experimental features or science.** Domain-specific.
- **Lightbulb — idea or insight.** Sometimes used for "tips" or "AI suggestions"; not strongly conventional.
- **Lightning bolt — speed, power, or "premium."** Highly variable.
- **Key — access or authentication.** Sometimes confused with "settings."
- **Tag — label, category, or filter.** Reasonably strong but ambiguous between these three meanings.
- **Folder — collection or category.** Strong for desktop users; weaker for mobile-native users.
- **Cloud — cloud storage or sync.** Strong, but conflated with "weather" in some contexts.
- **Pin — location or "pin to top."** Two distinct meanings; disambiguate with context.
- **Bookmark — save for later.** Strong, but conflated with "favorite."

## Color conventions

Color conventions interact with cultural mappings and require similar caution.

- **Red — error, danger, stop, destructive action.** Strong in driving cultures; "auspicious" in some Asian cultures (use carefully in international UI).
- **Green — success, go, confirm, positive change.** Strong in driving cultures.
- **Yellow / amber — warning, caution, in-progress.** Strong.
- **Blue — informational, neutral, link, default action.** Strong in software UI; sometimes "trust / corporate" in marketing.
- **Gray — disabled, inactive, secondary.** Strong.

Always pair color with a non-color cue (shape, icon, label) for accessibility.

## Anti-pattern: the obscure-icon-set

Designers sometimes adopt an entire custom icon set across an interface, replacing conventional icons with bespoke variants for visual coherence. The result is universally less usable: every icon now requires the user to learn it, and the convention strength accumulated by the standard icons is lost. Visual coherence is achievable through color, weight, and stroke style — the icon shapes themselves should hew to convention.

A related anti-pattern is the "minimalist line-icon set" where every icon is a thin outline with no fill, designed to look harmonious. Frequently the result is a row of icons that all look similar and require careful inspection to distinguish. If your icons cannot be told apart at a glance, you've lost the central virtue of icon-based UI. Either weight the icons differently, label them all, or pick a more varied set.

## Convention drift over time

Icon conventions are not stable. The floppy disk for "save" is weakening as a generation grows up that has never used floppies. The telephone handset for "call" is weakening as wired-handset phones disappear. The hamburger menu was a niche convention in 2010 and is now near-universal. The kebab menu was unknown a decade ago and is now standard.

When a convention is in flux, the safe path is to pair the icon with a label, at least until the new convention has stabilized. Trying to lead the convention is risky; following it once it's established is safe.

## Test your icons

Show the icon set, without labels, to five users from your actual audience. Ask them what each icon means. Anything that fewer than four out of five interpret correctly needs a label or a different icon. This test takes ten minutes and prevents weeks of post-launch confusion.

## Cross-reference

For more on when iconic forms are appropriate at all, see `iconic-representation`.
