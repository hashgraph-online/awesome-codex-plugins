# Suede AI Video Prompting Guide

How Suede writes testable prompts for any currently callable and authorized AI
video model.

---

## Prompt Structure

A strong video prompt follows this formula:

```
[Subject] + [Action] + [Camera movement] + [Visual style] + [Lighting/mood] + [Technical specs]
```

### Example Prompts by Use Case

**Product hero shot:**
```
A sleek laptop on a minimal white desk, screen glowing with a dashboard UI,
camera slowly orbits 180 degrees around the desk,
soft volumetric lighting from the left, shallow depth of field,
cinematic commercial aesthetic, 4K
```

**Lifestyle B-roll:**
```
A woman in a modern co-working space smiling while looking at her phone,
natural window light, candid documentary feel,
camera handheld with subtle movement, warm color grading
```

**Abstract/brand:**
```
Flowing liquid gold particles forming the shape of a network graph,
dark background, particles catch light as they move,
slow-motion macro photography style, dramatic rim lighting
```

**SaaS explainer scene:**
```
An overhead shot of a team around a conference table pointing at charts,
camera slowly pushes in, bright modern office,
clean corporate style, even lighting, 1080p
```

---

## Camera Movement Vocabulary

Use these terms: video models understand them:

| Term | Effect |
|------|--------|
| **Static** | Locked camera, no movement |
| **Pan left/right** | Camera rotates horizontally |
| **Tilt up/down** | Camera rotates vertically |
| **Dolly in/out** | Camera moves toward/away from subject |
| **Orbit** | Camera circles around subject |
| **Tracking shot** | Camera follows moving subject |
| **Crane/aerial** | Camera rises or descends |
| **Handheld** | Subtle shake, documentary feel |
| **Zoom** | Lens zoom (different from dolly) |
| **Slow push** | Gradual dolly in: builds tension/focus |

---

## Style Keywords

### Cinematic
- "cinematic color grading"
- "anamorphic lens flare"
- "shallow depth of field"
- "film grain"
- "35mm film"

### Commercial/Corporate
- "clean commercial lighting"
- "bright and airy"
- "professional corporate aesthetic"
- "even, diffused lighting"

### Documentary
- "handheld documentary style"
- "natural lighting"
- "candid, unposed"
- "observational camera"

### Social/Trendy
- "vertical 9:16"
- "fast-paced cuts"
- "bold text overlays"
- "high contrast, saturated colors"

---

## Model-Specific Verification

Do not carry model capability, quality, duration, price, or prompt-length claims
from memory. For each currently callable candidate:

1. Read its current official documentation and the authenticated account limits.
2. Record the controls actually exposed: text-to-video, image reference, camera,
   duration, audio, seed, edit, and export.
3. Run the same bounded prompt and reference frame where terms allow.
4. Compare visual fit, continuity, instruction adherence, render time, failure
   rate, rights, and total cost.
5. Keep model-specific advice only when the current docs or test output supports
   it, and attach the source date.

If no model is callable and authorized, deliver prompts, reference-frame briefs,
and a manual test matrix. Do not claim that generation occurred.

---

## Common Prompt Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| "A person using our app" | Too vague, no visual detail | Describe the person, setting, lighting, camera |
| Including text/logos | Generated typography may not meet accuracy requirements | Add reviewed text in a verified editor |
| "Make it viral" | Not a visual instruction | Describe the visual style you want |
| Unbounded prompt detail | Important constraints can become hard to diagnose | Start concise, then add one tested constraint at a time |
| No camera direction | Uncontrolled camera behavior | Specify or test movement when the current model supports that control |
| "Realistic" alone | Not specific enough | "Photorealistic, natural lighting, shot on RED camera" |

---

## Prompting Workflow

1. **Reference first**: find a real video that looks like what you want
2. **Describe it**: break down: subject, action, camera, style, mood
3. **Generate a bounded comparison set**: same concept, one controlled variable
4. **Iterate on the selected result**: refine from recorded evidence
5. **Composite**: combine AI footage with programmatic text/overlays

---

## Aspect-Ratio Verification

Read current destination documentation and preview the authenticated composer
before choosing a ratio. The rows below are starting test candidates, not
current platform requirements:

| Placement hypothesis | Starting ratio candidate | Starting resolution candidate |
|----------------------|--------------------------|-------------------------------|
| Long-form video | 16:9 | 1920x1080 |
| Short-form full-screen | 9:16 | 1080x1920 |
| Feed placement | 1:1 or 4:5 | 1080x1080 or 1080x1350 |
| Website hero | Match the approved component | Match rendered display and performance budget |
| Professional feed | 16:9, 1:1, or another supported ratio | Verify in current composer |

---

## Cost Control

- Verify current pricing, included credits, failed-generation treatment, and
  commercial rights before generating.
- Set a run-level budget cap and maximum comparison count.
- Test lower-cost preview settings only when current docs say they preserve the
  decision-relevant characteristics.
- Test image-to-video against text-to-video; do not assume it is cheaper or
  better on the current model.
- Batch only when the account terms, cost model, and review capacity support it.
- Reuse footage only when source and derivative rights permit it.
