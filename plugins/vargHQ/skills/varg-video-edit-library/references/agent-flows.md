# AI agent flows

Agents at work: step lists, tool calls, node graphs, streaming chat answers and hand-offs between agents. 10 takes. Browse them with previews at https://skills.varg.ai/browse/skills/agent-flows/.

Make an agent's work legible without raw logs: a typed task as the hook, then plain-language steps that go running → done, and a visible result. Stream text in natural bursts, build node graphs in narration order, and compress waits to under a second or two.

## Prompt Typed, Then Generate

<a id="prompt-typed-then-generate"></a>A real task types into the prompt box, the Generate button is pressed, and the result starts to build.

Built on [UI AI Prompt Flow](https://remocn.dev/r/ai-prompt-flow.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

Composer field with attachments, human-cadence typing, the button goes hover → press → loading, and the canvas begins to fill.

- **When:** Open of almost every AI product launch: it shows what the product does in the first 3–5 s.
- **Watch out:** Do not open with a logo and voiceover before the prompt; the typed task is the hook.
- **Timing:** Typing 40–70 ms/char in bursts; button press 0.1/0.2 s; result starts ≤ 0.5 s after.
- **Also called:** prompt box, AI prompt flow, type and generate
- **Card:** https://skills.varg.ai/skills/prompt-typed-then-generate/

### HyperFrames

```bash
npx hyperframes add typed-prompt
npx hyperframes add ai-chat-reveal
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/ai-prompt-flow
// or @remocn/claude-chat / @remocn/chat-gpt for branded composers
```

### CapCut

Record the real prompt; speed typing 1.5–2×; zoom 170% on the composer while typing, release on Generate.

### Components

- UI AI Prompt Flow (remocn): `npx shadcn@latest add @remocn/ai-prompt-flow` · https://skills.varg.ai/component/remocn.ai-prompt-flow/
- Typed Prompt (hyperframes): `npx hyperframes add typed-prompt` · https://skills.varg.ai/component/hf.typed-prompt/
- Claude Chat (remocn): `npx shadcn@latest add @remocn/claude-chat` · https://skills.varg.ai/component/remocn.claude-chat/
- AI Chat Reveal (hyperframes): `npx hyperframes add ai-chat-reveal` · https://skills.varg.ai/component/hf.ai-chat-reveal/

Sources: [Bohdan Motion: breakdown of the Claude Design launch video](https://x.com/bohdanmotion/status/2080610655237751033) · [Bohdan Motion: breakdown of the ElevenLabs Flows launch video](https://x.com/bohdanmotion/status/2079974237893456071) · [Bohdan Motion: breakdown of the Grok Build Mode launch video](https://x.com/bohdanmotion/status/2082193183111614671)

## Answer Streams In

<a id="answer-streams-in"></a>The assistant's reply arrives in uneven token bursts, the way a real model streams.

Built on [Streaming Text](https://github.com/heygen-com/hyperframes/tree/main/registry/components/streaming-text) by Miao Yang (hyperframes), Apache-2.0. The write-up and recipes are varg's.

Words appear in short irregular bursts with a soft caret; markdown headings and lists form as they stream.

- **When:** Chat assistants and any feature whose output is text.
- **Watch out:** Do not reveal at a perfectly even rate; real streams come in bursts and that rhythm sells authenticity.
- **Timing:** Bursts of 2–6 tokens every 40–120 ms; total ≤ 3 s on screen, then hold.
- **Also called:** streaming text, token stream, AI reply
- **Card:** https://skills.varg.ai/skills/answer-streams-in/

### HyperFrames

```bash
npx hyperframes add streaming-text
```
Use a fixed seed for burst sizes so every render streams identically.

### Remotion

```tsx
const bursts = useMemo(()=>seededBursts(text, 42),[]); // [{at,frame,upto}]
const upto = bursts.filter(b=>b.frame<=frame).at(-1)?.upto ?? 0;
<Markdown>{text.slice(0,upto)}</Markdown>
```

### CapCut

Record the real stream; or Text → Animation In "Typewriter" with a long duration on a pasted answer.

### Components

- Streaming Text (hyperframes): `npx hyperframes add streaming-text` · https://skills.varg.ai/component/hf.streaming-text/
- Claude Exchange (hyperframes): `npx hyperframes add claude-exchange` · https://skills.varg.ai/component/hf.claude-exchange/
- Text Generate Effect (aceternity): `npx shadcn@latest add @aceternity/text-generate-effect` · https://skills.varg.ai/component/aceternity.text-generate-effect/

Sources: [Glama: designing tool-enabled chat interfaces](https://glama.ai/blog/2025-08-27-designing-tool-enabled-chat-interfaces) · [Trace visualization: showing users what your AI agent is doing](https://agentinterface-co.pages.dev/blog/trace-visualization-showing-users-what-ai-agent-does.html)

## Tool Calls as Status Rows

<a id="tool-calls-status-rows"></a>Each tool call appears as a row with an icon and label that goes spinner → check, building a visible plan.

Built on [Agent Run](https://remocn.dev/r/agent-run.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

Rows like "Searching docs…", "Reading 3 files", "Running tests" with a shimmer while running and a green check when done; planned steps greyed.

- **When:** Explain what an agent does without raw logs; make autonomy legible.
- **Watch out:** Do not dump JSON or full logs on screen; one plain-language line per step.
- **Timing:** Row in 0.2 s; running shimmer 0.6–1.2 s; check pop 0.2 s; next row starts on the check.
- **Also called:** agent steps, tool use trace, run log
- **Card:** https://skills.varg.ai/skills/tool-calls-status-rows/

### HyperFrames

```bash
npx hyperframes add state-chip-rail
```
One row per step; tween `data-state` running → done on cue times.

### Remotion

```tsx
// npx shadcn@latest add @remocn/agent-run
<AgentRun steps={[{label:'Searching docs',doneAt:30},{label:'Writing scene',doneAt:60}]}/>
```

### CapCut

Text rows with Animation In "Fade in"; a spinner sticker then a ✓ sticker per row.

### Components

- Agent Run (remocn): `npx shadcn@latest add @remocn/agent-run` · https://skills.varg.ai/component/remocn.agent-run/
- State Chip Rail (hyperframes): `npx hyperframes add state-chip-rail` · https://skills.varg.ai/component/hf.state-chip-rail/
- Text Shimmer (motion-primitives): `npx motion-primitives@latest add text-shimmer` · https://skills.varg.ai/component/motionprimitives.text-shimmer/

Sources: [Trace visualization: showing users what your AI agent is doing](https://agentinterface-co.pages.dev/blog/trace-visualization-showing-users-what-ai-agent-does.html) · [Glama: designing tool-enabled chat interfaces](https://glama.ai/blog/2025-08-27-designing-tool-enabled-chat-interfaces)

## Nodes Wire Up on a Canvas

<a id="nodes-wire-up-canvas"></a>Nodes pop onto a canvas and connectors draw between them as the camera pulls back to show the whole pipeline.

Built on [Flowchart](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/flowchart) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Rounded nodes with icons and labels; bezier connectors draw from output to input; a pulse travels the finished path.

- **When:** Workflow builders, multi-step AI pipelines, automations.
- **Watch out:** Do not show the whole graph first; build it in narration order, then reveal the full canvas.
- **Timing:** Node pop 0.25 s, connector draw 0.4–0.6 s, pulse 0.8 s per edge; final pull-back 1 s.
- **Also called:** node graph, workflow canvas, pipeline graph
- **Card:** https://skills.varg.ai/skills/nodes-wire-up-canvas/

### HyperFrames

```bash
npx hyperframes add flowchart
```
Or `constellation-hub` for feature nodes brightening in narration order.

### Remotion

```tsx
const len = path.getTotalLength();
const off = interpolate(frame,[edge.at,edge.at+15],[len,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
<path d={d} strokeDasharray={len} strokeDashoffset={off}/>
```

### CapCut

Record the real canvas; zoom on each node as it is added, then a long ease-out zoom to 100% for the overview.

### Components

- Flowchart (hyperframes): `npx hyperframes add flowchart` · https://skills.varg.ai/component/hf.flowchart/
- Constellation Hub (hyperframes): `npx hyperframes add constellation-hub` · https://skills.varg.ai/component/hf.constellation-hub/
- Hand-Drawn Flowchart (hyperframes): `npx hyperframes add hw-pipeline` · https://skills.varg.ai/component/hf.hw-pipeline/

Sources: [Bohdan Motion: breakdown of the ElevenLabs Flows launch video](https://x.com/bohdanmotion/status/2079974237893456071)

## Beams Into the Agent Hub

<a id="beams-into-agent-hub"></a>Light pulses run along curved lines from tool icons into a central agent and back out to a result.

Built on [Animated Beam](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/animated-beam.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

App icons on the left, the agent mark in the center, outputs on the right; gradient beams travel along curved paths.

- **When:** Show that an agent connects tools and data (MCP, integrations, sources).
- **Watch out:** Do not run every beam at once; stagger them so the eye follows the flow.
- **Timing:** Beam travel 1.5–3 s per path, 0.2–0.4 s stagger; curvature small (≤ 80 px).
- **Also called:** animated beam, data flow, hub and spokes
- **Card:** https://skills.varg.ai/skills/beams-into-agent-hub/

### HyperFrames

```bash
npx hyperframes add tracing-beam
```
Draw the paths in SVG; animate a short gradient dash along each with `strokeDashoffset` on the timeline.

### Remotion

```tsx
// npx shadcn@latest add @magicui/animated-beam  (props: fromRef, toRef, curvature, duration, delay, reverse)
// make it seek-safe: drive the gradient offset from frame instead of its motion animation
```

### CapCut

Add icon overlays and line shapes; animate a small glowing dot sticker along each line with Position keyframes.

### Components

- Animated Beam (magic-ui): `npx shadcn@latest add @magicui/animated-beam` · https://skills.varg.ai/component/magicui.animated-beam/
- Ecosystem Constellation (remocn): `npx shadcn@latest add @remocn/ecosystem-constellation` · https://skills.varg.ai/component/remocn.ecosystem-constellation/
- Tracing Beam (hyperframes): `npx hyperframes add tracing-beam` · https://skills.varg.ai/component/hf.tracing-beam/

Sources: [Magic UI: Animated Beam](https://v3.magicui.design/docs/components/animated-beam)

## Thinking… Shimmer Label

<a id="thinking-shimmer-label"></a>A muted "Thinking…" label with a moving shine shows the model working between prompt and answer.

Built on [Shimmering Text](https://github.com/imskyleen/animate-ui/blob/main/packages/react/src/primitives/texts/shimmering/index.tsx) by animate-ui, MIT + Commons Clause. The write-up and recipes are varg's.

Small grey text with a light band sweeping through it, or three bouncing dots, placed exactly where the answer will appear.

- **When:** Short waits in AI demos; it marks time without dead air.
- **Watch out:** Do not hold it longer than ~1.5 s in a film; cut the real wait down.
- **Timing:** Sweep period 1.2–1.6 s; show for 0.6–1.5 s total.
- **Also called:** thinking indicator, generating label, typing dots
- **Card:** https://skills.varg.ai/skills/thinking-shimmer-label/

### HyperFrames

```bash
npx hyperframes add typing-indicator
```
Or `text-shimmer` on a muted label for the "Generating…" look.

### Remotion

```tsx
const x = ((frame % 40) / 40) * 160 - 30;
<span style={{backgroundImage:`linear-gradient(90deg,#666 ${x-15}%,#eee ${x}%,#666 ${x+15}%)`,WebkitBackgroundClip:'text',color:'transparent'}}>Thinking…</span>
```

### CapCut

Text "Thinking…" in grey; Effects → "Shine" or Animation Loop "Flicker" gently.

### Components

- Shimmering Text (animate-ui): `npm install @animate-ui/react motion` · https://skills.varg.ai/component/animateui.shimmering-text/
- Text Shimmer (motion-primitives): `npx motion-primitives@latest add text-shimmer` · https://skills.varg.ai/component/motionprimitives.text-shimmer/
- Typing Indicator (hyperframes): `npx hyperframes add typing-indicator` · https://skills.varg.ai/component/hf.typing-indicator/
- UI Typing Indicator (remocn): `npx shadcn@latest add @remocn/typing-indicator` · https://skills.varg.ai/component/remocn.typing-indicator/

Sources: [Trace visualization: showing users what your AI agent is doing](https://agentinterface-co.pages.dev/blog/trace-visualization-showing-users-what-ai-agent-does.html)

## Parallel Agents Side by Side

<a id="parallel-agents-lanes"></a>Several agent cards work at once in lanes or an orbit, each with its own status, then merge into one result.

Built on [Three Orbiting Cards](https://github.com/heygen-com/hyperframes/tree/main/registry/components/three-orbiting-cards) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Three to five cards with names (Researcher, Writer, Reviewer) and live status chips; lines converge into a final output card.

- **When:** Multi-agent systems, subagents, parallel cloud agents.
- **Watch out:** Do not make every lane busy with motion; one lane leads at a time while others idle-tick.
- **Timing:** Cards in 0.3 s stagger 0.1 s; status ticks every 0.4–0.8 s; merge 0.6 s.
- **Also called:** multi-agent, agent swarm, parallel runs
- **Card:** https://skills.varg.ai/skills/parallel-agents-lanes/

### HyperFrames

```bash
npx hyperframes add three-orbiting-cards
npx hyperframes add state-chip-rail
```

### Remotion

```tsx
agents.map((a,i)=> <AgentCard key={i} name={a.name} status={a.timeline.findLast(s=>s.f<=frame)?.label} style={{left:`${12+i*26}%`}}/>)
```

### CapCut

Split screen into 3 lanes (Templates → split screen), one recording per lane, then cut to the merged result.

### Components

- Three Orbiting Cards (hyperframes): `npx hyperframes add three-orbiting-cards` · https://skills.varg.ai/component/hf.three-orbiting-cards/
- State Chip Rail (hyperframes): `npx hyperframes add state-chip-rail` · https://skills.varg.ai/component/hf.state-chip-rail/
- Split Tilt Cards (hyperframes): `npx hyperframes add split-tilt-cards` · https://skills.varg.ai/component/hf.split-tilt-cards/

Sources: [Vox on X: a 4-agent HyperFrames motion team for product videos](https://x.com/Voxyz_ai/status/2104194355556671987) · [Cursor 3 Design Mode and its launch video](https://pasqualepillitteri.it/en/news/3794/cursor-design-mode-what-it-is-how-it-works-cursor-3)

## Plan Checklist Ticks Off

<a id="plan-checklist-ticks"></a>The agent's plan appears as a checklist and each item ticks and dims as it is done.

Built on [Specs Checklist](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/mk-specs-list) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Left-aligned rows with empty circles; a check draws in each, the row text dims or strikes, the next row brightens.

- **When:** Long tasks compressed into a few seconds; show progress and reliability.
- **Watch out:** Do not tick everything at an even pace; vary 0.4–1.0 s to feel like real work.
- **Timing:** Rows in 0.2 s with 0.08 s stagger; each tick 0.3 s path draw; final row → success pop.
- **Also called:** todo list, agent plan, checklist
- **Card:** https://skills.varg.ai/skills/plan-checklist-ticks/

### HyperFrames

```bash
npx hyperframes add mk-specs-list
npx hyperframes add success-check
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/check-list
const done = (i)=> frame > ticks[i];
```

### CapCut

Text list with one row per layer; add ✓ stickers on each row at its time; reduce row Opacity to 50% after its tick.

### Components

- Specs Checklist (hyperframes): `npx hyperframes add mk-specs-list` · https://skills.varg.ai/component/hf.mk-specs-list/
- Check List (remocn): `npx shadcn@latest add @remocn/check-list` · https://skills.varg.ai/component/remocn.check-list/
- Success Check (hyperframes): `npx hyperframes add success-check` · https://skills.varg.ai/component/hf.success-check/

Sources: [Trace visualization: showing users what your AI agent is doing](https://agentinterface-co.pages.dev/blog/trace-visualization-showing-users-what-ai-agent-does.html)

## Vertical Chat Exchange

<a id="vertical-chat-exchange"></a>A portrait chat plays out: the prompt types and sends, the answer streams and assembles a card or image.

Built on [ChatGPT Exchange](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/chatgpt-exchange) by Jake Moran (hyperframes), Apache-2.0. The write-up and recipes are varg's.

Phone-sized chat UI, bubbles pop with a tiny scale from the sender's corner, typing dots before replies.

- **When:** Vertical cuts for TikTok, Reels and Shorts about AI features.
- **Watch out:** Do not make bubbles readable only at full screen; use 1.5× normal type size for phones.
- **Timing:** Bubble pop 0.12–0.2 s (scale 0.75→1), typing dots 0.6–1 s, gap 0.3 s between messages.
- **Also called:** chat story, ChatGPT exchange, phone chat
- **Card:** https://skills.varg.ai/skills/vertical-chat-exchange/

### HyperFrames

```bash
npx hyperframes add chatgpt-exchange
```
Or `message-thread-reveal` / `chat-thread` for human conversations.

### Remotion

```tsx
// npx shadcn@latest add @remocn/imessage-chat-flow
// or @remocn/chat-flow / @remocn/telegram-chat-flow
```

### CapCut

Text → Text templates → "chat"/"message"; one bubble per layer, Animation In "Pop up" 0.15 s.

### Components

- ChatGPT Exchange (hyperframes): `npx hyperframes add chatgpt-exchange` · https://skills.varg.ai/component/hf.chatgpt-exchange/
- Message Thread Reveal (hyperframes): `npx hyperframes add message-thread-reveal` · https://skills.varg.ai/component/hf.message-thread-reveal/
- UI iMessage Chat Flow (remocn): `npx shadcn@latest add @remocn/imessage-chat-flow` · https://skills.varg.ai/component/remocn.imessage-chat-flow/

Sources: [CapCut: turn testimonials into quote graphics for short-form](https://www.capcut.com/create/testimonial-quote-graphics-short-form-content)

## Tracing Beam Through Steps

<a id="tracing-beam-through-steps"></a>A glowing dash travels one path through numbered steps, lighting each as it passes.

Built on [Tracing Beam](https://github.com/heygen-com/hyperframes/tree/main/registry/components/tracing-beam) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A thin rail connects 3–5 step cards; a bright head with a short tail moves along it and each card lifts and brightens on contact.

- **When:** Explain a 3–5 step workflow (connect → generate → publish) in one continuous move.
- **Watch out:** Do not exceed 5 steps; split longer flows into two scenes.
- **Timing:** 1–1.5 s per segment, power2.inOut; card lift 0.25 s on arrival.
- **Also called:** stepper, progress path, onboarding steps
- **Card:** https://skills.varg.ai/skills/tracing-beam-through-steps/

### HyperFrames

```bash
npx hyperframes add tracing-beam
npx hyperframes add onboarding-stepper-flow
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/stepper  (progress = continuous step index)
const step = interpolate(frame,[0,120],[0,4],{extrapolateRight:'clamp'});
```

### CapCut

Line shape with a glowing dot sticker keyframed along it; each step card with Animation In timed to the dot.

### Components

- Tracing Beam (hyperframes): `npx hyperframes add tracing-beam` · https://skills.varg.ai/component/hf.tracing-beam/
- Onboarding Stepper Flow (hyperframes): `npx hyperframes add onboarding-stepper-flow` · https://skills.varg.ai/component/hf.onboarding-stepper-flow/
- Flowchart Vertical (hyperframes): `npx hyperframes add flowchart-vertical` · https://skills.varg.ai/component/hf.flowchart-vertical/
- UI Stepper (remocn): `npx shadcn@latest add @remocn/stepper` · https://skills.varg.ai/component/remocn.stepper/

Sources: [Bohdan Motion: breakdown of the ElevenLabs Flows launch video](https://x.com/bohdanmotion/status/2079974237893456071)
