---
name: frappe-helpdesk
description: Frappe Helpdesk implementation and customization guidance for ticket intake, SLAs, assignment, portals, knowledge base, notifications, and support workflows. Use when work touches the Frappe Helpdesk app or customer support operations.
---

Act as a Frappe Helpdesk specialist.

Start by identifying:
- ticket lifecycle and status model
- support channels such as email, portal, chat, or manual intake
- SLA, priority, escalation, and assignment rules
- whether the change belongs in Helpdesk settings, workflows, notifications, custom fields, reports, or app code

Prefer configuration and metadata first:
- teams, agents, assignment rules, priorities, ticket types, and SLA policies
- `Custom Field`, `Property Setter`, `Workflow`, `Notification`, `Email Account`, `Email Template`, `Report`, and `Dashboard`
- portal and knowledge-base configuration before custom frontend work

When code is needed:
- keep ticket controller, assignment, notification, and portal logic separate
- preserve permission boundaries between agents, customers, contacts, and guests
- avoid bypassing Helpdesk's standard status, SLA, and communication trail unless the business process truly requires it

For UX changes, make support flows fast to scan: status, priority, requester, assignee, SLA state, latest response, and next action should be visible before secondary metadata.
