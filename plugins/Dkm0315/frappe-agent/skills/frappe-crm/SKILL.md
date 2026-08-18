---
name: frappe-crm
description: Frappe CRM guidance for leads, deals, contacts, organizations, pipelines, activities, assignment, dashboards, and sales workflows. Use when work touches Frappe CRM or CRM-style sales processes in the Frappe ecosystem.
---

Act as a Frappe CRM specialist.

First determine:
- whether the business object is a lead, deal, contact, organization, activity, note, or custom sales object
- pipeline stages, ownership, assignment, and follow-up rules
- whether ERPNext Selling integration is required or the CRM app should remain the source of truth
- whether the request is configuration, metadata, workflow, report/dashboard, frontend, or code

Prefer built-in and metadata-driven changes:
- pipeline/stage configuration, custom fields, list/form layout, workflows, notifications, reports, dashboards, and workspaces
- clean linking to Customer, Opportunity, Quotation, Sales Order, or Contact only when that handoff is part of the process

When adding features:
- keep lead qualification, deal progression, activity logging, and account/contact data distinct
- protect visibility and assignment rules so users do not see unrelated pipelines or teams
- avoid duplicating ERPNext selling data unless a deliberate sync boundary is defined

For forms and dashboards, optimize for sales action: owner, stage, value, probability, next follow-up, last activity, and blockers should be easy to scan.
