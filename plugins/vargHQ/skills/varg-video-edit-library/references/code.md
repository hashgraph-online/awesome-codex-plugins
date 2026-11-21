# Code & terminal

Code that types itself, diffs, terminal sessions, install lines and IDE close-ups that stay readable. 10 takes. Browse them with previews at https://skills.varg.ai/browse/skills/code/.

Code on screen should be short, large and focused: 8–12 visible lines, a real editor theme, and one thing highlighted at a time. Type only the lines that matter at human cadence (bursts of a few characters, 30–100 ms each), use diffs or morphs to show change, and finish developer videos on one copyable command.

## Editor Types the Code

<a id="editor-types-the-code"></a>Syntax-highlighted code types into an editor window with a caret riding the frontier.

Built on [Code Typing](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/code-typing) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A real editor theme (VS Code dark), line numbers, the caret moving with human chunks rather than one char per frame.

- **When:** Show how little code it takes: SDK usage, API calls, config.
- **Watch out:** Do not type more than ~8–12 lines on screen; paste the boilerplate and type only the lines that matter.
- **Timing:** 30–60 ms per char in bursts of 3–8 chars with 80–200 ms pauses; hold 1.5 s after the last line.
- **Also called:** code typing, typed snippet, IDE typing
- **Card:** https://skills.varg.ai/skills/editor-types-the-code/

### HyperFrames

```bash
npx hyperframes add code-typing
```
Token-streamed: the visible frontier is derived from time, so scrubbing is exact.

### Remotion

```tsx
// npm create video@latest -- --code-hike  (Code Hike template)
const n = Math.floor(interpolate(frame,[0,90],[0,code.length],{extrapolateRight:'clamp'}));
<Pre code={highlighted} visibleChars={n}/>
```

### CapCut

Record the editor typing for real (or with a typing tool), speed up 2×, and zoom 150% on the active lines.

### Components

- Code Typing (hyperframes): `npx hyperframes add code-typing` · https://skills.varg.ai/component/hf.code-typing/
- Code Snippet - Dark Modern (hyperframes): `npx hyperframes add code-snippet-dark-modern` · https://skills.varg.ai/component/hf.code-snippet-dark-modern/
- Glass Code Block (remocn): `npx shadcn@latest add @remocn/glass-code-block` · https://skills.varg.ai/component/remocn.glass-code-block/

Sources: [Remotion template: Code Hike](https://remotion.dev/templates/code-hike) · [charmbracelet/vhs: terminal recordings as code (TypingSpeed, Sleep)](https://github.com/charmbracelet/vhs)

## Red/Green Diff Collapse

<a id="red-green-diff"></a>Removed lines flash red and collapse away while added lines expand in green.

Built on [Code Diff](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/code-diff) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Unified diff in an editor frame: red lines shrink in height to zero, green lines grow from zero with a left gutter bar.

- **When:** Show an AI fix, a migration or a one-line config change.
- **Watch out:** Do not show both sides at once and leave it static; the collapse/expand motion is what tells the story.
- **Timing:** Red flash 0.2 s, collapse 0.35 s, green expand 0.4 s power2.out; stagger 0.05 s per line.
- **Also called:** code diff, diff highlight, PR change
- **Card:** https://skills.varg.ai/skills/red-green-diff/

### HyperFrames

```bash
npx hyperframes add code-diff
```
```html
<div data-composition-id="code-diff" data-composition-src="compositions/code-diff.html" data-start="6" data-duration="5" data-track-index="2"></div>
```

### Remotion

```tsx
const h = interpolate(frame,[6,16],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
<div style={{height:`${h*1.5}em`, overflow:'hidden', background:'rgba(248,81,73,0.15)'}}>{removed}</div>
```

### CapCut

Screenshot before and after diffs; add red/green rectangles over changed lines with Fade in; cross-fade the screenshots.

### Components

- Code Diff (hyperframes): `npx hyperframes add code-diff` · https://skills.varg.ai/component/hf.code-diff/

Sources: [Remotion template: Code Hike](https://remotion.dev/templates/code-hike) · [Anthony Fu: Shiki Magic Move](https://antfu.me/posts/shiki-magic-move)

## Spotlight One Line of Code

<a id="spotlight-one-line"></a>A highlight band sweeps onto the one line that matters while the rest of the file dims.

Built on [Code Highlight Sweep](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/code-highlight) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Other lines drop to ~35% opacity, the target line gets a soft accent band and full brightness; optional callout label at the right.

- **When:** Explain the key line of an SDK example or the fix inside a long function.
- **Watch out:** Do not dim to near-black; context must stay readable enough to orient.
- **Timing:** Dim 0.3 s, band sweep 0.4 s power2.out, hold 1.5–2.5 s.
- **Also called:** line highlight, code focus, dim context
- **Card:** https://skills.varg.ai/skills/spotlight-one-line/

### HyperFrames

```bash
npx hyperframes add code-highlight
```

### Remotion

```tsx
const d = interpolate(frame,[0,9],[1,0.35],{extrapolateRight:'clamp'});
lines.map((l,i)=> <div style={{opacity: i===target?1:d, background: i===target?'rgba(56,139,253,0.18)':'none'}}>{l}</div>)
```

### CapCut

Duplicate the code clip; on the top copy Mask → Rectangle around the line; lower the bottom copy's Opacity to 40%.

### Components

- Code Highlight Sweep (hyperframes): `npx hyperframes add code-highlight` · https://skills.varg.ai/component/hf.code-highlight/
- Code Scroll To Line (hyperframes): `npx hyperframes add code-scroll` · https://skills.varg.ai/component/hf.code-scroll/

Sources: [Slidev: Shiki Magic Move (800 ms default)](https://sli.dev/features/shiki-magic-move) · [Remotion template: Code Hike](https://remotion.dev/templates/code-hike)

## Code Morphs Between Versions

<a id="code-morphs-versions"></a>One snippet transforms into the next: shared tokens glide to new positions, removed ones fade, new ones fade in.

Built on [Code Morph](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/code-morph) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Like Keynote Magic Move for code: the editor never cuts, tokens slide on smooth paths.

- **When:** Step-by-step tutorials and "before → after" refactors; showing an API getting simpler.
- **Watch out:** Do not morph between files that share almost nothing; it becomes a confetti of tokens.
- **Timing:** 0.6–0.8 s per morph (Shiki Magic Move defaults to 800 ms), ease-in-out; hold ≥ 1.5 s on each version.
- **Also called:** magic move, token morph, code transition
- **Card:** https://skills.varg.ai/skills/code-morphs-versions/

### HyperFrames

```bash
npx hyperframes add code-morph
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/code-morph
// or Code Hike template: npm create video@latest -- --code-hike (steps from annotated markdown)
```

### CapCut

Not native; render the morph in Slidev (````md magic-move` blocks) or Remotion and import it.

### Components

- Code Morph (hyperframes): `npx hyperframes add code-morph` · https://skills.varg.ai/component/hf.code-morph/
- Code Morph (remocn): `npx shadcn@latest add @remocn/code-morph` · https://skills.varg.ai/component/remocn.code-morph/

Sources: [Anthony Fu: Shiki Magic Move](https://antfu.me/posts/shiki-magic-move) · [Slidev: Shiki Magic Move (800 ms default)](https://sli.dev/features/shiki-magic-move) · [Remotion template: Code Hike](https://remotion.dev/templates/code-hike)

## Terminal Session Run

<a id="terminal-session-run"></a>A terminal types a command, then streams real-looking log output with green checks.

Built on [Terminal Simulator](https://github.com/heygen-com/hyperframes/tree/main/registry/components/terminal-simulator) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Dark terminal with traffic lights, prompt types at human speed, output lines roll in faster, old lines scroll off the top.

- **When:** CLIs, deploy tools, agents that run in the terminal.
- **Watch out:** Do not stream walls of logs; keep 4–8 meaningful lines and fake-skip the rest with "…".
- **Timing:** Typing 50–100 ms/char; output lines every 80–200 ms; 0.5 s pause before the final success line.
- **Also called:** CLI demo, terminal window, command run
- **Card:** https://skills.varg.ai/skills/terminal-session-run/

### FFmpeg

```bash
# record a reproducible session with VHS (uses ffmpeg under the hood)
# demo.tape: Set TypingSpeed 75ms\nType "npx varg render"\nEnter\nSleep 3s
vhs demo.tape
```

### HyperFrames

```bash
npx hyperframes add terminal-simulator
```
Or `code-terminal-run` for one command with a token-chrome panel.

### Remotion

```tsx
// npx shadcn@latest add @remocn/terminal-simulator
<TerminalSimulator commands={[{cmd:'npx varg render', output:['✓ scenes 4','✓ audio','✓ done in 38s']}]}/>
```

### CapCut

Record the real terminal (or a VHS tape), trim the waits, speed up output 2×, zoom on the final line.

### Components

- Terminal Simulator (hyperframes): `npx hyperframes add terminal-simulator` · https://skills.varg.ai/component/hf.terminal-simulator/
- Code Terminal Run (hyperframes): `npx hyperframes add code-terminal-run` · https://skills.varg.ai/component/hf.code-terminal-run/
- Terminal Simulator (remocn): `npx shadcn@latest add @remocn/terminal-simulator` · https://skills.varg.ai/component/remocn.terminal-simulator/

Sources: [charmbracelet/vhs: terminal recordings as code (TypingSpeed, Sleep)](https://github.com/charmbracelet/vhs)

## One-Line Install Card

<a id="one-line-install-card"></a>A single install command types into a small terminal card, prints a success check, and holds.

Built on [Terminal](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/terminal.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

Compact terminal (or pill) with `npx … add` typing, a green ✓ line, and a copy icon; centered with lots of air.

- **When:** End of a developer video, right before or as the CTA.
- **Watch out:** Do not show a multi-step install; one copyable line or link to docs.
- **Timing:** Typing 60–80 ms/char, ✓ line after 0.4 s, hold 2–3 s.
- **Also called:** install command, npx line, get started command
- **Card:** https://skills.varg.ai/skills/one-line-install-card/

### FFmpeg

```bash
-vf "drawtext=fontfile=JetBrainsMono.ttf:text='$ npx skills add varg-ai':x=(w-tw)/2:y=h/2:fontsize=48:fontcolor=white:box=1:boxcolor=0x111111@0.9:boxborderw=28"
```

### HyperFrames

```bash
npx hyperframes add code-snippet-apple-terminal-pro
```
Set the command text in the block variables; keep it on one line.

### Remotion

```tsx
// npx shadcn@latest add @magicui/terminal  (drive typing from frame, not timers)
const n = Math.floor(interpolate(frame,[0,cmd.length*2],[0,cmd.length],{extrapolateRight:'clamp'}));
```

### CapCut

Text → monospace font on a dark rounded shape; Animation In "Typewriter" 1–1.5 s; add a ✓ text line 0.4 s later.

### Components

- Terminal (magic-ui): `npx shadcn@latest add @magicui/terminal` · https://skills.varg.ai/component/magicui.terminal/
- Code Snippet - Apple Terminal Pro (hyperframes): `npx hyperframes add code-snippet-apple-terminal-pro` · https://skills.varg.ai/component/hf.code-snippet-apple-terminal-pro/
- Typing Text (animata): `npx shadcn@latest add https://animata.design/r/text/typing-text.json` · https://skills.varg.ai/component/animata.typing-text/

Sources: [charmbracelet/vhs: terminal recordings as code (TypingSpeed, Sleep)](https://github.com/charmbracelet/vhs)

## Camera Scrolls a Long File

<a id="camera-scrolls-long-file"></a>The view scrolls through a long file and stops with the target line centered and lit.

Built on [Code Scroll To Line](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/code-scroll) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Smooth decelerating scroll with slight motion blur, then a spotlight on the destination line.

- **When:** Walk through a real codebase file or show scale ("this is all generated").
- **Watch out:** Do not scroll at constant speed; ease in and out so the stop is readable.
- **Timing:** Scroll 0.8–1.4 s power3.inOut; spotlight 0.3 s after the stop.
- **Also called:** code scroll, file walkthrough, scroll to line
- **Card:** https://skills.varg.ai/skills/camera-scrolls-long-file/

### FFmpeg

```bash
# scroll a tall code image: crop window moves down
-vf "crop=1920:1080:0:'min(ih-1080, t*900)'"
```

### HyperFrames

```bash
npx hyperframes add code-scroll
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/glass-code-walk
const y = interpolate(frame,[0,36],[0,-targetLine*lineH + 400],{extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)});
```

### CapCut

Add a tall code screenshot, keyframe Position Y from top to the target with ease-in-out.

### Components

- Code Scroll To Line (hyperframes): `npx hyperframes add code-scroll` · https://skills.varg.ai/component/hf.code-scroll/
- Glass Code Walk (remocn): `npx shadcn@latest add @remocn/glass-code-walk` · https://skills.varg.ai/component/remocn.glass-code-walk/

Sources: [Remotion template: Code Hike](https://remotion.dev/templates/code-hike)

## Code Left, Live UI Right

<a id="code-left-ui-right"></a>Code types on the left and the UI on the right snaps to match after each change.

Built on [Live Code Compilation](https://remocn.dev/r/live-code-compilation.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

Two panes: editor and preview. Each typed edit triggers a quick flash/update on the preview side.

- **When:** Frameworks, UI libraries, design-to-code and AI coding tools.
- **Watch out:** Do not let the preview lag; the update should land within 0.2 s of the edit finishing.
- **Timing:** Per edit: typing 0.8–1.5 s, preview update 0.2–0.3 s.
- **Also called:** live preview, split code and result, HMR demo
- **Card:** https://skills.varg.ai/skills/code-left-ui-right/

### HyperFrames

```bash
npx hyperframes add code-typing
```
Two clips side by side; fire a 0.25 s `tl.fromTo(preview,{opacity:0.4},{opacity:1})` and swap the preview image at each edit's end time.

### Remotion

```tsx
// npx shadcn@latest add @remocn/live-code-compilation
// or @remocn/chat-to-preview-layout for chat on the left
```

### CapCut

Split screen: two clips side by side (Basic → Position); cut the preview clip at each edit point.

### Components

- Live Code Compilation (remocn): `npx shadcn@latest add @remocn/live-code-compilation` · https://skills.varg.ai/component/remocn.live-code-compilation/
- Chat to Preview Layout (remocn): `npx shadcn@latest add @remocn/chat-to-preview-layout` · https://skills.varg.ai/component/remocn.chat-to-preview-layout/
- Code Typing (hyperframes): `npx hyperframes add code-typing` · https://skills.varg.ai/component/hf.code-typing/

Sources: [Cursor 3 Design Mode and its launch video](https://pasqualepillitteri.it/en/news/3794/cursor-design-mode-what-it-is-how-it-works-cursor-3) · [Bohdan Motion: breakdown of the Grok Build Mode launch video](https://x.com/bohdanmotion/status/2082193183111614671)

## Code on a Lit 3D Slab

<a id="code-on-3d-slab"></a>Highlighted code sits on a beveled slab that turns through space under studio light, then faces the camera.

Built on [Code 3D Extrude](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/code-3d-extrude) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Thick glassy or dark slab, specular light sliding across, code crisp on the face; optional particles assembling into the glyphs.

- **When:** Hero shot of an SDK or API in a launch film; title beat for developer products.
- **Watch out:** Do not keep the slab angled while the viewer is meant to read; land flat and hold.
- **Timing:** Turn 1.2–1.8 s power2.inOut, land flat, hold 1.5 s.
- **Also called:** 3D code, code hero, extruded code
- **Card:** https://skills.varg.ai/skills/code-on-3d-slab/

### HyperFrames

```bash
npx hyperframes add code-3d-extrude
```
Or `code-particle-assemble` / `code-shader-dissolve` for compile-in effects.

### Remotion

```tsx
const ry = interpolate(frame,[0,45],[-28,0],{extrapolateRight:'clamp',easing:Easing.inOut(Easing.quad)});
<div style={{transform:`perspective(1600px) rotateY(${ry}deg)`, boxShadow:'0 40px 80px rgba(0,0,0,.5)'}}><CodeBlock/></div>
```

### CapCut

Overlay a code screenshot; Animation In "Rotate 3D"; add a light-sweep effect.

### Components

- Code 3D Extrude (hyperframes): `npx hyperframes add code-3d-extrude` · https://skills.varg.ai/component/hf.code-3d-extrude/
- Code Particle Assemble (hyperframes): `npx hyperframes add code-particle-assemble` · https://skills.varg.ai/component/hf.code-particle-assemble/
- Code Shader Dissolve (hyperframes): `npx hyperframes add code-shader-dissolve` · https://skills.varg.ai/component/hf.code-shader-dissolve/

Sources: [Remotion template: Code Hike](https://remotion.dev/templates/code-hike)

## Agent CLI Welcome Screen

<a id="agent-cli-welcome"></a>A coding agent's terminal welcome screen appears, a prompt types, and the agent starts working.

Built on [Claude Code](https://remocn.dev/r/claude-code.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

Dashed welcome box with the tool name, a prompt line typing the task, then status lines and file edits streaming.

- **When:** Videos about agent workflows, skills and plugins for terminal agents.
- **Watch out:** Do not copy a brand's TUI pixel for pixel without permission; keep it generic or use the real recording.
- **Timing:** Welcome 0.4 s, prompt typing 50–70 ms/char, status lines every 0.3 s.
- **Also called:** Claude Code screen, TUI welcome, coding agent terminal
- **Card:** https://skills.varg.ai/skills/agent-cli-welcome/

### HyperFrames

```bash
npx hyperframes add code-snippet-apple-terminal-pro
npx hyperframes add typed-prompt
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/claude-code
// npx shadcn@latest add @remocn/opencode
```

### CapCut

Record the real terminal agent session; cut thinking pauses; zoom on the prompt then on the result.

### Components

- Claude Code (remocn): `npx shadcn@latest add @remocn/claude-code` · https://skills.varg.ai/component/remocn.claude-code/
- OpenCode (remocn): `npx shadcn@latest add @remocn/opencode` · https://skills.varg.ai/component/remocn.opencode/
- Code Snippet - Apple Terminal Pro (hyperframes): `npx hyperframes add code-snippet-apple-terminal-pro` · https://skills.varg.ai/component/hf.code-snippet-apple-terminal-pro/
- Typed Prompt (hyperframes): `npx hyperframes add typed-prompt` · https://skills.varg.ai/component/hf.typed-prompt/

Sources: [Vox on X: a 4-agent HyperFrames motion team for product videos](https://x.com/Voxyz_ai/status/2104194355556671987) · [charmbracelet/vhs: terminal recordings as code (TypingSpeed, Sleep)](https://github.com/charmbracelet/vhs)
