---
summary: "The style profile JSON recording a bot's interface decisions (voice, density, keyboards, emphasis, icons, navigation, formats) and which knob touches which surface; read when tuning a bot's look."
verified: "2026-11-15"
bot_api: "10.4"
---

# Bot style profile: the knobs that tune a bot

> Status: **Heuristic** (this skill's design system) except rows marked **API**. Reviewed
> against Bot API 10.4 on 2026-11-15. Tool: `scripts/style_profile.py` (`probe`, `scaffold`,
> `check`). Example: `examples/style-profile/profile.example.json`. Process:
> `redesign-orchestration.md`.

The profile is one JSON file in the bot's project (default `docs/telegram-ui/profile.json`)
that records every interface decision of the bot: voice, density, keyboards, emphasis, icons,
navigation, formats, profile texts and which contracts are frozen. Screens are built from it;
tuning the bot means editing a knob and sweeping the surfaces it touches.

Rules:

- **Every knob has a source.** `sources` maps a dotted path (`"voice.address"`) to the
  evidence: `file:line`, a URL, `"user 2026-11-15"`. A knob without a source is an assumption;
  `check` lists them so they are confirmed or kept consciously.
- **Unknown keys are errors.** A typo in a knob must not silently fall back to a default.
- **API limits are errors, taste is a warning.** `check` fails on what Telegram rejects or what
  contradicts this skill's rules (`floor.md`); it warns on values outside the usual ranges.
- **A missing section uses the defaults below.**

## Sections and knobs

### `bot` — what the bot is

| Knob | Values | Default | Effect |
|---|---|---|---|
| `archetype` | free text, ideally a family from `recipes/use-cases.json` | — | picks the closest recipes |
| `contexts` | any of `private`, `group`, `channel`, `business`, `inline` | `["private"]` | gates drafts, ephemeral panels, widgets, emoji eligibility |
| `locales` | language codes | `["en"]` | label budget is checked in the longest one |
| `primary_locale` | one of `locales` | first locale | source language for rewrites |
| `sdk`, `bot_api_ceiling` | text, e.g. `"aiogram 3.22"`, `"10.4"` | — | features above the ceiling need a bridge (`sdk-compatibility.md`) |

### `mandate` — what the agent may reach and change

| Knob | Values | Default |
|---|---|---|
| `access` | `A0`-`A4` (`redesign-orchestration.md` §0) | `A1` |
| `change` | `M1` wording, `M2` screens, `M3` structure, `M4` contracts | `M2` |

### `voice`

| Knob | Values | Default | Surfaces |
|---|---|---|---|
| `address` | `informal`, `formal`, `impersonal` | `informal` | every text, toast, placeholder |
| `tone` | `calm`, `friendly`, `warm`, `playful`, `strict`, `technical` | `calm` | every text; errors first |
| `person` | `we`, `i`, `impersonal` | `impersonal` | confirmations, errors, onboarding |
| `exclamations` | `never`, `rare`, `allowed` | `rare` | results, onboarding |

Address in Russian and Ukrainian maps to ты/вы, ти/ви; in English `formal` means no
contractions and full sentences. `probe` counts address forms in ru/uk catalogs.

### `density`

| Knob | Values | Default | Surfaces |
|---|---|---|---|
| `max_body_lines` | 1-40 | `8` | menu and result bodies (warn above 15) |
| `max_sentences_per_paragraph` | 1-6 | `2` | all prose |
| `headings` | `bold_line`, `rich_heading`, `none` | `bold_line` | screen titles, reports |
| `tables` | `never`, `when_compared`, `prefer` | `when_compared` | data screens (`tables.md`) |
| `long_text` | `rich_message`, `split`, `document` | `rich_message` | AI answers, reports, long reads |

### `keyboard`

| Knob | Values | Default | Surfaces |
|---|---|---|---|
| `max_actions_per_screen` | 1-12 | `6` | every inline keyboard, excluding navigation (warn above 8) |
| `max_buttons_per_row` | 1-8 | `2` | every keyboard (warn above 3: labels truncate on phones) |
| `label_max_chars` | 4-64 | `20` | every label, in the longest locale (warn above 30) |
| `label_form` | `verb_object`, `noun`, `mixed` | `verb_object` | action buttons |
| `nav_row` | `last`, `first`, `none` | `last` | Back / Home position |
| `back_label`, `home_label` | text | `"← Back"`, `"Home"` | one label bot-wide (`consistency-and-review.md`) |
| `confirm_destructive` | `true`, `false` | `true` | delete, cancel order, leave, revoke |

### `emphasis`

| Knob | Values | Default | Rule |
|---|---|---|---|
| `primary_per_screen` | `0`, `1` | `1` | more than one `primary` is an error (skill rule) |
| `success_on_commit` | `true`, `false` | `true` | Pay, Confirm, Save on the final step |
| `danger` | `after_confirm`, `on_destructive`, `never` | `after_confirm` | `danger` on the confirming button only |

`style` accepts only `primary`, `success`, `danger` (**API**). A brand colour is never a style.

### `icons`

| Knob | Values | Default | Rule |
|---|---|---|---|
| `system` | `none`, `unicode`, `custom` | `unicode` | one system per bot (`visual-language.md`) |
| `eligibility` | `none`, `fragment`, `premium`, `unverified` | `none` | `custom` needs `fragment` or `premium`; channels need `fragment` (**API**) |
| `pack` | pack/family name | `null` | required for `custom`; one family (`emoji-packs.md`) |
| `in_labels` | `leading`, `none` | `leading` | icon before the label text, never instead of it |
| `in_body` | `none`, `status_only`, `section_markers` | `status_only` | where emoji may appear in message text |
| `max_per_message` | 0-12 | `3` | decoration budget (warn above 5) |

### `navigation`

| Knob | Values | Default | Surfaces |
|---|---|---|---|
| `entry` | `home_screen`, `reply_keyboard`, `menu_button_mini_app`, `commands_only` | `home_screen` | `/start`, menu button, returning users |
| `edit_in_place` | `true`, `false` | `true` | screen transitions (editing ≠ resending) |
| `max_depth` | 1-5 | `2` | taps from home to any frequent job (warn above 3) |
| `menu_button` | `commands`, `web_app`, `default` | `commands` | `setChatMenuButton` |
| `commands` | list of `{command, description}` | `[]` | `setMyCommands` (**API**: name 1-32 chars of `a-z`, `0-9`, `_`; description 1-256; at most 100) |

### `feedback`

| Knob | Values | Default |
|---|---|---|
| `ack_every_tap` | `true` (only value the skill accepts) | `true` |
| `progress` | `named_stages`, `chat_action`, `none` | `named_stages` |
| `ai_streaming` | `draft_with_stop`, `edit_throttled`, `none` | `draft_with_stop` (drafts: private chats only, **API**) |

### `formats`

Free text per knob: `date`, `time`, `number_grouping`, `currency`. One format bot-wide; dates
and numbers follow the reader's locale when the project localizes them.

### `profile_texts` — the bot's own profile, per language (**API**)

`{"<lang>": {"name": ≤64, "short_description": ≤120, "description": ≤512}}` for
`setMyName`, `setMyShortDescription`, `setMyDescription`. The description is the first thing a
new user reads in an empty chat; write it in the profile's voice. The profile photo is a file
path in `brand.avatar` and is set with `setMyProfilePhoto`.

### `brand`

`traits` (list of words from the research), `accent` (hex, informational: it reaches only a
Mini App or hosted images, never buttons or regular text), `icon_style`
(`outline`, `solid`, `duotone`, `flat`, `mixed`) used to choose an emoji pack, `avatar`.

### `contracts` — what the redesign must not break

| Knob | Values | Default | Non-default needs |
|---|---|---|---|
| `callback_data` | `frozen`, `versioned` | `frozen` | `mandate.change = M4`, `callback_prefix` (1-16 bytes), a legacy decoder |
| `i18n_keys` | `frozen`, `new_keys_for_new_meaning` | `frozen` | `M4` |
| `deep_links` | `frozen`, `mapped` | `frozen` | `M4` and an old → new table |
| `commands` | `frozen`, `aliased` | `frozen` | `M4`; removed commands stay as hidden aliases for one release |

## Tuning: which knob touches which surface

A tuning request edits the profile first, then every surface in the knob's row, in one change.

| Request | Knob | Sweep |
|---|---|---|
| "more formal", "на вы" | `voice.address` | all locale strings of the primary locale; mark other locales stale |
| "less chatty", "shorter" | `density.max_body_lines`, `max_sentences_per_paragraph` | menus, results, onboarding, errors |
| "fewer emoji" | `icons.in_body`, `icons.max_per_message` | bodies and toasts; labels keep their icons unless `in_labels` changes |
| "buttons in one column" | `keyboard.max_buttons_per_row = 1` | every keyboard builder |
| "red only on the last step" | `emphasis.danger = after_confirm` | destructive flows |
| "premium icons" | `icons.system = custom`, `eligibility`, `pack` | every icon slot (`emoji-packs.md`), with fallback |
| "menu in a Mini App" | `navigation.entry`, `navigation.menu_button` | `/start`, menu button, commands |
| "change the bot's description" | `profile_texts` | `setMyDescription` per language |

After the sweep: `check` the profile, run `scripts/audit_copy.py` and
`scripts/validate_keyboard.py`, run the project's tests.
