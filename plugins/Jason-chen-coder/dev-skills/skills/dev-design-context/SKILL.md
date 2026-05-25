---
name: dev-design-context
description: 'Use as a one-time design setup for UI, product, landing-page, or brand-heavy work. Scans the project for design context, asks only the UX questions that cannot be inferred, then writes persistent design guidelines to .design-context.md. Does not implement features or review code.'
---

# Dev Design Context

Gather design context for this project, then persist it so future UI work starts with the same visual and product direction.

This skill is for **one-time setup** or major design-direction resets. It does not write application code, generate mockups, or review implementation diffs.

---

## Trigger routing

Use this skill when the user wants Codex / Claude Code to learn a project's design direction before building UI.

Trigger phrases include:

- `dev-design-context`
- `setup design context`
- `设计上下文`
- `设计规范`
- `先建立设计方向`
- `gather design context`
- `persistent design guidelines`

Output goes to `.design-context.md` in the project root.

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。以下行为准则在本 skill 全程生效:**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准**。

baseline 与本 skill 的关联点:

- **不假设** —— 先扫描真实代码和资产,再问问题;不要让用户重复回答代码里已经能看到的信息。
- **最小代码** —— 只写 `.design-context.md` 的设计上下文,不要顺手改组件、CSS 或产品文案。
- **外科手术式改动** —— 如果 `.design-context.md` 已存在,只更新 `## Design Context` 相关内容。
- **可验证成功标准** —— 结束前明确写出设计原则已经落在哪个文件,并总结未来设计工作应遵守的 3-5 条原则。

## Step 1 — Explore the codebase

Before asking questions, scan the project to discover what can be inferred:

- **README and docs**: project purpose, target audience, and stated goals
- **Package / config files**: tech stack, dependencies, and design libraries
- **Existing components**: layout patterns, spacing, typography, component conventions
- **Brand assets**: logos, favicons, image assets, and already-defined color values
- **Design tokens / CSS variables**: color palettes, font stacks, spacing scales, radii, motion values
- **Style guides or brand docs**: any explicit product, content, or visual direction

Summarize what you learned and what remains unclear before asking the user anything.

## Step 2 — Ask UX-focused questions

Ask the user directly to clarify only what cannot be inferred from the codebase. Keep questions focused and avoid long questionnaires.

### Users and purpose

- Who uses this? What is their context when using it?
- What job are they trying to get done?
- What emotions should the interface evoke, such as confidence, calm, delight, urgency, or precision?

### Brand and personality

- How would you describe the brand personality in 3 words?
- Are there reference sites or apps that capture the right feel? What specifically works about them?
- What should this explicitly not look like? Are there anti-references?

### Aesthetic preferences

- Are there strong preferences for visual direction, such as minimal, bold, editorial, technical, playful, or organic?
- Should it support light mode, dark mode, or both?
- Are there colors that must be used or avoided?

### Accessibility and inclusion

- Are there specific accessibility requirements, such as a WCAG level or known user needs?
- Are there constraints around reduced motion, color blindness, contrast, or other accommodations?

Skip questions where the answer is already clear from the codebase exploration.

## Step 3 — Write design context

Synthesize the codebase findings and the user's answers into this section:

```markdown
## Design Context

### Users
[Who they are, their context, and the job to be done]

### Brand Personality
[Voice, tone, 3-word personality, and emotional goals]

### Aesthetic Direction
[Visual tone, references, anti-references, theme, color, and motion direction]

### Design Principles
[3-5 principles derived from the codebase and conversation that should guide all design decisions]
```

Write this section to `.design-context.md` in the project root. If the file already exists, update the `## Design Context` section in place instead of duplicating it.

Then ask the user whether they also want the same Design Context appended to `.github/copilot-instructions.md`. If yes, append or update that section there as well.

Confirm completion and summarize the key design principles that will guide future UI work.

---

## Multi-Agent Profile

Recommended agent_type: explorer

Use when:
- The main agent needs design-system or UI convention discovery before UI work.
- The project has existing components, styles, assets, or brand cues to inspect.
- The sub-agent can summarize findings without implementing UI changes.

Do:
- Explore README, assets, styles, components, tokens, and existing screens.
- Separate codebase facts from assumptions.
- Ask only UX questions that cannot be inferred.
- Follow the explorer boundaries in `../../docs/multi-agent-policy.md`.

Do not:
- Implement UI.
- Rewrite product copy or CSS outside `.design-context.md`.
- Invent brand direction when the project already provides evidence.

Output:
- Codebase design facts
- Unknowns that require user input
- Proposed design principles
- Files inspected
