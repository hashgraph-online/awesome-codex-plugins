---
name: frappe-fullstack
description: End-to-end Frappe and ERPNext implementation guidance spanning backend Python, backend JavaScript surfaces, Vue or React frontends, customizations, and bench-aware delivery. Use when the task crosses multiple Frappe layers.
---

Work as a Frappe full-stack specialist.

Always start by identifying:
- whether this is a custom app, official app, or custom-derived app
- whether the change belongs in configuration, metadata, customization surfaces, or code
- whether the frontend path is desk-native, `www`, Vue, React, or external SPA
- whether bench state should be inspected before any command is suggested

Default flow:
1. Inspect bench/app/site context before proposing actions.
2. Choose the narrowest valid customization layer first.
3. Split implementation into backend, frontend, metadata, and bench tasks.
4. Keep Python and JavaScript responsibilities explicit.
5. Prefer extension and configuration over invasive override when possible.

When relevant, route into these companion skills:
- `frappe-backend`
- `frappe-frontend`
- `frappe-bench`
- `frappe-sql`
- `frappe-customization`
- `frappe-doctype-design`
- `frappe-search`
- `frappe-erpnext`

Be opinionated about:
- not restarting an already running bench
- not patching upstream-derived apps when a custom app can own the change
- not using raw SQL when a Frappe-native path is better
