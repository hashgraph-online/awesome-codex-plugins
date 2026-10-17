---
name: frappe-frontend
description: Frappe frontend guidance for Vue and React, including desk pages, `www` pages, `frappe-ui`, Doppio-style frontends, client scripts, and external SPA integrations. Use when building or reviewing Frappe UI work.
---

Treat Frappe frontend work as a React-or-Vue decision, not a generic browser task.

Support:
- desk-native pages
- `www` pages
- `Web Page`
- `Workspace`
- `Client Script`
- Vue with `frappe-ui`
- Doppio-generated app patterns
- React SDK and external SPA patterns

Decide first:
- desk-native vs website/public vs external SPA
- Vue vs React
- metadata/configuration surface vs code surface

Prefer:
- Vue when the app is already using `frappe-ui` or desk-native Vue patterns
- React when the project is already React-based or clearly external-SPA oriented

Do not flatten everything into the same UI recommendation.

