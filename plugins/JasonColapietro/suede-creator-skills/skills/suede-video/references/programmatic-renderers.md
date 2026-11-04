# Programmatic Renderers: React Path and Renderer Selection

Read this when the repo already uses React, or when a renderer choice between an
HTML/CSS path and a React path has to be justified before any install
authorization is requested. The HTML/CSS example and both authorization gates
live in SKILL.md; this file only carries the React sample and the selection
table.

---

## React renderer sample

Remotion may fit a React-based workflow. Verify the installed or callable
version, current documentation, license, rendering path, and hosting cost before
recommending it. A composition is a React component that reads the current
frame number and returns what is on screen; props drive content. Confirm whether
rendering is local or uses an authorized hosted renderer.

```tsx
export const ProductDemo: React.FC<{ title: string; features: string[] }> = ({
  title, features
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "#000", color: "#fff" }}>
      <h1>{title}</h1>
      {features.map((f, i) => (
        <Sequence from={i * 30} key={i}>
          <p>{f}</p>
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
```

**Candidate fit:** teams that already write React and want to reuse their
components.

---

## When to Pick Which

Both render web pages to video in a headless browser. The durable difference is
what you write:

| | HTML/CSS renderer (Hyperframes) | React renderer (Remotion) |
|--|---------------------------------|---------------------------|
| You write | HTML, CSS, JS | React components (TypeScript) |
| Timing | Declared in markup; the renderer seeks a paused animation timeline | Computed in code from the current frame number |

Existing HTML, CSS, or browser animations point to the HTML/CSS path; an
existing React codebase points to the React path. Do not call either one more
powerful. For rendering options, licensing, and current features, check each
project's docs ([hyperframes.heygen.com](https://hyperframes.heygen.com/introduction),
[remotion.dev](https://www.remotion.dev/docs)); they change faster than this
file.

Then verify fit in the repo:

| Factor | HTML/CSS renderer | React renderer |
|--------|-------------------|----------------|
| Existing stack | Browser and CSS capability | React and renderer capability |
| Animation needs | Test required transitions | Test required timeline primitives |
| Batch rendering | Verify local or hosted path | Verify local or hosted path |
| Team fit | Inspect maintainability in this repo | Inspect maintainability in this repo |
| Rights and cost | Verify current license and runtime cost | Verify current license and runtime cost |

Neither column is a default. Pick the renderer the repo can already run, and
record the evidence for that call in the handoff.
