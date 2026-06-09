# Distill — Theoretical Foundations

The `/distill` skill applies information theory, NLP research, and classical writing principles to semantic text compression.

## 1. Shannon's Information Theory (1948)

**Source:** Claude Shannon, [*A Mathematical Theory of Communication*](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf), Bell System Technical Journal, 1948.

Shannon defines **entropy** H(X):

```
H(X) = -Σ p(xᵢ) · log₂ p(xᵢ)
```

The **Source Coding Theorem**: a source cannot be compressed below its entropy without loss. Everything above entropy is eliminable redundancy.

In 1951 ([*Prediction and Entropy of Printed English*](https://www.princeton.edu/~wbialek/rome/refs/shannon_51.pdf)), Shannon estimated English at ~1.0–1.5 bits/character out of ~4.7 bits/char maximum — ~70–80% structural redundancy. Modern LLMs lower this to ~0.7–0.8 bits/character.

**Application:** Shannon entropy is the compression floor. gzip (LZ77 + Huffman) approximates entropy from above. If gzip size drops after distillation, real redundancy was removed.

## 2. Verbosity Compensation in LLMs (Sun et al., 2025)

**Source:** Jie Sun et al., [*Verbosity ≠ Veracity*](https://arxiv.org/abs/2411.07858), UncertaiNLP Workshop, ACL 2025.

**Verbosity Compensation (VC):** LLMs, when uncertain, produce more words — analogous to human hesitation.

### Five VC categories

| Type | Description | Example |
|------|-------------|---------|
| Ambiguity | Vague instead of precise | "It's quite large" vs "3,029 entries" |
| Question repetition | Restates question before answering | Paraphrases without answering |
| Enumeration | Lists all possibilities instead of selecting | "Could be A, B, C, D" when answer is B |
| Verbose details | Excessive context around a simple fact | 3 paragraphs for a one-line answer |
| Verbose format | Unnecessary formatting | Excessive markdown, emphasis on non-key terms |

### Findings

- GPT-4 exhibits VC in **50.4%** of responses (range: 13.6% Llama-3-70B to 74% Mistral-7B)
- Verbose responses are **27.6% less accurate**
- Higher uncertainty → higher verbosity
- Gap does **not diminish** with more capable models — structural, tied to RLHF training

**Application:** All five categories map to the skill's noise taxonomy. Verbosity correlating with lower accuracy justifies aggressive removal.

## 3. LLM Slop Taxonomy

**Sources:**
- [TinyComputers.io — *What Makes Something Slop*](https://tinycomputers.io/posts/llm-generated-content-what-makes-something-slop.html)
- [AI Phrase Finder](https://aiphrasefinder.com/words-that-identify-ai/)
- [Embryo — Words AI Overuses](https://embryo.com/blog/list-words-ai-overuses/)
- [Slop Radar](https://github.com/renefichtmueller/slop-radar) — 245 English buzzwords + pattern matching

Core mechanism: slop is "grammatically flawless and semantically empty." The **commitment problem** — refusing to make falsifiable claims through relentless qualification.

### The 10 noise categories

1. **Hedging** — "It's important to note", "It's worth mentioning"
2. **Empty transitions** — "Moreover", "Furthermore", "Additionally"
3. **Empty conclusions** — "In summary", "In conclusion"
4. **Filler openers** — "Certainly!", "Great question!"
5. **Buzzword inflation** — delve, tapestry, landscape, leverage, paradigm, holistic, synergy
6. **Verbose constructions** — "in order to" → "to", "due to the fact that" → "because"
7. **Structural padding** — unnecessary headers, rigid essay format, decorative formatting
8. **Non-committal language** — "X can be Y" when "X is Y", excessive hedging
9. **Repetition** — same idea in different words, echo sentences
10. **Verbosity compensation** — the five academic categories from Sun et al.

## 4. High-Entropy Writing (Miessler, 2024)

**Source:** Daniel Miessler, [*High-Entropy Writing*](https://danielmiessler.com/blog/high-entropy-writing), 2024. Creator of [Fabric](https://github.com/danielmiessler/Fabric) (140k+ stars).

High-entropy content **surprises** the reader. If every sentence is predictable, the text adds nothing. For every piece of content: *"What's surprising here?"* If nothing — cut it.

**Exception:** Frameworks combining known elements into novel, useful structures qualify through elegance and usability.

**Application:** Quality test: "Would a knowledgeable reader learn something from this paragraph?" If not, it's zero-entropy filler.

## 5. Orwell's Writing Rules (1946)

**Source:** George Orwell, *Politics and the English Language*, 1946.

1. Never use a clichéd metaphor or figure of speech
2. Never use a long word where a short one will do
3. If it is possible to cut a word, cut it
4. Never use passive where active works
5. Never use jargon if an everyday equivalent exists
6. Break any rule sooner than say anything barbarous

**Application:** Rules 1–4 are directly implemented. Rule 1 is especially relevant for LLM text (models produce "tapestry", "landscape", "delve into" at scale). Rule 6 is the safety constraint.

## 6. Strunk & White — The Elements of Style (1918/1959)

**Source:** William Strunk Jr., *The Elements of Style*, 1918. Revised by E.B. White, 1959.

> "Vigorous writing is concise. A sentence should contain no unnecessary words, a paragraph no unnecessary sentences."

Key rules: omit needless words, use definite/specific/concrete language, put statements in positive form, use nouns and verbs (they carry information; adjectives often dilute).

**Application:** Informs the verbose constructions list (20+ substitutions) and the preference for concrete over abstract words.

## 7. Factual Density (Horn & Zhila, 2013)

**Source:** Christian Horn and Alisa Zhila, [*Using Factual Density to Measure Informativeness*](https://aclanthology.org/W13-5621.pdf), ACL Workshop, 2013.

```
FD = number_of_extracted_facts / number_of_words
```

Uses OIE to extract (subject, relation, object) triples, then calculates facts per word. Validated with 13 annotators (Spearman ρ = 0.41, p < 0.01).

**Application:** "Maximize facts-per-word." Distillation increases FD by shrinking words while keeping facts constant. Self-check verifies fact count preservation.

## 8. Plain Language (ISO 24495, 2023)

**Sources:**
- [ISO 24495-1:2023](https://www.iso.org/standard/78907.html)
- [US National Archives — Plain Language Principles](https://www.archives.gov/open/plain-writing/10-principles.html)

Plain language: communication whose "wording, structure, and design are so clear that the intended audience can easily find what they need, understand what they find, and use that information."

Principles: main point first, short sentences (under 20-25 words), one idea per paragraph, active voice, common words, structure that aids scanning.

**Application:** Balances compression against readability. The `<hard-gate>` "NEVER make the text telegraphic" enforces this.

## 9. Claude 4.6 Prompting Best Practices

**Sources:**
- [Anthropic — Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Anthropic — Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [obra/superpowers](https://github.com/obra/superpowers) — agentic skills framework

| Technique | Why | Source |
|-----------|-----|--------|
| Role assignment (`<role>`) | Focuses behavior and tone | Anthropic docs |
| XML tags | Unambiguous parsing | Anthropic docs |
| 3 before/after examples | Most reliable way to steer output | Anthropic docs |
| Motivation/WHY (`<why-this-matters>`) | Generalizes from explanations | Anthropic docs |
| Positive framing | Tell what to do, not what not to | Anthropic docs |
| Self-verification loop | Verify against criteria before finishing | Anthropic docs |
| `<hard-gate>` | Prevents rationalization of exceptions | superpowers |
| Dense prompt style | Prompt format influences output | Anthropic docs |
| Reference files | Be literal, don't assume inference | Anthropic skill docs |
| SKILL.md under 500 lines | Optimal context performance | Anthropic skill docs |
| Feedback loop | Generate → review → refine | Anthropic docs |

## 10. Why gzip

gzip compression ratio is the primary entropy proxy. The Source Coding Theorem guarantees lossless compression output is an upper bound on entropy.

gzip (LZ77 + Huffman) captures: exact string repetitions (redundancy) and non-uniform character distributions (statistical redundancy).

If gzip size drops after distillation, real structural redundancy was removed. Word count alone doesn't distinguish meaningful words from filler.

## How the Pieces Fit

```
Shannon (theory)           → Compression floor; above it is eliminable
    ↓
Sun et al. (diagnosis)     → LLMs produce ~50% VC; verbose = less accurate
    ↓
Slop taxonomy (symptoms)   → 10 categories of recognizable noise
    ↓
Orwell + Strunk (therapy)  → Mechanical rules for sentence-level compression
    ↓
Miessler (quality gate)    → Every sentence must surprise; zero surprise = cut
    ↓
Plain Language (constraint) → Result must stay readable, not telegraphic
    ↓
Claude 4.6 patterns (impl) → XML tags, examples, self-check, hard-gates
    ↓
gzip + word count (measure) → Objective verification of real compression
```
