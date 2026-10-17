# AI & LLM UX Patterns

AI-powered interfaces are now mainstream but have unique UX challenges. This reference covers design patterns for conversational AI, copilots, agents, and generative interfaces.

---

## AI as a Respectful Copilot, Not an Autopilot

The defining 2026 framing (NN/g *State of UX 2026* and broad trend consensus): the
best AI features are a **respectful copilot**—present and helpful, but optional and
under user control—rather than an **autopilot** that hijacks the flow. As raw UI
becomes a commodity, the differentiator is judgment about *when not to act*.

**What "respectful copilot" looks like:**
- **Optional, not forced** — AI is offered (a sidebar, overlay, collapsible panel,
  inline suggestion), never shoved into the critical path. The user can ignore it
  and still complete the task the normal way.
- **Calm and peripheral** — it augments the current context instead of taking over
  the screen; suggestions sit beside the work, not on top of it.
- **User stays in control** — the human initiates or explicitly accepts; AI
  proposes, the user disposes. Every AI action is previewable, reversible, and
  attributable (see "Hidden AI", "Over-automation", "No AI undo" anti-patterns).
- **Transparent** — clearly labeled as AI, honest about confidence and limits,
  shows its sources/reasoning when it matters.

```
Autopilot (avoid)              Respectful copilot (prefer)
─────────────────              ──────────────────────────
Auto-rewrites your text        Suggests an edit you can accept/dismiss
Modal hijacks the screen       Quiet panel beside your work
Acts, then maybe tells you     Proposes, you confirm, then it acts
"AI is doing X…" (opaque)      Shows what, why, and an undo
```

Apply this lens to every pattern below: chat, copilots, and agents should all
default to *offered and reversible*, never *imposed and silent*.

---

## Conversational / Chat UI

### Message Layout

```
┌─────────────────────────────────────────┐
│  User message                    [14:02] │
│  Right-aligned, accent background        │
├─────────────────────────────────────────┤
│  [AI avatar]                             │
│  AI response                    [14:02]  │
│  Left-aligned, neutral background        │
│  ┌─────────────────────────────┐         │
│  │ Source: document.pdf, p.12  │         │
│  └─────────────────────────────┘         │
│  [👍] [👎] [Copy] [Regenerate]           │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐   │
│  │ Type a message...          [Send] │   │
│  │ [Attach] [Voice]                  │   │
│  └───────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Message Bubbles

- **User messages**: Right-aligned, accent color background, rounded corners
- **AI messages**: Left-aligned, neutral/light background, distinct from user
- **System messages**: Centered, muted, no bubble (e.g., "Conversation started")
- **Max width**: 70-80% of container to maintain readability
- **Timestamps**: Show on hover or at natural breaks, not every message

### Streaming Responses

```
AI is typing...
├── Show cursor/blinking indicator at end of text
├── Render markdown incrementally (not raw then formatted)
├── Allow user to stop generation mid-stream [Stop] button
├── Smooth text appearance (word-by-word or chunk-by-chunk)
└── Don't auto-scroll if user has scrolled up to read history
```

**Key timings:**
- First token should appear within 500ms-1s (perceived responsiveness)
- Show typing indicator immediately on send
- Skeleton/placeholder for structured outputs (tables, code blocks)

### Turn-Taking

- Disable send button while AI is responding (or allow interrupt)
- Clear visual separation between turns
- Support editing previous user messages and re-generating from that point
- Show "AI is thinking..." for multi-step reasoning delays
- Multi-turn context: show thread/conversation history clearly

---

## Prompt UX

### Input Design

```html
<!-- Expandable textarea that grows with content -->
<div class="prompt-input">
  <textarea
    placeholder="Ask anything..."
    rows="1"
    aria-label="Message input"
  ></textarea>
  <div class="input-actions">
    <button aria-label="Attach file">📎</button>
    <button aria-label="Send message" disabled>→</button>
  </div>
</div>
```

**Best practices:**
- Auto-expanding textarea (start 1 row, grow to ~6, then scroll)
- Send on Enter, Shift+Enter for newline (document this with a tooltip)
- Enable send button only when input is non-empty
- Character/token count for limited contexts
- Support paste of images, files, and rich text

### Suggested Prompts

```
┌─────────────────────────────────────────┐
│  What can I help you with?              │
│                                         │
│  ┌──────────┐  ┌──────────────────┐     │
│  │ Summarize │  │ Compare options  │     │
│  │ this doc  │  │ for deployment   │     │
│  └──────────┘  └──────────────────┘     │
│  ┌──────────────┐  ┌──────────────┐     │
│  │ Write a test  │  │ Explain this │     │
│  │ for this fn   │  │ error        │     │
│  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────┘
```

- Show 3-6 contextual suggestions on empty state
- Update suggestions based on current context (file open, selection, etc.)
- Use prompt templates for complex tasks with fill-in-the-blank slots
- Allow users to save and reuse their own prompt templates
- Provide category-based prompt libraries for discoverability

### Multimodal Inputs

- Image upload with preview and crop/annotate before sending
- File attachment with type indicators and size display
- Voice input with waveform visualization and transcription preview
- Screen/selection capture with annotation tools
- Drag-and-drop support with clear drop zone indicators

---

## AI Transparency & Trust

### Confidence Indicators

```
High confidence:
  "The capital of France is Paris."

Medium confidence:
  "Based on available data, revenue likely increased ~15%."
  ⚠️ This estimate is based on partial data

Low confidence:
  "I'm not certain, but this might be related to..."
  ⚠️ Low confidence — verify independently
```

**Pattern options:**
- Textual hedging ("I believe", "Based on...", "I'm not sure")
- Visual indicators (confidence bars, color-coded borders)
- Explicit disclaimers for uncertain outputs
- "Verified" badges for factual claims with sources

### Source Attribution

```
┌─────────────────────────────────────────┐
│  AI Response text here with inline      │
│  citations [1] and references [2].      │
│                                         │
│  ┌─ Sources ─────────────────────────┐  │
│  │ [1] design-system.md, line 42     │  │
│  │ [2] api-docs.md, §Authentication  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

- Inline citations linked to expandable source cards
- Distinguish between direct quotes and paraphrasing
- Show source reliability/recency metadata
- Allow click-through to original source
- Group sources by type (documents, web, code)

### "AI-Generated" Labels

- Mark AI-generated content clearly: "Generated by AI" or sparkle icon (✨)
- Distinguish AI suggestions from confirmed/human-edited content
- Persist labels through copy/paste and export
- Follow platform regulations (EU AI Act requires labeling)

---

## Hallucination Handling

### Prevention UX

- Ground responses in user-provided context (RAG patterns)
- Show "based on" indicators linking to source material
- Limit AI to domains where it has verified information
- Offer "search the web" as explicit fallback for unknown topics

### Detection & Recovery

```
┌─────────────────────────────────────────┐
│  AI: "The function `getData()` returns  │
│  a Promise<User[]>."                    │
│                                         │
│  ⚠️ Could not verify this in your       │
│  codebase. [Check source] [Report]      │
│                                         │
│  Was this response helpful?             │
│  [👍 Yes] [👎 No — incorrect]           │
└─────────────────────────────────────────┘
```

- Provide feedback mechanisms (thumbs up/down, flag as incorrect)
- "Regenerate" button to get a fresh response
- User correction flow: allow editing AI output directly
- Track and surface known inaccuracies for similar future queries
- Show verification status for factual claims when possible

---

## Human-in-the-Loop

### Approval Workflows

```
┌─────────────────────────────────────────┐
│  AI Suggestion                          │
│  ┌───────────────────────────────────┐  │
│  │ Proposed changes:                 │  │
│  │ - Update user.email to new value  │  │
│  │ - Send confirmation email         │  │
│  │ - Log change in audit trail       │  │
│  └───────────────────────────────────┘  │
│                                         │
│  [✓ Apply All] [Review Each] [✗ Cancel] │
└─────────────────────────────────────────┘
```

### Suggestion vs. Auto-Action Spectrum

```
Full manual ←────────────────────→ Full auto

  Suggest    →  Suggest+     →  Auto+     →  Auto
  only         default apply   notify       silent

  User        User can        User can     No user
  initiates   reject          review       action
  action      suggestion      after        needed
```

**Best practices:**
- Default to "suggest" mode for destructive or irreversible actions
- Allow users to configure automation level per action type
- Show clear diff/preview before applying changes
- Provide undo for auto-applied actions (minimum 10 seconds)
- Log all AI-initiated actions for auditability

### Override Patterns

- Always provide manual override for AI decisions
- Make overrides discoverable (not hidden in settings)
- Don't penalize users for overriding (no "Are you sure?" friction)
- Learn from overrides to improve future suggestions
- Show "AI suggested X, you chose Y" in history for context

---

## Generative UI

### AI-Generated Interface Elements

- Render structured AI outputs as rich components (tables, charts, forms)
- Provide fallback to plain text if rendering fails
- Allow user to toggle between rendered and raw views
- Maintain accessibility in generated components

### Adaptive Layouts

```
Simple query → Single text response
Data query   → Table or chart + summary
Comparison   → Side-by-side cards
Multi-step   → Numbered steps with progress
Code query   → Syntax-highlighted block with copy button
```

- Match output format to query intent
- Let users request different output formats ("show as table")
- Remember format preferences per query type

---

## AI Copilot Patterns

### Inline Suggestions

```
┌──────────────────────────────────────────┐
│  function calculateTotal(items) {        │
│    return items.reduce((sum, item) =>    │
│    ░░sum + item.price * item.qty, 0);░░  │  ← ghost text
│  }                                       │
│                                          │
│  [Tab] to accept  [Esc] to dismiss      │
└──────────────────────────────────────────┘
```

**Ghost text / inline completion:**
- Show suggestion as dimmed/ghost text at cursor position
- Tab to accept, Esc to dismiss, keep typing to refine
- Accept word-by-word with Ctrl+Right (partial accept)
- Show suggestion after 300-750ms pause in typing (debounce)
- Never show during active, rapid typing

### Accept / Reject / Modify

- **Accept**: Tab or click — apply suggestion immediately
- **Reject**: Esc or keep typing — dismiss silently
- **Modify**: Accept then edit — encourage iteration
- **Partial accept**: Accept first N words/lines
- Show acceptance rate metrics to tune suggestion quality

### Suggestion Panel (Multi-Option)

```
┌─ AI Suggestions ────────────────────────┐
│                                          │
│  Option 1: Using array.filter()          │
│  ┌────────────────────────────────────┐  │
│  │ const active = users.filter(u =>  │  │
│  │   u.status === 'active');         │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Option 2: Using for...of loop           │
│  ┌────────────────────────────────────┐  │
│  │ const active = [];                │  │
│  │ for (const u of users) { ...      │  │
│  └────────────────────────────────────┘  │
│                                          │
│  [Apply #1] [Apply #2] [Dismiss]         │
└──────────────────────────────────────────┘
```

---

## Agent UX

### Multi-Step Task Visibility

```
┌─ Agent Task: "Deploy to staging" ───────┐
│                                          │
│  ✅ Step 1: Run tests          (12s)     │
│  ✅ Step 2: Build application  (45s)     │
│  🔄 Step 3: Push to registry   ...       │
│  ⬚  Step 4: Update deployment            │
│  ⬚  Step 5: Run health checks            │
│                                          │
│  ├── Elapsed: 1m 23s                     │
│  └── [View Logs] [Pause] [Cancel]        │
└──────────────────────────────────────────┘
```

### Progress & Autonomy Controls

- Show current step, total steps, and elapsed time
- Expandable logs/details for each step
- Pause/Resume to give users control over long-running tasks
- Cancel with confirmation for destructive operations
- Estimated remaining time when possible

### Tool-Use Transparency

```
┌─────────────────────────────────────────┐
│  🔧 Agent used: file_search             │
│     Searched 24 files matching "*.ts"    │
│     Found 3 relevant results             │
│     [Show details ▾]                     │
│                                          │
│  🔧 Agent used: code_edit               │
│     Modified: src/utils/auth.ts          │
│     [View diff ▾]                        │
└─────────────────────────────────────────┘
```

- Show each tool invocation with name and brief description
- Collapsible detail view (inputs, outputs, duration)
- Highlight side effects (file writes, API calls, etc.)
- Permission prompts before sensitive tool use
- Full audit log accessible after task completion

---

## Ethical AI UX

### Bias Disclosure

- Acknowledge known limitations and biases upfront
- Provide model card information accessible from the UI
- Show training data recency ("Knowledge current through [date]")
- Flag outputs in sensitive domains (medical, legal, financial)

### User Control Over AI Behavior

```
┌─ AI Preferences ────────────────────────┐
│                                          │
│  Response style:  [Concise ▾]            │
│  Creativity:      ████░░░░░ 40%          │
│  Auto-suggest:    [✓ Enabled]            │
│  Data usage:      [View policy]          │
│                                          │
│  [Reset to defaults]                     │
└──────────────────────────────────────────┘
```

- Let users adjust tone, verbosity, creativity
- Opt-out of data collection for model training
- Clear "forget this conversation" action
- Per-conversation or global preference settings
- Transparent about what data is retained and for how long

### Opt-Out Mechanisms

- Easy toggle to disable AI features entirely
- Graceful degradation to manual workflows
- No penalty or reduced functionality for opting out
- Clear explanation of what changes when AI is disabled
- Respect opt-out across sessions and devices

---

## Key Metrics

| Metric | Target | Context |
|--------|--------|---------|
| Time to first token | < 1s | Perceived responsiveness |
| Streaming speed | 30-80 tokens/s | Natural reading pace |
| Suggestion acceptance rate | 25-35% | Copilot usefulness |
| Response rating (thumbs up) | > 80% | Quality benchmark |
| Regeneration rate | < 15% | First-response quality |
| Task completion (agents) | > 90% | Reliability |
| Hallucination rate | < 5% | Factual accuracy |
| Human override rate | Track trend | Automation calibration |

---

## Anti-Patterns

1. **Anthropomorphizing too much** — Avoid names, personalities, or claims of emotions that mislead users about AI capabilities
2. **No streaming** — Showing nothing then dumping a wall of text feels broken
3. **Hidden AI** — Users should always know when they're interacting with AI
4. **Ignoring errors** — Silently failing or making up answers instead of admitting uncertainty
5. **Over-automation** — Applying AI changes without user awareness or consent
6. **No undo for AI actions** — AI-applied changes must be reversible
7. **Prompt injection vulnerability** — Showing AI outputs that can execute code or alter UI
8. **Infinite context illusion** — Not communicating context window limits
9. **Blocking UI during generation** — Users should be able to navigate or cancel
10. **No feedback loop** — Not providing thumbs up/down or correction mechanisms

---

## Sources

- [Nielsen Norman Group: UX for AI](https://www.nngroup.com/articles/ai-ux/) — AI interaction research
- [Nielsen Norman Group: State of UX](https://www.nngroup.com/articles/) — annual UX trend analysis (respectful-copilot framing)
- [Google PAIR: People + AI Guidebook](https://pair.withgoogle.com/guidebook) — AI design patterns
- [Apple: Human Interface Guidelines for Machine Learning](https://developer.apple.com/design/human-interface-guidelines/machine-learning)
- [Microsoft: HAX Toolkit](https://www.microsoft.com/en-us/haxtoolkit/) — Human-AI interaction guidelines
- [Anthropic: Responsible AI Practices](https://www.anthropic.com/) — Safety and transparency
- [EU AI Act](https://artificialintelligenceact.eu/) — Regulatory requirements for AI interfaces
