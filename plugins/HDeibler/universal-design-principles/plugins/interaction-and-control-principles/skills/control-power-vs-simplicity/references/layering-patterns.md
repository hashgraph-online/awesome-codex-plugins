# Layered control — patterns by product category

Specific architectural patterns for layering simple and advanced controls, organized by the kind of product or feature being designed.

## Pattern: collapsible advanced section

The default view shows the basic fields; an "Advanced" section toggles open to reveal additional options. The depth is inline but hidden until requested.

Use when: depth is in additional task parameters that a few users will want, conceptually related to the basic task.

Examples: flight booking advanced filters, signup forms with optional fields, configuration dialogs with "Show advanced settings."

Pitfalls: an Advanced section that's so minimal it doesn't justify the toggle (just include the fields, or remove them); an Advanced section that becomes the universal dumping ground and contains too much for a single disclosure.

## Pattern: tabbed interfaces with depth-by-tab

The default surface is a primary tab; secondary tabs hold depth. Users only visit secondary tabs when they need them.

Use when: the depth is in conceptually distinct categories of work that benefit from being separated.

Examples: a product page with tabs for Overview, Specs, Reviews, Q&A. A settings panel with tabs for Account, Notifications, Privacy, Integrations.

Pitfalls: too many tabs (more than 5–6 starts to overflow); important features hidden in tabs that users don't expect to contain them.

## Pattern: drill-in for depth

The default surface is a list; clicking an item drills into a detail view that contains the depth. The list is simple; the detail is rich.

Use when: each item has many properties that aren't all relevant in the list view.

Examples: email inbox (list of emails; click to read full email with all metadata, attachments, and reply controls). File manager (list of files; click for detailed properties).

Pitfalls: drilling in is a navigation step that breaks flow; if users frequently need depth on multiple items, consider showing it inline or in a sidebar.

## Pattern: split view with primary + detail

The default is a list on the left; selecting an item shows its detail on the right. The user stays in context but sees depth for the selected item.

Use when: users need to scan items and dive into details without navigating away from the list.

Examples: email clients (list + reading pane). Settings panels (categories + detail). File managers (list + preview).

Pitfalls: requires enough screen real estate; doesn't translate well to mobile (where it usually becomes drill-in).

## Pattern: contextual toolbar

The default UI is the main canvas; a toolbar appears with controls relevant to the current selection or mode. Depth is contextual to what the user is doing right now.

Use when: depth is operation-specific and only relevant in certain contexts.

Examples: text editors (formatting toolbar for selected text). Image editors (selection-tool options bar). Diagramming tools (shape-property panel for selected shape).

Pitfalls: toolbars can become cluttered if every operation adds controls; the user can lose track of where the toolbar is when selection changes.

## Pattern: command palette

The visual UI is simple; a command palette (typically Cmd-K or Ctrl-K) provides a searchable list of every action the user can take. Experts use the palette; novices use the visual UI.

Use when: depth is in many specific actions that don't all need visual real estate.

Examples: VS Code, Linear, Notion, Slack, modern terminal applications.

Pitfalls: novices don't know the palette exists; the action vocabulary needs to be consistent and searchable; some actions need parameters and a palette doesn't gracefully handle them.

## Pattern: keyboard shortcuts

Shortcuts for common actions, optionally hidden behind tooltips. Experts learn and use them; novices use the menu.

Use when: speed of common operations matters and the user base will get value from learning shortcuts.

Examples: every productivity tool has them. The well-designed ones make shortcuts discoverable in tooltips and menus.

Pitfalls: shortcuts that conflict with system or browser shortcuts; inconsistent shortcuts across modes or contexts; shortcuts that are too clever to remember.

## Pattern: settings panel for configuration

Persistent configuration lives in a dedicated settings UI. Users visit it to change behavior, then return to the main UI.

Use when: the configuration affects future behavior of the product (theme, default values, feature toggles, integrations).

Examples: every desktop application; most modern web apps.

Pitfalls: settings sprawl (too many options, no organization); settings that should be in-context (like a per-document setting that's actually in global preferences); settings the user can't predict the effect of.

## Pattern: configuration as code

Power users configure the product by editing a text file (JSON, YAML, Lua, etc.) rather than (or in addition to) using a settings UI.

Use when: the audience includes developers who prefer programmatic control, or the configuration is too rich for a UI.

Examples: VS Code's settings.json, dotfile-driven Unix tools, Neovim/Emacs configuration.

Pitfalls: requires the user to learn the schema; errors are hard to surface; the UI version of settings can drift from the file version.

## Pattern: extension/plugin API

The product is extensible by code the user (or a third party) writes. Maximum depth, but requires programming.

Use when: the audience is developer-adjacent and the use cases extend beyond what the core product can anticipate.

Examples: VS Code extensions, Figma plugins, Notion's API, browser extensions, Slack apps.

Pitfalls: the API surface needs to be stable; bad plugins can damage trust in the product; discovery and quality control of the plugin marketplace is its own design problem.

## Pattern: separate products for separate audiences

When the gap between novice and expert is too large, build different products. The novice product is approachable; the expert product is powerful. They share concepts but not interfaces.

Use when: the audiences have fundamentally different workflows, not just different volumes of the same workflow.

Examples: a consumer trading app vs. a professional trading platform. A consumer photo organizer vs. a professional photo editor. A consumer calendar vs. a professional scheduling system.

Pitfalls: requires building and maintaining two products; users may want to graduate from one to the other and find the migration painful.

## Anti-patterns

**The "more options" link that goes nowhere useful.** A button labeled "Advanced settings" or "More options" that, when clicked, reveals options no one actually wants. Better to delete the link than to make users curious about it.

**The mode toggle that confuses everyone.** A "Basic / Advanced" toggle in a product where the difference between modes isn't obvious. Users flip back and forth trying to find features. Either the modes should be sharply differentiated and clearly labeled, or the depth should be unified.

**Settings as the universal answer.** Every option becomes a setting. The settings panel grows uncontrollably. Users can't find anything. Resist the urge to make every behavior configurable; pick sensible defaults and let users live with them.

**Power users as the design target.** Building primarily for the most committed users. Leads to interfaces that intimidate or alienate the larger novice audience. Power users are loud and articulate, but they're usually a small fraction of the user base.

**Novices as the design target while alienating power users.** The opposite failure: aggressively simplifying, removing features, hiding depth so successfully that experts can't find it. Power users churn to deeper alternatives, and the product loses its credibility.

## Decision framework

When choosing an architecture, ask:

1. **Is the depth conceptually related to the basic task?** If yes, progressive disclosure within view.
2. **Is the depth about a different kind of work?** If yes, mode toggle or separate product.
3. **Is the depth about configuration?** If yes, settings panel.
4. **Is the depth about speed of common operations?** If yes, keyboard shortcuts and command palette.
5. **Is the depth about extending the product?** If yes, plugin/API surface.

Most successful products combine multiple architectures. Don't think you have to pick one — pick the right one for each kind of depth.

## Cross-reference

For the parent principle on calibrating control to the user, see `control`. For the structural mechanism within views, see `progressive-disclosure`.
