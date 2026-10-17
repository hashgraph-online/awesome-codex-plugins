# Extended glyph coverage

The portable set in `SKILL.md` is drawn to a single rule: use a glyph only when
a mainstream terminal font is likely to draw it. That rule keeps output readable
on a stock machine, and it costs coverage. Greek indices become `x_β`, a
superscript C becomes `A^C`, and a formula that would read as one symbol reads
as two characters instead.

If you run a font with wider Unicode coverage, you can spend that coverage. This
file is the opt-in set: every semantically correct super- and subscript code
point the portable rules leave on the table.

## Opting in

Nothing here applies unless you ask for it. Neither Claude Code nor Codex exposes
per-skill settings, so say it once and it holds for the session:

> Use extended glyph coverage from math-unicode.

To make it permanent, put the same line in the memory file your agent already
reads: `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex. The skill checks for
that instruction before reaching for anything below.

## Scope

Extended mode changes one thing: which single characters may become a script
glyph. It does not touch any other rule.

- Rule 5 is unchanged. Big-operator bounds stay bracketed: `∑[i=1..n]`,
  `∫[a..b]`, `lim[x→0]`. Per-character mapping is what produces `∫₀^∞`, one bound
  a glyph and the other a caret, and no amount of font coverage fixes it because
  there is no superscript `∞` to find.
- Multi-character scripts stay as they are: `x^(k+1)`, `n_{s,r}`.
- Rule 13 is unchanged. The Mathematical Alphanumeric Symbols block stays out,
  in extended mode as much as in portable mode, because its failure is copy and
  search rather than font coverage.

## The set

Counts are `fonts carrying the glyph / fonts measured`, from the same twelve
monospace fonts as the *Font coverage* table in `SKILL.md`. Regenerate with
`node scripts/measure-font-coverage.mjs <font-file>...`.

### Greek subscripts

| glyph | code point | fonts | portable form |
|---|---|---|---|
| ᵦ | U+1D66 | 2/12 | `x_β` |
| ᵧ | U+1D67 | 2/12 | `x_γ` |
| ᵨ | U+1D68 | 2/12 | `I_ρ` |
| ᵩ | U+1D69 | 2/12 | `x_φ` |
| ᵪ | U+1D6A | 2/12 | `x_χ` |

### Greek superscripts

| glyph | code point | fonts | portable form |
|---|---|---|---|
| ᵝ | U+1D5D | 2/12 | `x^β` |
| ᵞ | U+1D5E | 2/12 | `x^γ` |
| ᵟ | U+1D5F | 2/12 | `x^δ` |
| ᵠ | U+1D60 | 2/12 | `x^φ` |
| ᵡ | U+1D61 | 2/12 | `x^χ` |

`ᶿ` (superscript θ, U+1DBF) is not listed here. It measures as well as the Latin
blocks and is already part of the portable set, so `xᶿ` needs no opt-in.

### Latin capitals and small q

These have code points but no font in the measured set ships them, so they draw
as tofu almost everywhere. Enable them only if you have checked your own font.

| glyph | code point | fonts | portable form | note |
|---|---|---|---|---|
| ꟲ | U+A7F2 | 0/12 | `A^C` | Unicode 14.0 |
| ꟳ | U+A7F3 | 0/12 | `A^F` | Unicode 14.0 |
| ꟴ | U+A7F4 | 0/12 | `A^Q` | Unicode 14.0 |
| ꟱ | U+A7F1 | 0/12 | `A^S` | Unicode 17.0, September 2025 |
| 𐞥 | U+107A5 | 0/12 | `x^q` | Unicode 14.0, outside the BMP |

Nothing exists for superscript X, Y or Z, or for any subscript capital, in any
Unicode version. Those stay `A^X`, `M^Y`, `A^Z` and `A_B` in every mode.

## Checking your own font

The measured set is twelve fonts, not every font. To check the one you actually
run:

```bash
fc-list ":charset=1D68:spacing=100" family     # who ships ᵨ
printf 'xᵨ  Aꟲ  x\U000107A5\n'       # look for tofu
```

A glyph missing from your terminal font is often supplied by fontconfig from
another installed font. It draws, but at that font's advance width, which is
what pulls columns out of line in aligned derivations and matrices. Tofu means
no installed font has it at all.
