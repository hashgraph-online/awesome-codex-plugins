# design

Design skills — UX psychology, visual design, accessibility, and Apple featuring readiness for web, SaaS, and mobile apps.

One of the five [Tartiner Labs skill collections](../../README.md). Once the plugin is installed, invoke a skill through your agent's skill or command interface, for example `/design:ux-psychology` in Claude Code.

## Skills

| Skill | Description |
|-------|-------------|
| [ux-psychology](skills/ux-psychology) | Apply research-backed UX psychology (Hick, Fitts, cognitive load, Gestalt, defaults, reciprocity) while building screens and flows, or audit them on request — detects web/SaaS, Apple platforms, Android, and React Native/Expo |
| [visual-design](skills/visual-design) | Pick a visual direction and apply it as tokens — colour, typography, spacing, surfaces, buttons, icons, and imagery — while building screens, or audit code, screenshots, and mockups on request — for web, Apple platforms, Android, and React Native/Expo |
| [accessibility](skills/accessibility) | Build and audit accessible UI mapped to WCAG 2.2 AA — screen readers, keyboard and focus, contrast, text scaling, reduced motion, targets, forms, and media — for web, Apple platforms, Android, and React Native/Expo |
| [apple-featuring](skills/apple-featuring) | Review an Apple platform app's readiness for App Store featuring and the Apple Design Awards, and plan the featuring nomination in App Store Connect |

## Agents

Claude Code only.

| Agent | Description |
|-------|-------------|
| [a11y-audit](agents/a11y-audit.md) | Read-only accessibility audit of a whole app or several screens against WCAG 2.2 AA. Use for full-app, multi-screen, or pre-release accessibility reviews — returns an impact-ranked report without editing files. Detects web, Apple platforms, Android, and React Native/Expo. |
| [ux-audit](agents/ux-audit.md) | Read-only UX psychology audit of a whole app or several screens. Use for full-app or multi-screen UX reviews — returns a severity-ranked report without editing files. Detects web/SaaS, Apple platforms, Android, and React Native/Expo. |

## Installation

**Claude Code**

```bash
claude plugin marketplace add tartinerlabs/skills
claude plugin install design@tartinerlabs
```

**Codex and Cursor:** open this repository in the app and install `design` from the repo marketplace.

**OpenCode** (v2):

```bash
opencode plugin add 'github:tartinerlabs/skills#main::path:plugins/design'
```

**skills.sh**, one skill at a time:

```bash
pnpm dlx skills add tartinerlabs/skills/ux-psychology
```

The [root README](../../README.md#installation) has the details for every channel.

## License

MIT
