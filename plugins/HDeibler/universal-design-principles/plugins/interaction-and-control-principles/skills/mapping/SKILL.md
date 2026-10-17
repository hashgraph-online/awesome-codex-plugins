---
name: mapping
description: 'Apply the principle of Mapping — designing the relationship between controls and their effects so the connection between input and output is immediately obvious. Use when designing controls (knobs, switches, buttons, sliders, gestures), arranging them in space relative to what they affect, or diagnosing user confusion about which control does what. Strong mappings exploit physical analogies (up = more), spatial correspondence (the left burner control is on the left), and cultural conventions (red = stop). Poor mappings force the user to memorize arbitrary pairings, generating slips and errors that compound over time.'
---

# Mapping

> **Definition.** Mapping is the relationship between a control and the effect it produces. Good mapping makes the connection immediately apparent — by spatial position, shape, motion, or convention — so the user does not have to think, label, or memorize. Bad mapping requires the user to translate between control and effect, which is slow, error-prone, and quietly punishing.

The classic test of mapping is the four-burner stove. Four knobs in a row, four burners in a 2×2 grid. Which knob controls which burner? In a poorly mapped stove the answer requires labels (and, even with labels, half a second of squinting); in a well-mapped stove the knobs are arranged in a 2×2 grid that matches the burner layout, and you simply reach for the knob in the position of the burner you want.

The same problem appears in software a hundred times a day. The arrow keys move the cursor in the direction of the arrow — strong mapping. The "swap" button has two arrows curving in opposite directions — strong mapping. The "settings" gear icon has no inherent connection to settings — weak mapping, sustained only by convention. The number "3" next to a column header increases the column count by 3 — questionable mapping; better would be a stepper that visibly changes the column layout in real time.

## Why this matters

The cost of weak mapping is paid every single time the user reaches for a control. A user of a four-burner stove with bad mapping turns on the wrong burner perhaps once a month — usually when distracted, sometimes when something is on the burner and shouldn't be heated. This is the core observation that Don Norman built *The Design of Everyday Things* around: most "user error" is actually a design failure to make the mapping obvious. The user is not confused because they are stupid; the user is confused because the designer asked them to memorize an arbitrary pairing in a context where the cost of getting it wrong is real.

In digital interfaces, the punishment is subtler but constant. Every weak mapping costs a few hundred milliseconds of cognitive lookup ("which one was the save icon again?"), and a percentage of the time it costs an actual error: clicking the delete button when you meant to click archive, swiping the wrong way to dismiss, hitting the wrong toggle in a settings panel because the labels and the affected setting are not visually linked. These costs are paid millions of times across a product's user base, and they compound especially in high-stakes flows (cockpit controls, medical devices, financial transactions, legal forms) where a single mismapped action can be expensive or dangerous.

## The four mapping techniques

There are four ways to make a mapping obvious. They are roughly in order of strength.

**1. Spatial correspondence.** The control is positioned where the thing it affects is. Stove knobs in the same 2×2 grid as the burners. The volume slider on the right side of the screen, the mute button at the bottom of the screen near the audio waveform. In information design: a legend whose entries are positioned in the same vertical order as the data series on the chart, so the eye does not have to translate between key and data. This is the strongest form because it requires no learning at all — the user just looks at where the control is.

**2. Physical analogy.** The control's shape, motion, or behavior mimics a physical action whose meaning is universally understood. A volume slider goes up for louder; a brightness control goes right for brighter; a temperature dial goes clockwise for warmer. These mappings are not innate — they're cultural — but they are nearly universal in industrialized cultures, and breaking them generates immediate confusion. The mapping is strong because it exploits an embodied intuition.

**3. Visual signaling.** The control looks like the effect it produces, or the affected element is visually highlighted when the control is engaged. A button labeled "Bold" rendered in bold type. A color picker showing the actual color, not a name. A row of typeface samples letting you see what each font looks like before you pick it. The mapping is encoded in the rendering itself.

**4. Cultural convention.** Red = stop, green = go. The trash can = delete. The gear = settings. The magnifying glass = search. These are the weakest of the four, because they require prior learning and don't transfer across cultures or unfamiliar audiences. But they're cheap to deploy and, within a culture that recognizes them, they're effectively free. The risk is treating an unfamiliar convention as a known one — using a domain-specific glyph (the developer-tools icon, the database icon) and assuming the user will recognize it.

## Diagnosing a mapping problem

Three symptoms indicate a mapping problem. First, **the user pauses before reaching for the control.** They scan, hover, sometimes mouth the labels. If you watch a user use a feature and they hesitate at the moment of input, the mapping is weak. Second, **the wrong action is executed and the user is surprised.** Slips of this kind almost always trace back to mapping failures — the user reached for what their motor habit told them was correct, and the layout disagreed. Third, **labels are necessary.** Labels are an admission that the mapping isn't obvious. A control that needs a tooltip, a "what does this do?" link, or an onboarding tour to be understandable is a control whose mapping has failed. Labels are not bad — they're a useful safety net — but the more labels you need, the weaker the underlying mapping.

## When to apply this principle

You should think hardest about mapping at three moments. **When you design a new control.** Before you settle on an icon, a position, or a gesture, ask: what does the user expect this to do, and how can I make the answer immediate? **When you arrange multiple controls together.** A row of similar buttons, a settings panel, a chart with a legend, a remote with many buttons — the spatial arrangement should mirror the conceptual arrangement of what each control affects. **When you observe user errors or slow performance on a specific interaction.** If users repeatedly miss a button, click the wrong toggle, or swipe in the wrong direction, the mapping is the first place to look.

## When the principle backfires

Two failure modes are worth knowing.

**Forced spatial mapping in cramped layouts.** Sometimes the physical or screen real estate does not allow a true spatial correspondence — the four-burner stove with knobs along the front lacks the depth to lay them out in a 2×2 grid. Forcing the mapping by inventing fake spatial relationships (a tiny diagram next to each knob showing which burner it controls) is often worse than relying on labels, because the user has to interpret the diagram. Pick the strongest mapping that the form factor actually supports.

**Cultural convention assumed where it doesn't hold.** A globe icon for "language" is widely understood; a globe icon for "external link" is recognized by many but not all; a globe icon for "go to homepage" will confuse most users. When you reach for a convention, verify that your audience actually shares it. This matters especially for international products, accessibility audiences, and domain newcomers.

## Sub-skills in this cluster

- **mapping-natural** — Spatial correspondence and physical analogy. The strongest forms of mapping; how to recognize when your form factor supports them and when it doesn't. Includes the stove problem, vehicle controls, video editing timelines, and chart legends.
- **mapping-cultural** — Visual signaling and cultural convention. The weaker but more flexible forms; how to use icons, colors, and conventions without leaning on them past the point where users actually recognize them.

## Heuristic checklist

Before shipping any new control, ask the following. **Could a first-time user predict what this does without reading anything?** If no, can the mapping be strengthened? **Is the control's position related to the position of what it affects?** If not, is there a reason it can't be? **If you remove all labels, can the user still operate the interface?** They shouldn't have to — labels exist for a reason — but the answer tells you how much the mapping is doing on its own. **When users err, are the errors clustered around specific controls?** Those controls have weak mappings.

## Related principles

- **Affordance** — what a control suggests it can do (mapping picks up where affordance leaves off: affordance suggests the action is possible, mapping clarifies which target it affects).
- **Visibility** — whether the control is visible at all in the moment it's needed.
- **Proximity** — controls that affect the same thing should be near each other; this is a layout-level form of mapping.
- **Consistency** — once a mapping is established, applying it consistently elsewhere strengthens recognition.
- **Constraint** — physical and logical constraints that prevent the wrong control from being reached or activated when the mapping is weak.
- **Recognition Over Recall** — strong mappings let users recognize the right control rather than recall its label.

## See also

- `references/lineage.md` — historical origins, Norman's contribution, and HCI-research support.
- `mapping-natural/` — sub-skill on spatial and physical mappings.
- `mapping-cultural/` — sub-skill on conventional and signaling mappings.
