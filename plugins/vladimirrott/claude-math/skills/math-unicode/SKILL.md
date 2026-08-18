---
name: math-unicode
description: This skill must be used whenever a response needs mathematical notation — equations, filters, set-builder notation, statistics, calculus, linear algebra, logic, ratios, drops, or counts. Load it before composing, including when the user explicitly mentions math-unicode. Emit terminal-native Unicode inline, never raw LaTeX delimiters or commands.
disable-model-invocation: false
---

# math-unicode

When emitting mathematical notation in a terminal coding agent (Claude Code, Codex CLI, or similar), **always use Unicode glyphs inline** — never wrap math in `$…$`, `\(...\)`, or `$$...$$`. These terminals do not render LaTeX; raw delimiters appear as plain dollar signs and reduce readability.

## When this skill applies

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
big            ∑ ∏ ∐ ∫ ∮ ∬ ∭ ⨁ ⨂ ⨅ ⨆
roots          √ ∛ ∜
calculus       ∂ ∇ Δ ∆ ⅆ ⅇ
constants      ∞ ∅ ℵ ℶ
```

### Relations

```
equality       =  ≠  ≈  ≅  ≡  ≜  ≝  ≐  ∝  ∼  ≃  ≢
order          <  >  ≤  ≥  ≪  ≫  ⋘  ⋙  ⊴  ⊵
set            ∈ ∉ ∋ ∌  ⊂ ⊃ ⊆ ⊇ ⊊ ⊋  ⊏ ⊐ ⊑ ⊒
set ops        ∪ ∩ ⊎ ⊔ ⊓ ∖
```

### Logic & arrows

```
logic          ∧ ∨ ¬ ⊕ ⊻ ⊼ ⊽   ⊢ ⊨ ⊥ ⊤
quantifiers    ∀ ∃ ∄ ∴ ∵
arrows         → ← ↔ ⇒ ⇐ ⇔ ↦ ↪ ↩ ↑ ↓ ⇑ ⇓ ⟶ ⟵ ⟷ ⟹ ⟸ ⟺ ⊸
```

### Number sets & brackets

```
sets           ℕ ℤ ℚ ℝ ℂ ℙ ℍ 𝔽
brackets       ⟨ ⟩  ⌈ ⌉  ⌊ ⌋  ‖ ‖  〈 〉
```

### Sub/superscript glyph blocks

```
superscript    ⁰ ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹  ⁺ ⁻ ⁼ ⁽ ⁾  ⁱ ⁿ ᵃ ᵇ ᶜ ᵈ ᵉ ᶠ ᵍ ʰ ʲ ᵏ ˡ ᵐ ᵒ ᵖ ʳ ˢ ᵗ ᵘ ᵛ ʷ ˣ ʸ ᶻ
sup (capital)  ᴬ ᴮ ᴰ ᴱ ᴳ ᴴ ᴵ ᴶ ᴷ ᴸ ᴹ ᴺ ᴼ ᴾ ᴿ ᵀ ᵁ ⱽ ᵂ
subscript      ₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉  ₊ ₋ ₌ ₍ ₎  ₐ ₑ ₕ ᵢ ⱼ ₖ ₗ ₘ ₙ ₒ ₚ ᵣ ₛ ₜ ᵤ ᵥ ₓ
```

**No glyph exists for these. Do not invent or approximate one.** A whitelist on
its own is not a membership test; these are the exact gaps that make the bare
`^x` / `_x` fallbacks in Rules 3, 4 and 5 fire:

```
subscript letters      b c d f g q w y z    → bare underscore: x_b, x_c, x_d
superscript capitals   S X Y Z              → bare caret: A^S, A^X, M^Y
superscript C F Q      U+A7F2–A7F4 only     → treat as absent (most fonts show tofu)
superscript ∞          does not exist       → never ^∞ as a glyph; use ∫[a..∞] (Rule 5)
Greek sub/superscript  ν μ ρ θ σ ...        → bare form: I_ν, ∂_μ, x^ν (Rules 3, 4, 8)
```

Measured coverage: **17/26** lowercase subscripts and **19/26** superscript
capitals. The `∞` gap is why big-operator bounds use a bracketed range rather
than stacked scripts: `∫₀^∞` would render one bound as a glyph and the other as
a caret in the same operator. When unsure, the bare `^` / `_` form is always
acceptable; a wrong or missing glyph is not.

### Common LaTeX → Unicode

| LaTeX | Unicode | LaTeX | Unicode | LaTeX | Unicode |
|---|---|---|---|---|---|
| `\alpha` | α | `\sum` | ∑ | `\in` | ∈ |
| `\beta` | β | `\prod` | ∏ | `\notin` | ∉ |
| `\gamma` | γ | `\int` | ∫ | `\subset` | ⊂ |
| `\delta` | δ | `\partial` | ∂ | `\subseteq` | ⊆ |
| `\epsilon` | ε | `\nabla` | ∇ | `\cup` | ∪ |
| `\theta` | θ | `\infty` | ∞ | `\cap` | ∩ |
| `\lambda` | λ | `\emptyset` | ∅ | `\setminus` | ∖ |
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
  `A^S` / `A^X` / `A^Y` / `A^Z`, which have no capital superscript form.
  `Aᵀ` is fine; see the gap list under *Sub/superscript glyph blocks*.
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
∑[m₁+...+mₙ=N] c_m      ∮[C] f(z) dz           Res[z=z₀] f(z)
```

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

Write variable names and identifiers with ordinary letters (x, A, Var, RSS). Do **not** reach into the Unicode *Mathematical Alphanumeric Symbols* block (𝐀 bold, 𝐴 italic, 𝓐 script, 𝔸 styled double-struck) to *style* ordinary letters. Those codepoints garble on copy/paste, terminal search, and screen readers — the same failure Claude Code hit in issue #61558.

Exception: the standard, semantically meaningful blackboard-bold sets and operators are correct notation, not styling — keep using ℕ ℤ ℚ ℝ ℂ ℙ 𝔽 (number sets) and 𝔼 (expectation). Use those; don't hand-style anything else.

## Quick reference — common forms

```
Mean / std        μ ± σ                        x̄ ± s
Probability       P(A | B)                     ℙ(A ∩ B) = ℙ(A) · ℙ(B | A)
Expectation       𝔼[X] = ∫ x · f(x) dx
Variance          Var(X) = 𝔼[X²] − 𝔼[X]²
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

f^(n)(z₀) = n! / (2π i) ∮[C] f(z) / (z−z₀)^(n+1) dz

∂u/∂t + (u · ∇)u = −∇p + νΔu + f,  ∇·u = 0

p(x) = exp(−½ (x−μ)ᵀΣ⁻¹(x−μ)) / √((2π)ᵈ det Σ)

F(ω) = ∫[−∞..∞] f(t)e^(−iωt) dt

f(x) =
  ⎧ x²    if x ≥ 0
  ⎩ −x    if x < 0
```

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
