# Deep redesign path: research the project, rethink the menus, tune the bot

> Status: **Heuristic** (this skill's process) except where marked **API**. Reviewed against
> Bot API 10.4 on 2026-11-15. Tool: `scripts/style_profile.py`. Knobs:
> `bot-style-profile.md`. Builds on `project-adaptation.md` (find the interface),
> `auditing-existing-bots.md` (inventory and diagnose) and `consistency-and-review.md`
> (final pass).

Use this path when the request is bigger than fixing screens: *"make the bot feel like our
product"*, *"rethink the whole menu"*, *"redo navigation from scratch"*, *"adapt the bot to
our brand"*, *"переосмысли меню"*, *"адаптируй бота под стиль проекта"*. It orchestrates the
other references in a fixed order with explicit gates, so a full rethink stays consistent,
reversible and inside what Telegram actually allows.

The output is three artifacts kept in the user's project, not in chat:

| Artifact | Default path in the target project | Holds |
|---|---|---|
| Research notes | `docs/telegram-ui/research.md` | evidence: sources read, brand traits, audience, ceilings |
| Style profile | `docs/telegram-ui/profile.json` | every tunable decision, each with its source |
| Redesign plan | `docs/telegram-ui/plan.md` | old → new screen map, migration, rollout, what stays |

Put them where the project already keeps design docs (next to `DESIGN.md`, in `docs/design/`)
if such a place exists. They are the bot's design system: the next change reads them instead
of re-researching.

## 0. Rights and mandate (decide before reading code)

Two independent ladders. Determine both from the environment and the user's words, state the
result in one line, and act within it.

**Access: what the agent can reach.**

| Level | The agent has | It can do |
|---|---|---|
| A0 | a pasted snippet or screenshots | infer, propose, mark every assumption |
| A1 | read access to the bot repo | full research and screen map |
| A2 | write access to the repo | implement on a branch, run tests |
| A3 | other project sources: website, Mini App, design repo, Figma export, brand folder | style research beyond the bot code |
| A4 | a **test** bot token in an environment variable | live sends, read-back of custom emoji, real-client checks |

Check A3 by looking, not by asking: sibling folders, monorepo packages (`apps/web`,
`miniapp/`), `homepage` in `package.json`, URLs in the README, `DESIGN.md`, `components.json`,
tokens files. Reach a website only when the user named it or the repo links it, and read only
public pages. Never read `.env*` values, key files or credentials to "learn the project";
`scripts/style_profile.py probe` skips them by design. A4 needs the user to provide the token
variable; never ask for a token in chat.

**Mandate: what the agent may change.**

| Level | Scope | Default when |
|---|---|---|
| M1 Wording | texts, labels, toasts, command descriptions | the user asks about text or tone |
| M2 Screens | layout, grouping, emphasis, icons, body format inside existing screens | "improve the menu", "make it nicer" |
| M3 Structure | screens added, merged, removed; navigation; commands; menu button; entry and onboarding | "rethink", "redo from scratch", "переосмысли", "the whole menu" |
| M4 Contracts | `callback_data` scheme, i18n keys, deep-link payloads, command names | only with an explicit yes, always with a migration (§7) |

M3 does not imply M4: a full rethink can keep every contract by mapping new screens onto old
callbacks. Reach for M4 only when the old scheme blocks the new structure, and say why.

Gates (the only points that wait for the user): voice samples (§5), the new structure when it
removes or renames something users already know (§6), and any M4 change (§7). Everything else
proceeds.

## 1. Project research (A1-A3)

Run the probe first; it is cheap and points at what to read:

```bash
py -3 <skill-dir>/scripts/style_profile.py probe <project-root> --json > probe.json
```

It reports, without reading secrets: SDK and version hints, design docs, design tokens (CSS
custom properties, Tailwind colours, token JSON, shadcn `components.json`), fonts, brand
assets, locale catalogs with their languages and the longest strings, emoji density in user
texts, and Telegram touchpoints (keyboards, `callback_data`, commands, menu button, Mini App,
widgets, custom emoji ids, `style` use). It finds; it does not judge. Then read, in this order:

1. **Product and audience**: README, landing copy, docs. Who uses the bot, what jobs they
   come for, how often, on which devices, in which languages. Write the top 5-10 user jobs.
2. **Brand**: `DESIGN.md` or brand guide, tokens, logo, Mini App styles, site copy. Extract
   *traits*, not pixels: calm or energetic, dense or airy, formal or casual, technical or
   plain, playful or strict; the accent colour and whether it is light or dark; icon style
   (outline / solid, rounded / sharp).
3. **Voice**: 10-20 real strings from the locale catalogs and the site, including errors.
   Note address form (you / formal you; ты / вы), sentence length, emoji habit, punctuation.
4. **Usage signals** if the project already has them in aggregate (analytics dashboards,
   command counters, support FAQ): which commands and screens matter. Never pull raw user
   messages or personal data for this.
5. **Constraints**: SDK Bot API ceiling (`sdk-compatibility.md`), contexts the bot lives in
   (private, groups, channels, business, inline), live locales, custom emoji eligibility
   (`custom-emoji.md`: Fragment usernames, or owner Premium outside channels).

Write `research.md` with a source per claim (`file:line`, URL, or "user said"). A trait with
no source is an assumption and is labelled so.

## 2. Translate the brand into what Telegram allows

A regular bot message has no CSS (**API**). Brand reaches the user only through the surfaces
below; decide each one explicitly. Most of a brand lives in words, structure and rhythm, not
in colour.

| Brand trait | Telegram surface | What is possible | What is not |
|---|---|---|---|
| Name, promise, first impression | `setMyName`, `setMyDescription` (empty chat screen), `setMyShortDescription` (profile, shares), `setMyProfilePhoto` (**API**) | per-language name and texts; a brand avatar | layout, colour of the chat |
| Voice and tone | every text, toast, command description, placeholder | full control | — |
| Density and rhythm | message length, line breaks, headings, lists, tables, expandable quotes, Rich Messages | full control within limits (`limits-and-splitting.md`) | custom fonts, spacing in px |
| Accent colour | button `style` (`primary`/`success`/`danger`) **API**; widgets and Mini Apps through theme variables | meaning-based emphasis | brand hex on buttons or text; brand chrome in widgets (`widget-design-system.md`) |
| Icon style | Unicode emoji, or one premium custom-emoji pack in the brand's drawing style (`emoji-packs.md`) | one family bot-wide when eligible | invented ids; mixed families; icons the user must decode |
| Imagery | profile photo, media covers, link previews, post images | full control over the images | backgrounds, themes of the user's client |
| Full visual identity | Mini App (hosted page; follows the Telegram theme by default, may carry brand) | anything a web page can do | it is a separate surface, not a chat message |
| Navigation feel | commands, menu button, reply vs inline keyboards, deep links, edit-in-place | full control | client chrome |

Write the decision per row into the profile (`bot-style-profile.md`). A brand colour that
cannot reach a surface is recorded as "not applicable", not approximated with coloured emoji.

## 3. Current state (A0-A1)

Reuse, do not redo: `project-adaptation.md` steps 2-7 for the screen/state map and
`auditing-existing-bots.md` passes 0-3 for the text inventory and ranked findings. Add two
columns the redesign needs: **which user job each screen serves** and **how a user reaches it**
(command, button path, deep link, notification). Screens that serve no job, and jobs that need
more than two taps from home, are the raw material of §6.

## 4. Draft the style profile

Generate a starting profile from the probe, then edit it by hand:

```bash
py -3 <skill-dir>/scripts/style_profile.py scaffold probe.json > docs/telegram-ui/profile.json
```

Every value carries `source` (evidence) or `"assumed"`. The knobs and their effect are in
`bot-style-profile.md`. Check it before anything is designed from it:

```bash
py -3 <skill-dir>/scripts/style_profile.py check docs/telegram-ui/profile.json
```

## 5. Voice gate: show, don't ask

Rewrite 2-3 representative real messages under the profile: the home screen, one error, one
confirmation. If tone or density is still uncertain, show the same message in the two
candidate voices side by side. One answer from the user fixes `voice` and `density`; record it
in the profile with `"source": "user"`. Do not rewrite message #4 before this.

## 6. Rethink the structure (M3)

Design from jobs, not from the old menu.

1. **Group jobs** by frequency and intent: daily (one tap), occasional (two taps), rare (a
   command or settings). Settings, help and language are never top-level work.
2. **Pick the entry model** per bot type (`bot-archetypes.md`, `navigation-and-flows.md`):
   - one home screen edited in place, with 2-6 actions (most bots);
   - a reply keyboard only when users repeat 2-4 actions all day (`reply-keyboards.md`);
   - a menu button opening a Mini App when the real work is a form or a catalogue;
   - commands as shortcuts to the same screens, never as the only path.
3. **Draw the new map**: each screen with its job, its keyboard, Back/Home slots, empty,
   error and loading states, the body format (`format-selection.md`), and where personal
   data appears (`ephemeral-and-personal.md`).
4. **Map old → new**: every old screen, command and deep link gets a row: kept, merged into,
   replaced by, or removed with reason. Nothing disappears silently; users have old messages
   with old buttons in their chats.
5. **Apply current capabilities where they serve a job** (the initiative rule in `SKILL.md`):
   Stop on long answers, disabled Submit and `force_reply` in forms, personal panels in
   groups, a live widget card, one emoji pack. Name each choice and its job.
6. **Prototype 2-3 key screens** as exact payloads and validate them
   (`scripts/validate_keyboard.py`, `scripts/audit_copy.py`). If the map removes or renames
   anything users know, this is the gate: show the map and the prototypes, then continue.

Record one recommended structure. Offer an alternative only when it hinges on a product
decision the agent cannot make (for example "Mini App catalogue vs in-chat catalogue"), and
then say which you recommend.

## 7. Migration (when M4 or a removed screen is involved)

- **`callback_data`**: introduce a versioned prefix for the new scheme (`v2:`) and keep a
  legacy decoder that routes every old value to its new screen or to a short "this menu was
  updated" screen with a Home button. Old messages in users' chats must still respond: every
  tap gets an answer, never a spinner (`inline-keyboards.md`). Test old payloads explicitly.
- **Commands**: change them with `setMyCommands` per scope and language in one release; keep
  a removed command as a hidden alias that routes to its replacement for one release cycle.
- **Deep links and `/start` payloads**: never break published links; map old payloads.
- **i18n keys**: new meaning gets a new key; mark replaced keys stale for every locale and
  agree with the user how translations are refreshed (`auditing-existing-bots.md`, "rework").
- **Menu button, name, descriptions, photo**: set per language; record the previous values
  in `plan.md` so they can be restored.
- **Rollout**: behind a flag or per-user cohort when the project has one; otherwise ship the
  new map with the legacy decoder and remove the decoder in a later, separate change.

## 8. Build, verify, report

Orchestrate with the skill's roles when the host supports subagents; otherwise do the same
steps yourself in this order. Roles cannot start other roles, so the main agent coordinates.

| Phase | Role | Input | Done when |
|---|---|---|---|
| §1-§6 research and design | `telegram-bot-designer` (read-only) | this file, probe output | research, profile and plan written; prototypes validated |
| widgets in the plan | `telegram-widget-builder` | the widget rows of the plan | widget built, size and lint green |
| §7-§8 implementation | `telegram-bot-builder` | plan + profile | screens built in screen order, legacy decoder tested |
| channel posts in scope | `telegram-publisher` | the post types of the plan | preview approved; nothing published without approval |
| verification | `telegram-bot-reviewer` | the diff, plan, profile | findings fixed or listed |

Verification is the same for every path (`consistency-and-review.md`), plus:

- every screen matches the profile: run `scripts/style_profile.py check` on the profile and
  `scripts/audit_copy.py` on the catalog; labels inside the profile's length budget in the
  longest live locale;
- every old `callback_data`, command and deep link from the §6 map is covered by a test;
- with A4 only: send the key screens to the test bot, read custom emoji back, and look at
  them in a real client. Without A4, say that client rendering is unverified.

Report: what the bot is now (map), what changed per screen, which profile values came from
evidence and which were assumed, what stayed (contracts, screens), the migration, and the
evidence level.

## 9. Tuning loop

After the redesign the profile is the single place to tune the bot. A request like "fewer
emoji", "shorter messages", "more formal", "buttons in one column", "make Delete red only on
the last step" is a profile edit, then a sweep:

1. change the knob in `profile.json` with `"source": "user"` and the date;
2. `style_profile.py check` the profile;
3. find every screen the knob touches (the profile's knob table names the surfaces) and
   update them all in one change, not just the screen the user looked at;
4. re-run the copy and keyboard validators and the tests.

A tuning request that contradicts an API rule (a fourth button colour, brand hex on a button,
custom emoji in a channel without Fragment) is answered with the nearest allowed setting, not
silently approximated.

## Anti-patterns

- Restyling before the research: a "brand" redesign built from the agent's taste.
- Copying web brand pixels into chat: coloured emoji as a palette, ASCII frames, fake
  headers. Telegram draws the chat; the bot brings words, structure and icons.
- A full rethink that silently breaks old messages, published deep links or translations.
- One flat list of 40 changes instead of a map, a profile and a few decisions.
- Treating the probe output as conclusions; it only says where to look.
- Tuning one screen and leaving the rest on the old setting.
