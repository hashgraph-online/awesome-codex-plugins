---
name: control-power-vs-simplicity
description: 'Apply layered control — designing interfaces that serve novice and expert users in the same product without forcing one audience into the other''s interface. Use when building products that span experience levels (most consumer software, most professional tools used occasionally), choosing between "simple by default" and "powerful by default," or deciding what to expose vs. hide behind progressive disclosure. The skill is creating a default surface that suffices for novices and a depth surface that doesn''t intimidate them but is fully present for experts.'
---

# Control — power vs. simplicity

The most-cited tension in control design: power users want depth, novices want simplicity, and most products have both kinds of users. The naive answers ("just make it simple," "just make it powerful") both fail. Simple products lose their experts to deeper alternatives; powerful products lose their novices before they ever discover the depth.

The successful pattern across decades of product design is *layering*: a simple default surface that handles the common cases, with depth available but not promoted. A novice can use the product productively without ever encountering the advanced controls. An expert can configure, customize, and extend without leaving the application.

## The core architecture

Layered control rests on a few moves applied consistently.

**Identify the 80/20.** What can a novice do that handles 80% of their use? That's the default surface. What does an expert need that handles the remaining 20% and the long-tail edge cases? That's the depth surface.

**Make the default surface complete for the novice case.** The novice should not feel that they're missing anything important. The default surface should be a complete tool for the use case it serves, not a stripped-down preview of the "real" tool.

**Make the depth surface accessible but not promoted.** The advanced controls are reachable in 1–2 actions (a "more options" button, a settings panel, an advanced mode toggle), but they don't appear in the default field of view. The novice doesn't have to dismiss them; they aren't there.

**Make the depth surface complete for the expert case.** Once the expert has unlocked depth, they should find the full set of capabilities the product offers, not a half-step that requires them to leave the product for serious work. Half-depth interfaces lose experts to fully-deep alternatives.

**Maintain consistent vocabulary across surfaces.** The same concepts should have the same names whether the user is in default or advanced mode. A novice who learns the product's vocabulary in default mode shouldn't have to relearn anything to graduate into advanced mode.

## The four common architectures

There are roughly four architectural patterns for layering control. They differ in where the depth lives and how the user reaches it.

**1. Progressive disclosure within the same view.** A "Show advanced" button or expandable section reveals additional controls inline. The novice never opens it; the expert always opens it. This works well when the depth controls are conceptually related to the default controls and benefit from being visually adjacent.

Example: a flight-booking interface where the basic search is "from / to / dates / passengers" and a "more options" expansion adds cabin class, refundable / non-refundable, multi-city, layover preferences. The expert opens the expansion and uses it; the novice never touches it.

**2. Mode toggle (basic / advanced).** A clearly-labeled mode switch changes the entire interface from a simple to a complex layout. The user picks their mode and the product follows.

Example: a photo editor with a "Quick" mode (auto-enhance, basic crop) and a "Pro" mode (curves, layers, masks). The user switches modes based on the task.

This works when the two modes are genuinely different workflows, not just more or fewer controls. It fails when users expect all the basic capabilities to also exist in pro mode and find some missing.

**3. Settings panel for configuration depth.** The default UI is the simple workflow; deep customization (keybindings, default values, plugin configuration) lives in a settings panel reachable through a menu. Users only visit settings when they want to change behavior.

Example: VS Code, Slack, Notion. The default editing surface is approachable; the settings panel is vast and contains depth most users never see.

This works for any product where the customization is configurational (set once, takes effect always) rather than per-task.

**4. Power-user shortcuts.** The visual UI is simple; expert speed is provided through keyboard shortcuts, command palettes, or programmatic interfaces. Novices use the UI; experts use the shortcuts.

Example: command palette (Cmd-K) interfaces in modern productivity apps. Vim and Emacs in the extreme.

This works when expert speed depends on minimizing pointing and clicking; the visual UI doesn't have to grow more complex to serve experts because experts are bypassing it.

## Choosing the right architecture

The choice depends on the nature of the depth.

- **Depth is in additional task parameters.** Use progressive disclosure within the view. The expert needs occasional access to the parameters; they don't want to leave the task.
- **Depth is in different workflows.** Use a mode toggle. The expert is doing a fundamentally different kind of work and benefits from a different layout.
- **Depth is in configuration that affects future behavior.** Use a settings panel. Set it once and forget it.
- **Depth is in speed of common operations.** Use power-user shortcuts. The expert just wants to do the same things faster.

A single product can use multiple architectures for different kinds of depth. Lightroom has progressive disclosure (Basic vs. Detail panels), settings (Catalog preferences), and power-user shortcuts (keyboard shortcuts for nearly every action) all at once.

## Worked examples

### A todo app

The novice surface: a list, a "+ add task" button, a checkbox to complete. That's it.

The first depth layer: due dates, priorities, projects. Available via a "..." menu on each task or an inline keyboard shortcut.

The second depth layer: filters, recurring rules, custom views, integrations. Available via a settings panel and a query language.

A novice using the app for personal task management never encounters any depth. An expert managing complex multi-project work uses all the depth and probably writes custom queries.

The failure mode: putting due-date pickers, priority selectors, and project assignments inline on every task. The novice sees a cluttered interface and either ignores the extra fields (rendering them clutter without function) or feels intimidated. The depth should be reachable but invisible until requested.

### A spreadsheet

The novice surface: type values into cells, do basic sums.

The first depth: formulas, cell references, basic chart types.

The second depth: pivot tables, named ranges, conditional formatting, macros.

The third depth: scripting (Apps Script, VBA), custom functions.

Spreadsheets are the canonical example of a product with vast depth that novices use productively without ever encountering most of it. The architecture is mostly progressive disclosure (more advanced features are in less prominent menus) and power-user shortcuts (formulas are typed, scripts are written).

### A trading platform vs. a consumer trading app

These are not layered; they're different products. A retail trading app and a professional trading platform serve audiences too different to be combined in a single interface. The retail app is "buy / sell, dollar amount, confirm." The professional platform is the full order-type taxonomy, routing options, and live order books.

This is the boundary case for layering: when the gap between novice and expert is too wide, build separate products. Trying to bridge the gap with a layered single product usually serves neither audience well.

The signal that you've reached this boundary: the simple-mode users complain about complexity even though they don't use the depth, and the expert-mode users complain about workarounds for things that should be primary actions.

### A search interface

Default: a single text box.

Depth (within the same view): a "filters" panel that opens to the side or below, with date, source, type, and other filters.

Power-user depth: a query syntax (`from:alice after:2023-01-01 -spam`) that lets experts express complex queries inline.

Three architectures coexisting. The novice uses the text box. The intermediate user opens the filters panel. The expert uses the query syntax. All three audiences are served without forcing any of them through the others' interface.

### Configuration in a developer tool

The default UI: sensible defaults, basic settings.

Settings panel depth: extensive customization options across categories (editor behavior, keybindings, themes, plugin management, language-server configuration).

Configuration-as-code depth: a settings JSON file (or YAML, or Lua script) that the user can edit directly to express things the settings UI doesn't support.

Plugin depth: an extension API that lets the user write code that extends the tool itself.

VS Code is the obvious example; the same pattern appears in JetBrains products, Sublime, and many others. Each layer of depth serves a more committed user. The vast majority of users stop at the settings panel; a small minority use the JSON; an even smaller minority writes plugins. All are served by the same product.

## Anti-patterns

**The "feature parity" trap.** A simple-mode UI that promises to have all the same features as the advanced mode, just with a friendlier face. Inevitably, some features don't fit the simpler architecture and have to be omitted, and users discover this and feel cheated. Better to be honest: simple mode handles the common cases; the depth is in advanced mode.

**The "settings sprawl" trap.** A settings panel that has accumulated every option ever requested by anyone, with no organization. Settings become unfindable. The expert who needs to change one thing spends fifteen minutes looking for it. Organize settings into a coherent taxonomy, and prune options that no one actually uses.

**The "everything in one screen" trap.** Trying to serve novices and experts with the same default view by including everything but visually demoting the advanced bits. Novices still see the visual noise; experts still have to wade past the basic controls. Pick one audience for the default and serve the other through a deliberate mechanism.

**The "tutorial as substitute for design" trap.** A complex default UI accompanied by extensive onboarding to teach the novice how to use it. The onboarding works for the first session and is gone after that; the complex UI persists. Better to make the default simple and let depth be discovered as users mature.

**The "depth that doesn't actually go deep" trap.** An advanced mode that adds a few extra options but is still missing the things a real expert needs. Experts open it, see that it doesn't go far enough, and leave for tools that do. If you commit to serving experts, the depth has to be real.

## Heuristic checklist

Before settling on the control architecture, ask: **Who are my actual audiences, and how different are their needs?** If very different, separate products may be better than layered. **What is the 80/20 of operations?** That's the default surface. **What does an expert genuinely need that the novice doesn't?** That's the depth. **Can a novice complete their core tasks without encountering any depth?** If not, the default surface is too cluttered. **Can an expert reach all needed depth in 1–2 actions?** If not, the depth is buried too far. **Does vocabulary stay consistent across surfaces?** If not, users have to relearn at each layer.

## Related sub-skills

- `control` — parent principle on the level of authority delegated to the user.
- `control-locus` — sibling skill on the perceived agency dimension of control.
- `progressive-disclosure` — the structural mechanism that implements layered control within views.
- `80-20-rule` — the empirical observation that justifies the architectural pattern.
- `recognition-over-recall` — power-user shortcuts trade recognition (visible UI) for recall (memorized commands); pick deliberately.

## See also

- `references/layering-patterns.md` — patterns for specific kinds of products and depth.
