---
name: frappe-customization
description: Frappe customization-surface guidance covering Custom Field, Property Setter, Client Script, Server Script, Workspace, Web Page, Page, Print Format, Report, Dashboard, Workflow, Role, Notification, Webhook, and related builder/admin DocTypes. Use when choosing or changing Frappe customization layers.
---

Choose the right Frappe customization surface before suggesting code.

Check these surfaces first when relevant:
- `Custom Field`
- `Property Setter`
- `Client Script`
- `Server Script`
- `Workspace`
- `Web Page`
- `Page`
- `Print Format`
- `Report`
- `Dashboard`
- `Dashboard Chart`
- `Number Card`
- `Web Form`
- `Workflow`
- `Role`
- `Notification`
- `Assignment Rule`
- `Webhook`
- `Auto Repeat`
- `Email Template`
- `Letter Head`
- `Print Style`

Preferred decision ladder:
1. built-in configuration
2. metadata/admin DocType customization
3. page/workspace/report/dashboard/print/web surfaces
4. hooks and custom app code
5. changes inside a custom-derived app only when necessary

Explicitly call out when a request should use `Custom Field` rather than editing a DocType JSON file directly.

When creating or redesigning a DocType, also apply `frappe-doctype-design` so fields, tabs, sections, columns, and required flags are chosen for a clean human workflow instead of a flat field dump.
