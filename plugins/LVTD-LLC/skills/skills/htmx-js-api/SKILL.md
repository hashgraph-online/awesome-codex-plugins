---
name: htmx-js-api
description: Use the htmx JavaScript API for imperative integration in server-rendered apps. Use when calling htmx.ajax, htmx.process, htmx.trigger, htmx.on, htmx.off, htmx.onLoad, htmx.find, htmx.findAll, htmx.closest, htmx.addClass, htmx.removeClass, htmx.toggleClass, htmx.takeClass, configuring htmx.config, logging htmx events, or integrating non-htmx JavaScript with swapped content.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: htmx JS API
  category: Frontend
  tags: htmx,javascript,api,frontend,events
---

# htmx JS API

Use this skill when declarative attributes are not enough. Prefer attributes first; reach for the JavaScript API to integrate with third-party widgets, dynamically injected markup, instrumentation, or programmatic request flows.

## Decision Rule

Use htmx attributes when the behavior is visible in the HTML and tied to one element. Use the JS API when:

- markup is inserted by non-htmx code and needs htmx processing;
- an external library needs to trigger an htmx request or event;
- event listeners must be registered centrally;
- debugging requires htmx logging;
- configuration must be set once during startup.

## Startup Configuration

Set global config once before relying on htmx behavior. Common examples:

- history behavior;
- default swap style or delay when project-wide;
- request timeout;
- scroll/focus behavior;
- security-sensitive options reviewed with `htmx-security`.

Keep config close to where htmx is loaded so there is one source of truth.

## DOM Helpers

Use htmx DOM helpers for concise integration code:

| Need | Methods |
| --- | --- |
| Find one element | `htmx.find`, `htmx.closest` |
| Find many elements | `htmx.findAll` |
| Remove an element | `htmx.remove` |
| Add a class | `htmx.addClass` |
| Remove a class | `htmx.removeClass` |
| Toggle a class | `htmx.toggleClass` |
| Make one element selected | `htmx.takeClass` |

Do not use helper calls to hide complex UI state that belongs in a component or server response.

## Events

- Use `htmx.on` for delegated or global listeners.
- Use `htmx.off` when unregistering listeners from code that can mount/unmount.
- Use `htmx.trigger` to bridge plain JavaScript events into htmx behavior.
- Use `htmx.onLoad` for behavior that must run on newly loaded htmx content.
- Prefer custom domain events for product interactions.

Example:

```js
htmx.on("saved", function (event) {
  console.info("Saved", event.detail);
});

htmx.trigger("#results", "filters:changed");
```

## Programmatic Requests

Use `htmx.ajax` when code needs to initiate an htmx request while preserving htmx swap semantics.

```js
htmx.ajax("GET", "/notifications", {
  target: "#notifications",
  swap: "innerHTML"
});
```

Before using `htmx.ajax`, ask whether a real link, button, or form with htmx attributes would be clearer and more accessible.

## Processing Dynamic Markup

Use `htmx.process(element)` after non-htmx code injects markup that contains htmx attributes.

```js
const panel = document.querySelector("#panel");
panel.innerHTML = htmlFromTrustedSource;
htmx.process(panel);
```

Only process trusted markup. If markup includes user content, review sanitization with `htmx-security` before insertion.

## Logging And Debugging

- Use `htmx.logAll()` temporarily while diagnosing event/request behavior.
- Use `htmx.logNone()` after debugging.
- Use a custom `htmx.logger` for structured local diagnostics.
- Remove noisy logging before shipping unless the project has a deliberate debug mode.

## Extensions And Transports

Use extension APIs only when a documented htmx extension or project-specific integration requires it. For WebSocket and SSE work, prefer `htmx-realtime` for transport design before writing extension code.

## Avoid

- Do not reimplement htmx with `fetch()` plus `innerHTML`.
- Do not process untrusted HTML.
- Do not bind duplicate event listeners every time a fragment loads.
- Do not use imperative requests just to avoid writing a small form or link.
- Do not change global `htmx.config` from feature code after the app has started.
