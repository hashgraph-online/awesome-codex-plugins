---
name: product-designer
description: "EaseUI & Linear/Stripe-caliber Product Designer & Design Architect. MUST be called whenever creating or refining animations, UI elements, video layouts, and motion mockups in this repo. Enforces multi-layer tactile depth, Gestalt layout, typography scale, 1px subtle borders, authentic SVGL logos, and zero-flop verification."
user-invocable: true
when_to_use: "MANDATORY / MUST-CALL before and during the implementation of ANY animation, UI mockup, motion video scene, or layout in this repo. Use to audit, refine, and elevate visual elements to world-class digital craft."
category: design
keywords: [product-designer, ease-ui, tactile-depth, linear-design, stripe-caliber, gestalt-layout, anti-flop, typography, svgl, phosphor]
license: PolyForm Shield 1.0.0 (see LICENSE)
metadata:
  author: design-os
  version: "1.0.0"
---

# Product Designer Skill — EaseUI & Linear/Stripe-Caliber Digital Craft

> **MANDATORY INVARIANT FOR ALL AI AGENTS**:
> Whenever an agent creates, refines, or debugs an animation scene, UI mockup, interactive component, or video layout in `design-os-svg-animation`, this skill **MUST BE ACTIVATED AND CONSULTED FIRST**. Never emit raw generic templates or AI-slop layouts.

---

## 1. Multi-Agent Runtime Mappings

| Agent Harness | Invocation Syntax | Subagent Mode |
| :--- | :--- | :--- |
| **Claude Code** (`.claude`) | `/product-designer` | Subagent `product_designer` |
| **Codex Native** (`Codex CLI`) | Consult `skills/product-designer/SKILL.md` | Persona `Product Designer` |
| **Antigravity** (`Gemini`) | `ak:product-designer` | Subagent `product_designer` |

---

## 2. The 6 Immutable Product Design Hardrules

### Rule 1: Multi-Layer Tactile Depth (No Flat Harsh Shadows)
Generic AI UI relies on single-layer black drops (`box-shadow: 0 4px 6px rgba(0,0,0,0.1)`). World-class UI layers ambient fill with directional depth:
```css
/* Light mode tactile card */
box-shadow:
  0 1px 2px rgba(0, 0, 0, 0.04),
  0 4px 8px -2px rgba(0, 0, 0, 0.06),
  0 16px 24px -6px rgba(0, 0, 0, 0.08);

/* Dark mode elevated surface */
box-shadow:
  0 0 0 1px rgba(255, 255, 255, 0.08),
  0 1px 2px rgba(0, 0, 0, 0.4),
  0 12px 24px -4px rgba(0, 0, 0, 0.6);
```

### Rule 2: Sub-Pixel Hairline Borders & Glassmorphism
Never use heavy 2px opaque borders. Use 1px translucent rims with background blur:
```css
border: 1px solid rgba(255, 255, 255, 0.08);
background: rgba(24, 24, 27, 0.85);
backdrop-filter: blur(16px);
-webkit-backdrop-filter: blur(16px);
```

### Rule 3: Zero Raw Emojis & 100% Vector Icon Integrity (Gate 1 Hardrule)
- **STRICT BAN**: Unicode emojis (e.g. 🌐, 🚀, ⚙️, 💬, ✏️, 📦) are strictly forbidden as UI elements or icons.
- **Icon Set**: Always use Phosphor regular vectors (`@phosphor-icons/core`) or Lucide (`lucide-react`) with exact viewBox (`0 0 256 256` or `0 0 24 24`) and inline SVG geometry.
- **Brand Logos**: Always pull authentic vector marks from **SVGL** (`https://svgl.app/`). Never draw rough custom stars, hand-typed glyphs, or fake logos.

### Rule 4: Aspect Ratio & Geometric Fidelity
- **3D Canvas Projections**: Canvas pixel buffers (`canvas.width`, `canvas.height`) MUST match CSS display bounds (`clientWidth`, `clientHeight`) dynamically. Aspect ratio distortion (e.g. oval globes, stretched spheres) is an instant design failure.
- **Browser Window Frame**: Browser chrome simulation must use authentic macOS/window controls (12px dots with 8px gaps) and genuine tab geometry with smooth inner radii.

### Rule 5: Typography Discipline & Negative Tracking
- **Header Tracking**: High-scale headers (`clamp(28px, 4vw, 48px)`) require tight negative tracking (`letter-spacing: -0.02em` to `-0.03em`).
- **Micro-labels**: Monospace metadata (`JetBrains Mono`, `12px/13px`, `text-transform: uppercase`, `letter-spacing: 0.02em`).
- **Contrast**: Maintain minimum 4.5:1 WCAG AA contrast ratio against all canvas surfaces.

### Rule 6: Deterministic Virtual-Clock Hooks
Animations must never depend on non-deterministic wall-clock `Date.now()` or unbounded `requestAnimationFrame`. All timelines must be driven through a global quantizer hook:
```javascript
window.__seekToTime = function(timeSeconds) {
  // Drives all CSS transitions, Three.js renders, and canvas draws deterministically
};
```

---

## 3. Product Designer Pre-Flight Checklist

Before marking any animation or UI code ready, execute this 5-point audit:

1. [ ] **Vector Icon Audit**: Grep for any raw emoji Unicode characters. Ensure every icon is an official Phosphor SVG.
2. [ ] **Brand Mark Audit**: Sourced genuine SVG from `https://svgl.app/` with intact coordinates and correct viewBox.
3. [ ] **3D / Canvas Distortion Audit**: Verified Three.js camera aspect ratio `width / height === 1` for circular objects; canvas element dimensions dynamically match client bounds.
4. [ ] **Depth & Elevation Audit**: Verified ambient + key multi-layer drop shadows and 1px translucent borders.
5. [ ] **Anti-Flop Gate Execution**: Run automated verification:
   ```bash
   python3 scripts/anti-flop-gate.py
   # Must return: 100% DESIGN:OS ANTI-FLOP GATES PASSED — ZERO FLOP PENALTIES (Exit 0)
   ```

---

## 4. Integration with Animation Workflows

When recreating promo videos or building SVG animations:
- **Phase 1 (Deconstruct)**: Analyze reference scenes with the Product Designer lens (measure spacing, identify font scales, inspect shadows).
- **Phase 2 (Scaffold)**: Implement UI containers using EaseUI modular tokens (8pt grid, concentric radii: outer radius = inner radius + padding).
- **Phase 3 (Verify)**: Run `python3 scripts/anti-flop-gate.py` and inspect headless screenshot renders for pixel perfection.
