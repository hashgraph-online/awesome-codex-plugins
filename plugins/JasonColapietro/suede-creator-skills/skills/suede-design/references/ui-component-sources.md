# UI Component Sources

Historical third-party source notes for an authorized component import. The
recorded checks below are dated 2026-08-26, not a current security or license
certification. They do not authorize downloads, installation or execution.
Verify the actual selected repository revision, dependency behavior, license and
runtime suitability before reuse. Existing local tokens/components/icons win.
A review does not need a new component package.

The repository names in the table identify sources; they are not immutable
commit pins. Resolve and record a real commit/version before importing code.

| Source | URL | Source repo | Holds | Stack | License / tier |
|---|---|---|---|---|---|
| shadcn/ui | https://ui.shadcn.com | github.com/shadcn-ui/ui | Design-system foundation: primitives, forms, dialogs, tables, blocks: the registry the rest plug into | React, Tailwind | MIT, free |
| beUI | https://beui.dev | github.com/starc007/ui-components | 100+ animated components: modals, docks, command palettes, dynamic islands, carousels | React/Next.js, Motion (Framer), Tailwind | MIT core; paid Pro (pro.beui.dev) |
| Rare UI | https://rareui.com | github.com/swamimalode07/rare-ui | Small set of uncommon animated one-offs: fluid orb, gravity letters, duration picker, OTP input | React, one file per component, shadcn CLI install | MIT, free |
| Transitions.dev | https://transitions.dev | github.com/Jakubantalik/transitions.dev | Micro-transitions: modal, skeleton loader, badge, toggle, dropdown animation snippets; also packaged as an installable agent skill (`Jakubantalik/transitions-dev`) | Portable CSS (`t-*` namespaced), copy-paste, no framework deps | Free tier; paid Pro |

Name-collision warning: an unrelated project also called "RareUI" lives at
rareui.in (different author, different repo). The vetted one is rareui.com
backed by the source repo above: resolve and inspect a revision before importing.

## Not yet vetted: do not treat as a vetted source

- **Beautiful UI** (https://www.beautifului.dev, repo
  `github.com/TurboKach/ai-native-react-components`, MIT): AI-native
  primitives: streaming text, thinking states, tool-call traces,
  human-in-the-loop approval flows. The only source in this file aimed at
  that register, and the reason it stays listed. It fails the vetting bar as
  of 2026-08-26: the domain was registered ~2026-08-12 and carries a
  "suspicious" threat-reputation verdict: a pattern consistent with domain
  newness rather than confirmed malice (the repo states "From
  beautifului.dev" and its owner account has been active since 2017), but
  consistent-with is not cleared. Promote it to the table only when both
  hold: the threat verdict has cleared, and the domain is older than 90
  days. These historical notes do not establish current safety. For a proposed
  import, verify an exact source revision, read every file and dependency,
  and use the authorized adoption checklist below.

## Which source for which job

- Base primitive, form, table, or dialog scaffolding → shadcn/ui.
- Agent or AI-product surface: chat stream, thinking state, tool-call
  display, approval step → no vetted source yet; see Beautiful UI in the
  not-yet-vetted section for the interim path.
- Interaction set-piece: dock, command palette, dynamic island, carousel →
  beUI.
- Raw material for the surface's signature move → Rare UI, then customize
  until check 3 below passes.
- Motion detail on a component that already exists, modal open, skeleton,
  toggle, badge → Transitions.dev.

## Adoption checklist (run per imported component)

1. **Local first.** Name the local gap before importing: which token,
   component, or pattern the system lacks. If the local system has the piece,
   style it instead.
2. **Inspect before import.** Use only an authorized, reviewed source and
   installation path. Read the selected component, dependency and install-hook
   behavior first; record its exact revision and license. No automatic CLI,
   remote execution or install belongs in an audit.
3. **Signature test.** A stock component from a public library is raw
   material, not a signature move: anyone can install the same one. It counts
   as the surface's memorable move only after subject-native customization:
   swap its content, motion, or geometry for something only this product would
   show.
4. **Retokenize before commit.** Replace the import's palette, radii, spacing,
   and font references with local tokens. An import still carrying its source
   palette is unfinished.
5. **Behavior still applies.** Match the project's motion language and verify
   reduced-motion behavior. Use the contextual checks in `design-laws.md`; do
   not import a fixed easing, scaling or stagger recipe as a universal rule.
6. **License and tier check.** Confirm the license file in the source repo
   before shipping to a public or client surface. Free tiers only unless the
   user owns the paid tier (beUI Pro, Transitions.dev Pro), never paste paid
   content from a demo page.
7. **Render the import.** The source's demo proves the demo. Render the
   component in the local stack at desktop and mobile widths before claiming
   it works.
