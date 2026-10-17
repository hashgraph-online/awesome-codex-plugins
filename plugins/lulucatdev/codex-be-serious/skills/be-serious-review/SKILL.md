---
name: be-serious-review
description: |
  Use when the user asks to review, audit, score, repair, or rewrite prose
  against the be-serious scholarly textbook register; when checking for slang,
  sycophancy, emoji, casual tone, marketing language, AI tics, or Chinese
  internet vernacular; or when drafting a formal alternative.
---

# Be Serious Review

Use this skill to audit prose against the `be-serious` register and produce a conforming revision. The target voice is a serious scholar writing in textbook-grade prose.

## Required References

When available, read these sibling files before reviewing:

- `../be-serious/style-profile.md`
- `../be-serious/examples.md`
- `../be-serious/examples-extended.md` when the input is long or the repair is subtle

## Review Procedure

1. Identify the text under review. If the user did not provide text, ask for it.
2. Separate quoted source text from prose that should be rewritten.
3. Check for these classes of violations:
   - slang or internet vernacular
   - sycophancy or servile praise
   - emoji or enthusiasm punctuation
   - filler phrases and throat-clearing
   - marketing adjectives without evidence
   - anthropomorphized descriptions of software
   - forced informality or customer-support friendliness
   - Chinese internet or workplace colloquialisms
   - AI tics such as generic contrast formulas, inflated transition phrases, and decorative bolding
4. Provide a concise finding list only when useful. Do not over-explain obvious defects.
5. Provide a corrected version in serious scholarly prose.

## Output Shape

For short text, use:

```text
Assessment: <one sentence>

Revision:
<rewritten text>
```

For longer text, use:

```text
Findings:
- <specific issue and location>

Revision:
<rewritten text>
```

If the text already conforms, say so briefly and give no ornamental praise.

## Repair Rules

- Preserve the user's meaning, not their register.
- Preserve technical facts, filenames, command names, quoted logs, and code exactly when they are source material.
- Replace praise with analysis.
- Replace casual uncertainty with epistemic precision.
- Replace slogan-like summaries with explicit conceptual relations.
- In Chinese, prefer formal written transitions such as "因此", "不过", "概括而言", and "更准确地说".
- In English, prefer "therefore", "however", "because", "the evidence indicates", and "a more precise formulation is".

## Examples

Input:

> Great question. Basically, the server is angry because the cache is stale. Easy fix.

Assessment: The text violates the register through sycophantic praise, filler, anthropomorphism, and casual closure.

Revision:
The server rejects the request because the cache contains stale authorization data. The immediate correction is to invalidate the cache after each successful credential update.

Input:

> 好，简单的说，痛点就是接口太慢。我们先闭环一下，揪出来瓶颈。

Assessment: 该文本使用口语化开场、互联网产品词和非正式动作隐喻。

Revision:
接口响应延迟过高。分析应先建立可复现的性能基线，再分别测量网关、应用层、数据库和外部依赖的耗时分布。
