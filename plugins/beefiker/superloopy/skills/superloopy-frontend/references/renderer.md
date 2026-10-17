# Renderer and Composition Contract

Use this when the UI is canvas-, engine-, scene-, texture-, or otherwise custom-rendered, or when one surface mixes DOM, native control, and custom regions. Renderer choice changes what can be assumed about semantics, text, input, accessibility, performance, and crawlability.

## Classify composition

For each region, record whether DOM, native control, custom renderer, or mixed composition owns pixels, layout, hit testing, text, focus, and semantics. Name overlays and portals explicitly. Do not infer a semantic tree from visual resemblance or infer native behavior from a toolkit brand.

The semantic and accessibility owner must expose useful names, roles, states, actions, relationships, bounds, reading/traversal order, live status, and focus. If an accessibility bridge or overlay mirrors scene data, prove synchronization during mutation, scroll, zoom, occlusion, virtualization, and teardown.

## Text and input

Prove text shaping, fallback, locale, bidirectionality, selection, clipboard, input, focus, IME composition, caret geometry, editing, validation, and assistive-technology interaction. A drawn text field is not an input capability until it implements the relevant semantic edit/validate/commit/cancel contract.

Map pointer, touch, keyboard, stylus, controller, and accessibility actions only where supported. Preserve equivalent semantic results and failure truth. Avoid invisible DOM or native controls that drift from the pixels they claim to represent.

## Scaling and performance

Build a **target-applicable scaling matrix** from device-pixel ratio (DPR), zoom, text scaling, resize/window class, orientation, safe areas/insets, large content, reduced motion, contrast/theme changes, and capture/compositing paths. Test orientation and safe areas only when the named target supports or exposes them, and record the rest as not applicable rather than simulating a foreign platform. Measure frame pacing, input latency, memory, startup, and power only when those claims matter; a fast synthetic scene does not prove a real journey.

Crawlability is a separate capability to prove when the current renderer target is deployed as crawlable public Web. For native or embedded current targets, assess it only on a distinct public Web deployment. Canvas, WebAssembly, engine output, or a hidden DOM fallback does not become indexable by declaration.

## Renderer evidence

Use semantic-tree inspection, input/IME journeys, screen-reader or platform accessibility checks, representative scaling/content matrices, and performance traces as applicable. Screenshot or pixel similarity can aim a visual review but is not capability promotion and cannot prove semantics, interaction, native integration, or crawlability.

Record renderer/backend/provider/version, composition boundaries, accessibility bridge, target hardware/software, build flags, and known fallbacks. Treat missing target tooling as an explicit unverified claim or blocker.
