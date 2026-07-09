# Visual Docs Knowledge

Visuals can reduce cognitive load when they show relationships, flow, state, or responsibility more clearly than prose alone. They create maintenance and accessibility costs when used casually.

Source basis: *Docs for Developers*, Chapter 6, "Adding visual content."

## Visual Types

| Type | Best For |
|------|----------|
| Screenshot | Showing UI state, labels, placement, or visual confirmation |
| Boxes-and-arrows diagram | Showing entities and relationships |
| Flowchart | Showing decisions or ordered process flow |
| Swimlane | Showing process steps across actors, services, or teams |
| Video | Showing motion or timing that cannot be expressed well in text or static visuals |
| Text-only | Copyable commands, values, critical instructions, and details that change often |

## Quality Dimensions

| Dimension | Check |
|-----------|-------|
| Comprehension | The visual makes a specific idea easier to understand |
| Relevance | The visual supports nearby text and reader task |
| Accessibility | Non-visual readers can get equivalent information |
| Performance | Image size, format, and rendering cost are appropriate |
| Maintenance | Source files and update triggers are known |

## Common Misconceptions

- **Myth**: A screenshot makes instructions clearer by default.
  **Reality**: Screenshots can age quickly and hide copyable information.
- **Myth**: A bigger diagram is more complete.
  **Reality**: One idea per diagram is usually more useful.
- **Myth**: Video is the richest documentation format.
  **Reality**: Video is expensive to maintain and hard to scan.

## Rules And Checks

Use these rules when designing or reviewing visuals in developer documentation.

## Core Rules

1. **Define the visual's job** - Use a visual only when it helps comprehension, not decoration.
2. **Keep critical text copyable** - Commands, config, IDs, and error messages should not appear only inside images.
3. **Place visuals near the relevant text** - Introduce the visual before or beside the explanation it supports.
4. **Use one level of detail** - Split visuals when a diagram mixes user flow, architecture, API sequence, and UI state.
5. **Label consistently** - Use the same product terms, shapes, lines, and colors throughout a visual set.
6. **Avoid crossed or ambiguous connectors** - Relationship diagrams should not require decoding.
7. **Annotate sparingly** - Highlight the exact area that matters.
8. **Check accessibility** - Provide alt text, captions, transcript for video, color contrast, and non-color cues.
9. **Check performance** - Prefer efficient formats such as SVG for diagrams and compress screenshots.
10. **Preserve source files** - Store editable source and note update triggers.

## Visual Type Selection

| Reader Need | Prefer |
|-------------|--------|
| Locate a UI control | Screenshot with annotation |
| Understand components and relationships | Boxes-and-arrows |
| Follow decisions or branches | Flowchart |
| See responsibility across actors | Swimlane |
| Understand timing or motion | Video only if static content fails |

## Red Flags

- The visual is not referenced by surrounding text.
- The diagram has no clear starting point.
- Color is the only way to distinguish meaning.
- Screenshot labels are stale or cropped.
- The source file is missing, so future edits require recreating the visual.


## Examples And Patterns

Use these examples as decision patterns.

## Screenshot Decision

Scenario: The doc tells users to switch a dashboard from live mode to test mode.

Good visual choice:

- Use a focused screenshot only if the toggle is hard to locate.
- Annotate the toggle.
- Keep the exact instruction in body text.
- Add alt text that explains the relevant UI state.

Bad visual choice:

- A full-page dashboard screenshot with no annotation.
- Instructions embedded only in the screenshot.

## Diagram Type Decision

Scenario: Explain webhook delivery.

| Need | Visual |
|------|--------|
| Show app, API, queue, and user server relationships | Boxes-and-arrows diagram |
| Show request, retry, success, and failure path | Flowchart |
| Show which team owns each delivery step | Swimlane |

## Maintenance Note Pattern

```text
Source: docs/diagrams/webhook-delivery.excalidraw
Export: docs/assets/webhook-delivery.svg
Update trigger: webhook retry policy, dashboard label, or event schema changes
Owner: Developer docs
```
