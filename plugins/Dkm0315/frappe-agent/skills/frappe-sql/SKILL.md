---
name: frappe-sql
description: Frappe-native SQL and ORM guidance for `frappe.db`, Query Builder, `tab{DocType}` tables, permission-sensitive queries, and raw SQL review. Use when writing or reviewing database access in Frappe.
---

Treat SQL and ORM decisions as first-class Frappe architecture choices.

Cover:
- `frappe.db.get_list`
- `frappe.db.get_all`
- `frappe.db.get_value`
- `frappe.db.exists`
- `frappe.qb`
- `frappe.db.sql`
- transaction boundaries
- permission implications

Rules:
- prefer Frappe-native APIs when they express the query clearly
- treat `get_all` and raw SQL as deliberate choices
- use correct `tab{DocType}` table naming when raw SQL is necessary
- flag brittle or permission-blind SQL
- distinguish reporting SQL from transactional logic

When reviewing code, explicitly state:
- why the chosen access layer is or is not appropriate
- whether permissions are respected or bypassed
- whether the query belongs in a report, service, patch, or controller

