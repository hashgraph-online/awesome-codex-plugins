---
name: math-unicode
description: Use when a response needs mathematical notation (equations, filters, set-builder notation, statistics, calculus, linear algebra, logic, ratios, drops, counts) and the output goes to a terminal or TUI that cannot render LaTeX: Claude Code, Codex CLI, SSH and tmux sessions, CI logs. Load it before composing, including when the user explicitly mentions math-unicode. Emit Unicode glyphs inline, never raw LaTeX delimiters or commands. Do not use when the host renders math natively, such as ChatGPT or Codex on desktop and web, notebooks, or a KaTeX/MathJax target, and do not use when the user asked for LaTeX or a .tex file.
disable-model-invocation: false
---

# math-unicode

When emitting mathematical notation in a terminal coding agent (Claude Code, Codex CLI, or similar), **always use Unicode glyphs inline** — never wrap math in `$…$`, `\(...\)`, or `$$...$$`. These terminals do not render LaTeX; raw delimiters appear as plain dollar signs and reduce readability.

## When this skill applies

Two conditions, both required: the response carries mathematical notation, and
the surface it lands on does not render LaTeX.

Surfaces that do not render LaTeX (apply the skill):
- Claude Code, Codex CLI, and other terminal or TUI coding agents
- Anything read through SSH, tmux, a pager, or a CI log

Surfaces that render math natively (do not apply the skill):
- ChatGPT and Codex on desktop and web, where math already renders
- Notebooks, and any target consumed by KaTeX or MathJax

No host exposes a per-surface predicate to a skill today, so this boundary is a
judgement the model makes from its own context. If you cannot tell, and the
session is a terminal coding agent, apply the skill.

Triggers (use Unicode math):
- Equations, formulas, derivations
- Filter conditions, set-builder notation
- Statistics: probabilities, expectations, distributions
- Calculus, linear algebra, logic
- Counts, ratios, fractions, drops where precision matters

Skip (do not transform):
- The user explicitly asks for LaTeX or a `.tex` file
- Math inside fenced code blocks (preserve source syntax)
- Strings being passed to a system that consumes LaTeX (KaTeX MCP, etc.)

## Glyph cheatsheet

### Greek

```
lowercase   α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ υ φ χ ψ ω
uppercase   Α Β Γ Δ Ε Ζ Η Θ Ι Κ Λ Μ Ν Ξ Ο Π Ρ Σ Τ Υ Φ Χ Ψ Ω
variants    ϵ ϑ ϕ ϖ ϱ ς
```

### Operators

```
arithmetic     + − × ÷ ± ∓ · ∗ ⋅ ∘ ⊕ ⊖ ⊗ ⊘ ⊙
big            ∑ ∏ ∐ ∫ ∬ ∭
roots          √ ∛ ∜
calculus       ∂ ∇ Δ ∆
constants      ∞ ∅
```

### Relations

```
equality       =  ≠  ≈  ≅  ≡  ≜  ≝  ≐  ∝  ∼  ≃  ≢
order          <  >  ≤  ≥  ⊴  ⊵
set            ∈ ∉ ∋ ∌  ⊂ ⊃ ⊆ ⊇ ⊊ ⊋  ⊏ ⊐ ⊑ ⊒
set ops        ∪ ∩ ⊎ ⊔ ⊓        (set difference: A \ B)
```

### Logic & arrows

```
logic          ∧ ∨ ¬ ⊕   ⊢ ⊥ ⊤
quantifiers    ∀ ∃ ∄ ∴ ∵
arrows         → ← ↔ ⇒ ⇐ ⇔ ↦ ↪ ↩ ↑ ↓ ⇑ ⇓ ⟶ ⟵ ⟷ ⊸
```

### Number sets & brackets

```
sets           ℕ ℤ ℚ ℝ ℂ ℙ ℍ
brackets       ⟨ ⟩  ⌈ ⌉  ⌊ ⌋  ‖ ‖
```

### Sub/superscript glyph blocks

```
superscript    ⁰ ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹  ⁺ ⁻ ⁼ ⁽ ⁾  ⁱ ⁿ ᵃ ᵇ ᶜ ᵈ ᵉ ᶠ ᵍ ʰ ʲ ᵏ ˡ ᵐ ᵒ ᵖ ʳ ˢ ᵗ ᵘ ᵛ ʷ ˣ ʸ ᶻ
sup (capital)  ᴬ ᴮ ᴰ ᴱ ᴳ ᴴ ᴵ ᴶ ᴷ ᴸ ᴹ ᴺ ᴼ ᴾ ᴿ ᵀ ᵁ ⱽ ᵂ
sup (Greek)    ᶿ                    (θ only; the rest are opt-in)
subscript      ₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉  ₊ ₋ ₌ ₍ ₎  ₐ ₑ ₕ ᵢ ⱼ ₖ ₗ ₘ ₙ ₒ ₚ ᵣ ₛ ₜ ᵤ ᵥ ₓ
```

**Do not invent or approximate a missing glyph.** A whitelist on its own is not
a membership test; these are the exact gaps that make the bare `^x` / `_x`
fallbacks in Rules 3, 4 and 5 fire. Two separate causes, same outcome.

No Unicode code point exists at all:

```
subscript letters      b c d f g q w y z    → x_b, x_c, x_d
subscript capitals     all 26               → A_B, M_N  (Unicode has no
                                              subscript capital, 0/26)
superscript capitals   X Y Z                → A^X, M^Y, A^Z
superscript ∞          none                 → never ^∞ as a glyph; use ∫[a..∞]
Greek sub/superscript  μ ν σ and most rest  → I_ν, ∂_μ, x^ν (Rules 3, 4, 8)
```

A code point exists, but no monospace font in the measured set ships it, so
treat it as absent:

```
superscript S          U+A7F1, Unicode 17.0 → A^S
superscript C F Q      U+A7F2..U+A7F4       → A^C, A^F, A^Q
superscript q          U+107A5, outside BMP → x^q
Greek subscripts       ᵦ ᵧ ᵨ ᵩ ᵪ            → x_β, I_ρ, x_γ
Greek superscripts     ᵝ ᵞ ᵟ ᵠ ᵡ            → x^β, x^φ
```

Two Greek exceptions worth knowing, because the older wording here got them
wrong. `ᶿ` (superscript θ, U+1DBF) renders as widely as the Latin blocks below
and is a normal part of the portable set, so write `xᶿ`, not `x^θ`. And `ρ` does
have a subscript, `ᵨ` U+1D68; it is missing from most terminal fonts rather than
from Unicode, which is why `I_ρ` stays the recommendation.

Measured coverage of the portable set: **17/26** lowercase subscripts, **0/26**
subscript capitals, and **19/26** superscript capitals with a code point that
some monospace font ships. The `∞` gap is why big-operator bounds use a
bracketed range rather than stacked scripts: `∫₀^∞` would render one bound as a
glyph and the other as a caret in the same operator. When unsure, the bare `^` /
`_` form is always acceptable; a wrong or missing glyph is not.

If your terminal font does carry the Greek scripts or the rarer capitals, see
`references/extended-glyphs.md` for the opt-in set.

## Font coverage

Unicode says a code point exists. Whether a terminal draws it is a property of
the font. These counts come from reading the `cmap` table of twelve monospace
fonts: the six most widely installed programming fonts (JetBrains Mono, Fira
Code, Cascadia Code, Hack, Source Code Pro, IBM Plex Mono) and six system fonts
(DejaVu Sans Mono, Liberation Mono, Ubuntu Mono, Ubuntu Sans Mono, Noto Mono,
Cousine). `scripts/measure-font-coverage.mjs` regenerates them and the test
suite asserts every number below against the result.

| what | glyphs | fonts |
|---|---|---|
| core operators and relations | ∑ ∏ ∫ √ ∂ ∞ ± × ÷ · ≈ ≠ ≤ ≥ ¬ − ² ³ | 12/12 |
| Greek letters | α β γ δ θ λ μ π σ φ ω Γ Δ Θ Λ Σ Φ Ω | 11-12/12 |
| sub/superscript digits | ⁰ ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ ₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉ | 9-12/12 |
| arrows, single | → ← ↔ ↑ ↓ | 9/12 |
| set and logic symbols | ∈ ∉ ∪ ∩ ⊂ ⊆ ∧ ∨ ∀ ∃ ∅ ∇ | 4-8/12 |
| superscript letters, lowercase | ᵃ ᵇ ᶜ ᵈ ᵉ ᶠ ᵍ ʰ ʲ ᵏ ˡ ᵐ ᵒ ᵖ ʳ ˢ ᵗ ᵘ ᵛ ʷ ˣ ʸ ᶻ | 4-5/12 |
| superscript i and n | ⁱ ⁿ | 2-7/12 |
| superscript theta | ᶿ | 4/12 |
| superscript signs and parens | ⁺ ⁻ ⁼ ⁽ ⁾ | 3-4/12 |
| subscript signs and parens | ₊ ₋ ₌ ₍ ₎ | 3-4/12 |
| superscript letters, capital | ᴬ ᴮ ᴰ ᴱ ᴳ ᴴ ᴵ ᴶ ᴷ ᴸ ᴹ ᴺ ᴼ ᴾ ᴿ ᵀ ᵁ ⱽ ᵂ | 1-3/12 |
| subscript letters, wider half | ₐ ₑ ᵢ ₒ ᵣ ᵤ ᵥ ₓ | 3/12 |
| subscript letters, thin half | ₕ ₖ ₗ ₘ ₙ ₚ ₛ ₜ ⱼ | 1/12 |
| number sets | ℕ ℤ ℚ ℝ ℂ ℙ ℍ | 3/12 |
| arrows, double | ⇒ ⇐ ⇔ ⇑ ⇓ | 4/12 |
| multiline brackets | ⎡ ⎣ ⎤ ⎦ ⎧ ⎩ ⟨ ⟩ | 4/12 |

Read that table as a ranking, not a verdict. A glyph the primary font lacks is
usually supplied by fontconfig from another installed font, so it still draws,
but at a different advance width, which is what breaks column alignment in
aligned derivations and matrices. Only a glyph no installed font carries shows
as tofu.

Two consequences worth acting on:

- The operators, Greek letters and digit scripts survive everywhere. Prefer them,
  and they carry most of the load in ordinary output.
- The letter sub/superscripts are DejaVu-class. JetBrains Mono, Fira Code, Hack
  and IBM Plex Mono ship none of them, so `xᵢ` and `xᵀ` arrive through fallback
  there. That is the reason Rules 3 and 4 keep `x_i` and `x^T` as first-class
  alternatives rather than last resorts.
- `ⱼ` and `ⱽ` are the two thinnest glyphs in the portable blocks, carried by one
  font each. They sit in the ranges above rather than in *Glyphs to avoid*
  because their fallback, `x_j` and `A^V`, is already what Rules 3 and 4 say to
  write when in doubt.

### Common LaTeX → Unicode

| LaTeX | Unicode | LaTeX | Unicode | LaTeX | Unicode |
|---|---|---|---|---|---|
| `\alpha` | α | `\sum` | ∑ | `\in` | ∈ |
| `\beta` | β | `\prod` | ∏ | `\notin` | ∉ |
| `\gamma` | γ | `\int` | ∫ | `\subset` | ⊂ |
| `\delta` | δ | `\partial` | ∂ | `\subseteq` | ⊆ |
| `\epsilon` | ε | `\nabla` | ∇ | `\cup` | ∪ |
| `\theta` | θ | `\infty` | ∞ | `\cap` | ∩ |
| `\lambda` | λ | `\emptyset` | ∅ | `\setminus` | `\` |
| `\mu` | μ | `\leq` | ≤ | `\wedge` | ∧ |
| `\pi` | π | `\geq` | ≥ | `\vee` | ∨ |
| `\sigma` | σ | `\neq` | ≠ | `\neg` | ¬ |
| `\phi` | φ | `\approx` | ≈ | `\Rightarrow` | ⇒ |
| `\omega` | ω | `\equiv` | ≡ | `\Leftrightarrow` | ⇔ |
| `\sqrt` | √ | `\propto` | ∝ | `\forall` | ∀ |
| `\pm` | ± | `\cdot` | · | `\exists` | ∃ |
| `\times` | × | `\to` | → | `\mathbb{R}` | ℝ |

## Style rules

### Rule 1 — Inline math: Unicode, no delimiters

Bad:  `The filter $f(T; m) = \{(s,r) : n_{s,r} \geq m\}$ produces the cohort.`
Good: `The filter f(T; m) = { (s,r) : n_{s,r} ≥ m } produces the cohort.`

### Rule 2 — Block math: own line(s), still no delimiters

Bad:

    $$|Q| / |T| = 5238 / 31075 \approx 16.9\%$$

Good:

    |Q| / |T|  =  5 238 / 31 075  ≈  16.9 %

### Rule 3 — Subscripts

- Single Unicode-renderable index: prefer the glyph (x₁, x₂, xᵢ, xⱼ, xₙ).
  `ⱼ` is the thinnest-supported glyph in this block, so `x_j` is equally fine.
- Single index with no subscript glyph: use a bare underscore — `I_ν`, `∂_μ`,
  and `x_c` / `x_b` / `x_d`, which have no subscript form at all. Check the
  gap list under *Sub/superscript glyph blocks* before reaching for a glyph.
- Multi-character or grouped subscript: use `_{...}` syntax — the underscore
  reads unambiguously as a subscript and stays more legible than bracket-style
  indexing:
  - `n_{s,r}` ← (s,r) has no Unicode subscript form
  - `x_max`, `σ_obs` ← multi-letter
- Never mix: don't write `x_₁` or `x_{1}` when `x₁` works.

### Rule 4 — Superscripts (powers)

- Simple / Unicode-mappable exponent: prefer the glyph — x², x³, xⁿ, eˣ, A⁻¹,
  and the transpose xᵀ / vᵀ.
- Single exponent with no glyph: use a bare caret — `x^ν`, `(z/2)^a`, and
  `A^X` / `A^Y` / `A^Z`, which have no capital superscript code point, plus
  `A^S`, which has one (U+A7F1, Unicode 17.0) that no terminal font ships.
  `Aᵀ` is fine, and so is `xᶿ`; see the gap list under *Sub/superscript glyph
  blocks*.
- Multi-character or expression exponent: use **caret + parentheses**, never
  `^{...}` — `x^(k+1)`, `x^(i)`, `e^(iπ)`. A bare `x^{T}` / `x^{(i)}` leaks
  LaTeX source; write `xᵀ` (single glyph) or `x^(i)` (parenthesized).

### Rule 5 — Big operators with selectors

Unicode operator + a **bracketed inline selector** — never `_{...}^{...}`. Use
`..` for a numeric/expression range, `∈` for set membership, `→` for a limit
target, and an equation/condition when that is the natural selector:

```
∑[i=1..n] aᵢ            ∏[k ∈ K] pₖ            ∫[a..b] f(x) dx
∫[−∞..∞] e^(−x²) dx     ⋃[i=1..n] Aᵢ           lim[x→0] f(x)
∑[m₁+...+mₙ=N] c_m      ∫[C] f(z) dz           Res[z=z₀] f(z)
```

Write a contour integral as `∫[C]`. The dedicated contour glyph is in no
monospace font measured here, and the bracketed selector already says the path
is C. See *Glyphs to avoid*.

Use ordinary letters for named functions: `Γ`, `B`, `erf`, `det`, `tr`, `Re`,
`Im`, `exp`, `log`, `sin`, `cos`, `argmin`. Do not emit `\operatorname`.
For a left-scripted named function, use available glyphs such as `₂F₁(a,b;c;z)`;
when an index cannot be expressed as one glyph, use readable ASCII notation such
as `_{p}F_q` rather than inventing a substitute.

### Rule 6 — Fractions

- Inline: `a/b`, `(a + b) / (c + d)`
- Block (only when it aids clarity):

```
       a + b
   ─────────────
     c² + d²
```

### Rule 7 — Matrices / vectors

ASCII art with corner glyphs:

```
A  =  ⎡ a  b ⎤        v  =  ( v₁ , v₂ , v₃ )ᵀ
      ⎣ c  d ⎦
```

Declare variable types in prose instead of faking bold or italic: “Here z and n
are vectors, and Ω is a matrix.”

### Rule 8 — Tensor indices

Tensor indices are indices, not powers. Keep non-mappable tensor indices in
bare ASCII form and group only when the index has multiple characters:

```
R^ρ_{σμν}        ∂_μ        Γ^ρ_{νσ}
```

### Rule 9 — Piecewise forms and aligned derivations

Use the box-drawing brace glyphs for a short piecewise definition; keep equals
signs in the same column for a derivation. If those brace glyphs are absent in a
reader's font, use a semicolon-separated sentence instead.

```
f(x) =
  ⎧ x²    if x ≥ 0
  ⎩ −x    if x < 0

aₙ = bₙ + cₙ
    = dₙ
```

### Rule 10 — Sets and conditions

Prefer set-builder with `|` or `:`:

```
Q  =  { (s,r) ∈ T  :  n_{s,r} ≥ 18  ∧  p⁰_{s,r} < 0.9 }
```

### Rule 11 — Numbers

- Thousands: thin space (` `, U+2009) — `5 238`, `34 601` — not commas (locale ambiguous).
- Decimal: dot — `16.9 %`.
- Percent: space before `%` — `16.9 %` (typographic convention; readable).
- Approximations: ≈, ∼. Order of magnitude: ~. Confidence: `x = 5.2 ± 0.3`.

### Rule 12 — When Unicode hurts, fall back explicitly

If a glyph chain becomes denser than the LaTeX it replaces, switch to readable ASCII pseudo-LaTeX and annotate it. Example:

```
H(p) = − ∑[x ∈ X] p(x) · log p(x)        (∑ = sum over the support X)
```

The reader's comprehension is the only metric. Prefer common, well-supported
glyphs. Do not use combining marks or obscure modifier letters just to force a
super- or subscript; use readable bare `^x` / `_x` notation instead. Choose
whichever form is clearest, then stay consistent within a passage.

### Rule 13 — Plain letters for variables; never style with math-alphanumeric codepoints

Write variable names and identifiers with ordinary letters (x, A, Var, RSS). Do **not** reach into the Unicode *Mathematical Alphanumeric Symbols* block (U+1D400 onward: bold, italic, script and styled double-struck letters) to *style* ordinary letters. Those code points garble on copy/paste, terminal search, and screen readers — the same failure Claude Code hit in issue #61558. They are also the least renderable characters in the block table: see *Glyphs to avoid*.

Exception: the standard blackboard-bold number sets are correct notation rather than styling, and they live in the Letterlike Symbols block, which terminal fonts do carry. Keep using ℕ ℤ ℚ ℝ ℂ ℙ ℍ.

The exception stops there. Double-struck F and double-struck E sit in the Mathematical Alphanumeric Symbols block this rule bans, and they measure worse than anything else the skill emitted before: one monospace font out of twelve. Write a general field as `F` and an expectation as `E[X]`. Everything the rule says about copy, search and screen readers applies to them too.

## Quick reference — common forms

```
Mean / std        μ ± σ                        x̄ ± s
Probability       P(A | B)                     ℙ(A ∩ B) = ℙ(A) · ℙ(B | A)
Expectation       E[X] = ∫ x · f(x) dx
Variance          Var(X) = E[X²] − E[X]²
Gradient          ∇f = ( ∂f/∂x₁ , ... , ∂f/∂xₙ )
Norm              ‖x‖₂ = √(∑[i=1..n] xᵢ²)
Big-O             T(n) = O(n log n)
Limit             lim[n → ∞] aₙ = L
Sum bounds        ∑[i=1..n] i  =  n(n+1)/2
Quantile          q_α = inf{ x : F(x) ≥ α }
```

## Golden corpus — difficult terminal-native forms

These examples are deliberately chosen to exercise non-mappable indices,
constrained sums, tensors, special functions, contours, and multiline output.
They are normalized terminal forms of standard formulas (including DLMF
§10.32.E2, §15.6.E1, §19.19.E1, and §21.2.E1).

```
I_ν(z) = (z/2)^ν / (√π Γ(ν+½)) ∫[0..π] e^(±z cos θ)(sin θ)^(2ν) dθ

F(a,b;c;z) = 1 / (Γ(b)Γ(c−b)) ∫[0..1] t^(b−1)(1−t)^(c−b−1) / (1−zt)^a dt

T_N(b,z) = ∑[m₁+...+mₙ=N] ((b₁)_{m₁} ··· (bₙ)_{mₙ}) / (m₁! ··· mₙ!) · z₁^(m₁) ··· zₙ^(mₙ)

θ(z | Ω) = ∑[n ∈ ℤ^g] exp(2π i(½ n · Ω · n + n · z))
  Here z and n are vectors, and Ω is a matrix.

R^ρ_{σμν} = ∂_μ Γ^ρ_{νσ} − ∂_ν Γ^ρ_{μσ} + Γ^ρ_{μλ} Γ^λ_{νσ} − Γ^ρ_{νλ} Γ^λ_{μσ}

f^(n)(z₀) = n! / (2π i) ∫[C] f(z) / (z−z₀)^(n+1) dz

∂u/∂t + (u · ∇)u = −∇p + νΔu + f,  ∇·u = 0

p(x) = exp(−½ (x−μ)ᵀΣ⁻¹(x−μ)) / √((2π)ᵈ det Σ)

F(ω) = ∫[−∞..∞] f(t)e^(−iωt) dt

f(x) =
  ⎧ x²    if x ≥ 0
  ⎩ −x    if x < 0
```

## Glyphs to avoid

Every glyph below has a code point and looks correct in a proportional editor.
None of them is carried by more than one of the twelve monospace fonts measured
in *Font coverage*, so in a terminal each one either draws from a fallback at the
wrong width or shows as tofu. Write the replacement instead. Counts are
`fonts carrying the glyph / fonts measured`.

| avoid | code point | fonts | write instead |
|---|---|---|---|
| ∮ | U+222E | 0/12 | `∫[C] f(z) dz` |
| ⅆ | U+2146 | 0/12 | `d` |
| ⅇ | U+2147 | 0/12 | `e` |
| ∖ | U+2216 | 0/12 | `A \ B` |
| ℵ | U+2135 | 0/12 | `aleph_0` |
| ℶ | U+2136 | 0/12 | `beth_0` |
| ⋘ | U+22D8 | 0/12 | `<<` |
| ⋙ | U+22D9 | 0/12 | `>>` |
| ⨁ | U+2A01 | 0/12 | `⊕[i=1..n]` |
| ⨂ | U+2A02 | 0/12 | `⊗[i=1..n]` |
| 〈 | U+3008 | 0/12 | `⟨` (U+3008 is a full-width CJK bracket) |
| 〉 | U+3009 | 0/12 | `⟩` |
| ≪ | U+226A | 1/12 | `<<` |
| ≫ | U+226B | 1/12 | `>>` |
| ⊨ | U+22A8 | 1/12 | `\|=` |
| ⊻ | U+22BB | 1/12 | `xor`, or `⊕` in a boolean-ring context |
| ⊼ | U+22BC | 1/12 | `nand` |
| ⊽ | U+22BD | 1/12 | `nor` |
| ⟸ | U+27F8 | 1/12 | `⇐` |
| ⟹ | U+27F9 | 1/12 | `⇒` |
| ⟺ | U+27FA | 1/12 | `⇔` |
| ⨅ | U+2A05 | 1/12 | `⊓[i=1..n]` |
| ⨆ | U+2A06 | 1/12 | `⊔[i=1..n]` |
| 𝔼 | U+1D53C | 1/12 | `E[X]` (also banned by Rule 13) |
| 𝔽 | U+1D53D | 1/12 | `F` (also banned by Rule 13) |
| 𝔸 | U+1D538 | 1/12 | `A`, or `ℕ ℤ ℚ ℝ ℂ` when a specific set is meant |

## Anti-patterns — never emit these in the terminal (Claude Code / Codex)

```
✗   $f(x) = \sum_{i=1}^{n} x_i$
✗   \( a^2 + b^2 = c^2 \)
✗   $$\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$$
✗   \[ |Q|/|T| \approx 16.9\% \]
✗   ∑_{i=1}^{n}  or  ∫_a^b  or  x^{T}   (stacked bounds / brace exponent leak source even without $…$ — write ∑[i=1..n], ∫[a..b], xᵀ)
✗   Let 𝑉𝑎𝑟 = …   or   matrix 𝐀 = …   (math-alphanumeric styling; garbles on copy/search — write Var, A)
```

If asked to produce raw LaTeX (e.g. for a `.tex` file or a KaTeX-rendering tool downstream), do so — and call it out explicitly: *"Raw LaTeX as requested; this will not render in the terminal."*
