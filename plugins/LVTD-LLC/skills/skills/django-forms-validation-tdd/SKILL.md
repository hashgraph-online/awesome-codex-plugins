---
name: django-forms-validation-tdd
description: "Test-drive Django validation across model constraints, forms, ModelForms, views, template errors, duplicate handling, and redirects. Use when adding or refactoring Django forms, surfacing validation errors, deciding model-vs-form-vs-view responsibility, or preventing invalid input from being saved."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Forms Validation TDD
  category: Django
  tags: django,tdd,forms,validation,testing
---

# Django Forms Validation TDD

Use this skill to place validation tests at the layer that owns the rule, then prove the user-facing error path still works. Django validation often crosses model, form, view, and template boundaries; keep those responsibilities explicit.

## Source Traceability

Primary source: Harry Percival, *Test-Driven Development with Python*, 3rd ed. Guidance is transformed and paraphrased from chapters 14-16 and Appendix A, especially model constraints, form validation, ModelForm tradeoffs, view-level error surfacing, and duplicate item handling.

## Workflow

1. Classify the validation rule.
   - Data integrity belongs near the model or database constraint.
   - User input shape and presentation belong in a form.
   - Request branching and redirects belong in the view.
   - Error rendering belongs in the template.

2. Write the lowest useful failing test.
   - Model constraint or validation test for persistence rules.
   - Form test for field errors, cleaning, and save behavior.
   - View test for HTTP status, redirect, template, and invalid-save prevention.
   - Functional test only for a critical user journey.

3. Prove invalid data is not persisted.
   - Check both the error response and database state when the risk is saving bad input.
   - For uniqueness, cover duplicate behavior at the level that actually enforces it.

4. Refactor toward the right boundary.
   - Move validation from views to forms when the view is parsing form details.
   - Move integrity rules to constraints when the database must protect them.
   - Keep presentation logic in templates unless Python code clearly owns it.

Read [validation-patterns.md](references/validation-patterns.md) for layer choices and common Django edge cases.

## Decision Rules

- If the rule must hold outside HTTP, test it below the view.
- If `save()` can bypass validation, test the path that actually runs validation or enforce the rule with constraints.
- If a ModelForm couples the UI to unwanted model details, use a plain form or customize fields deliberately.
- If a refactor changes field names, IDs, or templates, keep one user-facing check for the rendered contract.
- If duplicate handling depends on the database, include the database-level behavior in coverage.

## Guardrails

- Do not rely only on Selenium for validation cases.
- Do not test every HTML string when form errors can be inspected directly.
- Do not assume Django model validation runs automatically on every save.
- Do not swallow `IntegrityError` without a user-facing path and a test.

## Verification

Before finishing, record:

- Rule ownership by layer.
- Tests added or updated at model/form/view/browser level.
- Invalid-save prevention evidence where relevant.
- Focused Django test command and result.
