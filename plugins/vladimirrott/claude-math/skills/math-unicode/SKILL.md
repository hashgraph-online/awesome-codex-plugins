---
name: math-unicode
description: Use whenever you need to express mathematical notation — equations, filters, set-builder, statistics, calculus, logic, ratios, drops, counts. Emit Unicode math glyphs INLINE; never wrap in `$…$`, `\(...\)`, or `$$...$$`. Claude Code terminal does not render LaTeX, so raw delimiters appear as noise. This skill activates automatically when math is involved.
---

# math-unicode

When emitting mathematical notation in Claude Code, **always use Unicode glyphs inline** — never wrap math in `$…$`, `\(...\)`, or `$$...$$`. Claude Code's terminal does not render LaTeX; raw delimiters appear as plain dollar signs and reduce readability.

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
subscript      ₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉  ₊ ₋ ₌ ₍ ₎  ₐ ₑ ₕ ᵢ ⱼ ₖ ₗ ₘ ₙ ₒ ₚ ᵣ ₛ ₜ ᵤ ᵥ ₓ
```

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

    |Q| / |T|  =  5 238 / 31 075  ≈  16.9 %

### Rule 3 — Subscripts

- Single Unicode-renderable index: prefer the glyph (x₁, x₂, xᵢ, xⱼ)
- Multi-character or non-mappable subscript: keep `_{...}` syntax for clarity
  - `n_{s,r}` ← (s,r) has no Unicode subscript form
  - `x_max`, `σ_obs` ← multi-letter
- Never mix: don't write `x_₁` or `x_{1}` when `x₁` works.

### Rule 4 — Superscripts (powers)

- Integer powers, simple: x², x³, xⁿ, e^x → eˣ
- Multi-character / non-mappable: `x^{T}`, `x^{(i)}`, `A^{-1}` (or A⁻¹ if the exponent is simple)

### Rule 5 — Big operators with indices

Use Unicode operator + ASCII bounds:

```
∑_{i=1}^{n} aᵢ
∏_{k ∈ K} pₖ
∫_a^b f(x) dx
```

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

### Rule 8 — Sets and conditions

Prefer set-builder with `|` or `:`:

```
Q  =  { (s,r) ∈ T  :  n_{s,r} ≥ 18  ∧  p⁰_{s,r} < 0.9 }
```

### Rule 9 — Numbers

- Thousands: thin space (` `) — `5 238`, `34 601` — not commas (locale ambiguous).
- Decimal: dot — `16.9 %`.
- Percent: space before `%` — `16.9 %` (typographic convention; readable).
- Approximations: ≈, ∼. Order of magnitude: ~. Confidence: `x = 5.2 ± 0.3`.

### Rule 10 — When Unicode hurts, fall back explicitly

If a glyph chain becomes denser than the LaTeX it replaces, switch to readable ASCII pseudo-LaTeX and annotate it. Example:

```
H(p) = − Σ_{x ∈ X} p(x) · log p(x)        (Σ = sum over the support X)
```

The reader's comprehension is the only metric. Choose whichever form is clearest, then stay consistent within a passage.

### Rule 11 — Plain letters for variables; never style with math-alphanumeric codepoints

Write variable names and identifiers with ordinary letters (x, A, Var, RSS). Do **not** reach into the Unicode *Mathematical Alphanumeric Symbols* block (𝐀 bold, 𝐴 italic, 𝓐 script, 𝔸 styled double-struck) to *style* ordinary letters. Those codepoints garble on copy/paste, terminal search, and screen readers — the same failure Claude Code hit in issue #61558.

Exception: the standard, semantically meaningful blackboard-bold sets and operators are correct notation, not styling — keep using ℕ ℤ ℚ ℝ ℂ ℙ 𝔽 (number sets) and 𝔼 (expectation). Use those; don't hand-style anything else.

## Quick reference — common forms

```
Mean / std        μ ± σ                        x̄ ± s
Probability       P(A | B)                     ℙ(A ∩ B) = ℙ(A) · ℙ(B | A)
Expectation       𝔼[X] = ∫ x · f(x) dx
Variance          Var(X) = 𝔼[X²] − 𝔼[X]²
Gradient          ∇f = ( ∂f/∂x₁ , ... , ∂f/∂xₙ )
Norm              ‖x‖₂ = √(Σᵢ xᵢ²)
Big-O             T(n) = O(n log n)
Limit             lim_{n → ∞} aₙ = L
Sum bounds        ∑_{i=1}^{n} i  =  n(n+1)/2
Quantile          q_α = inf{ x : F(x) ≥ α }
```

## Anti-patterns — never emit these in Claude Code terminal

```
✗   $f(x) = \sum_{i=1}^{n} x_i$
✗   \( a^2 + b^2 = c^2 \)
✗   $$\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$$
✗   \[ |Q|/|T| \approx 16.9\% \]
✗   Let 𝑉𝑎𝑟 = …   or   matrix 𝐀 = …   (math-alphanumeric styling; garbles on copy/search — write Var, A)
```

If asked to produce raw LaTeX (e.g. for a `.tex` file or a KaTeX-rendering tool downstream), do so — and call it out explicitly: *"Raw LaTeX as requested; this will not render in the terminal."*
