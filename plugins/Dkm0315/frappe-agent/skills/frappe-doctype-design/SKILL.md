---
name: frappe-doctype-design
description: Frappe DocType creation and form UX guidance. Use when creating, reviewing, or redesigning DocTypes, including field choice, tabs, sections, columns, required fields, naming, child tables, and form usability.
---

Design every DocType as a human-facing form, not a flat database table.

Before adding fields, identify:
- the DocType's purpose and primary user
- the real business process or lifecycle it supports
- the relationships, status, reporting, and search needs
- whether it is master data, a transaction, a child table, or a configuration DocType

Field discipline:
- Add only fields that are required for identity, workflow, relationships, decisions, audit, reporting, or search.
- Do not add speculative, vanity, duplicate, or generic fields unless the use case clearly needs them.
- Make required fields truly required, not merely convenient.
- Use child tables only for real one-to-many repeating data.
- Prefer human-readable labels and stable snake_case fieldnames.

Form layout:
- Do not dump all fields into one tab or one section.
- Use `Tab Break` for major mental models only when the form has enough fields to justify tabs.
- Use `Section Break` for logical groups inside a tab.
- Use `Column Break` to create balanced, scan-friendly rows.
- Put the title, status, primary links, and most common required inputs first.
- Put advanced, rare, admin, or integration fields later, and fold them when appropriate.
- Avoid empty tabs, thin sections, and layout breaks that exist only for decoration.

Useful tab patterns include:
- Overview for identity, status, and primary summary fields
- Details for the main business data
- People or Parties for owners, customers, suppliers, employees, or contacts
- Schedule for dates, timelines, reminders, or recurrence
- Finance for amounts, accounts, taxes, or pricing
- Settings for infrequent configuration
- Activity or Audit for comments, references, or system-facing traceability

When proposing or creating a DocType, present the layout grouped by tab and section, and explain why each group exists. If a requested field does not belong, call it out and omit it unless the user confirms the need.
