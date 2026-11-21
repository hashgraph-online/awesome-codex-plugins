# Message Digest Template

This template defines the exact output format for `message_{DATE}.md`.

---

## Language-Specific Text

### Headers

| `--lang` | Header Line 1 | Header Line 2 |
|----------|---------------|----------------|
| `zh` | `MorningAI {YYYY-MM-DD}` | `共 {N} 条重要更新` |
| `en` | `MorningAI {YYYY-MM-DD}` | `{N} notable updates today` |
| `ja` | `MorningAI {YYYY-MM-DD}` | `本日の注目 {N} 件` |

### Footer

| `--lang` | Footer |
|----------|--------|
| `zh` | `Powered by MorningAI \| 完整报告: report_{DATE}.md` |
| `en` | `Powered by MorningAI \| Full report: report_{DATE}.md` |
| `ja` | `Powered by MorningAI \| 完全レポート: report_{DATE}.md` |

---

## Template Structure

```
{Header Line 1}

{Header Line 2}

{Item 1}

{Item 2}

...

{Item N}

---
{Footer}
```

---

## Item Template

### Standard Item

```
{emoji} **{Entity} {Event Description}**
{1-2 sentence summary with key metrics and specifics.}
🔗 {source_url}
```

**Emoji selection:**
- Score 9-10 → `🔥`
- Score 7-8 → `⭐`
- Score 5-6 → `🔷`

**Title rules:**
- Bold the entire title
- Include entity name + concise event description
- Keep titles under 30 characters (Chinese) or 60 characters (English) when possible
- Do NOT include score numbers

**Summary rules:**
- Condense to 1-2 sentences maximum
- Include the most important specific details: numbers, versions, benchmarks, pricing
- No filler phrases like "major update" without specifics
- End with a period

**Link rules:**
- **EVERY item MUST end with a `🔗 {source_url}` line — NO EXCEPTIONS**
- An item without a source link is a critical formatting error and must not appear in the output
- The URL comes from the item's `source_url` field
- If `source_url` is empty, construct the URL from known patterns:
  - HuggingFace models → `https://huggingface.co/{model_id}`
  - GitHub repos → `https://github.com/{owner}/{repo}`
  - arXiv papers → `https://arxiv.org/abs/{paper_id}`
  - Otherwise → search for the official announcement URL
- If no URL can be found → **drop the item entirely** rather than including it without a link
- Always use the full URL, do NOT shorten or omit

### GitHub Trending Item (Special)

When an item is from GitHub Trending or has notable star/fork metrics:

```
🔥 **GitHub Trending: {repo-name} (Stars Surging!)**
⭐ {star_count}(+{delta}) | {one-line description}
🔗 {source_url}
```

---

## Link Placement

### Inline Format (`MESSAGE_LINKS=inline`, default)

Each item ends with a source link — this is the standard format:

```
{emoji} **{Entity} {Event Description}**
{Summary sentence.}
🔗 {source_url}
```

### Bottom Format (`MESSAGE_LINKS=bottom`, alternative)

When set to `bottom`, omit `🔗` lines from items and group links as a reference list at the end:

```
---
[1] {Entity Event Short Label} - {source_url}
[2] {Entity Event Short Label} - {source_url}
...
```

- One link per item, in the same order as items appear
- Short label: `{Entity} {Event}` (e.g., "Anthropic Claude 4.5 Sonnet")
- Full URL from `source_url` field

---

## Complete Example

```
MorningAI 2026-04-14

8 notable updates today

🔥 **Anthropic Releases Claude 4.5 Sonnet**
New mid-tier model with +18% SWE-Bench, 200K context, 40% faster output. Available via API and claude.ai.
🔗 https://x.com/AnthropicAI/status/example

⭐ **Google Gemini 2.5 Flash Enters Public Preview**
Flash-tier model with native multimodal reasoning, 1M context. Free tier on AI Studio.
🔗 https://x.com/GoogleDeepMind/status/example

⭐ **Cursor Background Agents Now Generally Available**
Autonomous background agents for multi-file refactoring, test generation, and PR creation. Max 10 concurrent on Pro.
🔗 https://cursor.com/changelog/background-agents-ga

⭐ **DeepSeek Open-Sources V3-0407 Model**
Updated V3 with 671B MoE architecture, MIT license. Weights available on HuggingFace.
🔗 https://github.com/deepseek-ai/DeepSeek-V3

⭐ **OpenAI Open-Sources Codex CLI**
Terminal-based coding agent with suggest, auto-edit, and full-auto modes. MIT license.
🔗 https://github.com/openai/codex

⭐ **LMSYS Chatbot Arena April Rankings Update**
Claude 4.5 Sonnet enters #2 overall (ELO 1287). Gemini 2.5 Pro holds #1 in coding.
🔗 https://lmarena.ai

⭐ **GitHub Copilot Coding Agent Public Preview**
Autonomous agent handles issues and creates PRs in secure cloud sandbox. Free for Pro+ and Enterprise.
🔗 https://github.blog/changelog/copilot-coding-agent

⭐ **Windsurf Raises $200M Series C at $3B Valuation**
Largest round in AI coding tools space. Plans to hire 200 engineers and expand enterprise features.
🔗 https://techcrunch.com/2026/04/07/windsurf-raises-200m

---
Powered by MorningAI | Full report: report_2026-04-14.md
```
