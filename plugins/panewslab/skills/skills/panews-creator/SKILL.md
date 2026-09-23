---
name: panews-creator
description: >
  Create and manage articles on the PANews platform. All operations require a valid user session.
  Triggers: write and publish new articles, view / edit / delete drafts, revise and resubmit rejected articles,
  upload images, search tags, apply for a column, polish or review article content.
metadata:
  author: Seven Du
  version: "2026.09.23"
---

This is the PANews creator skill for contributors who need to write, edit, manage, and publish articles on the platform. Use it when the task involves authenticated creator workflows such as validating a session, managing drafts or submissions, uploading images, searching tags, applying for a column, or preparing an article for review.

It is best suited for real PANews publishing operations rather than generic writing help alone. The skill should guide the user through the platform workflow clearly and safely, especially when session validation, submission state, or destructive actions are involved.

**Session verification is required before any operation.**
If no session is available, guide the user to get `PA-User-Session` from browser DevTools -> Application -> Cookies.
On a 401 response, stop immediately and tell the user the session has expired and needs to be refreshed.

## Common User Phrases

- "Help me publish this article."
- "Upload this cover image and find tags for my draft."

## Capabilities

| Scenario | Trigger intent | Reference |
|----------|---------------|-----------|
| Publish a new article | I want to publish an article / help me submit | [workflow-publish](./references/workflow-publish.md) |
| Manage my articles | Status of my submissions / any rejections | [workflow-manage](./references/workflow-manage.md) |
| Revise and resubmit | Edit a draft / resubmit a rejected article | [workflow-revise](./references/workflow-revise.md) |
| Apply for a column | I don't have a column yet / want to start a column | [workflow-apply-column](./references/workflow-apply-column.md) |
| Upload an image | Upload this cover image / turn this local image into a usable asset URL | Use `upload-image` |
| Search tags | Find suitable tags / search PANews tags for this topic | Use `search-tags` |
| Polish an article | Help me improve this article / review it | [workflow-polish](./references/workflow-polish.md) |

## Language

`--lang` accepts standard locale strings (`zh`, `en`, `zh-TW`, `en-US`, `ja-JP`, etc.), automatically mapped to the nearest supported language; most read-style commands auto-detect the system locale if omitted.
For `create-article`, `--lang` indicates the **article content language** and is required. Pass the language the article is actually written in; this command does not auto-detect the locale.

## General principles

- On 401, stop immediately and prompt the user to refresh the session
- Require explicit confirmation before any delete operation
- Do not modify the user's article content or opinions unprompted

## Execution guards

- Use more freedom for low-risk tasks such as polishing copy, suggesting improvements, or helping the user prepare content before submission.
- Use strict procedure for high-risk creator actions:
  - Before any create, update, delete, submit, or column-application action, validate that a usable `PA-User-Session` is available.
  - On any 401 response, stop immediately and ask the user to refresh the session before continuing.
  - Before deletion, obtain explicit user confirmation for the exact target article.
  - When updating an article, change only the fields the user asked to modify.
  - Before moving an article to `PENDING`, make sure the user intends to submit it for review now.
  - Treat image upload and tag search as support steps for PANews publishing workflows, not as unrelated generic utilities.

## Scripts

- `scripts/cli.mjs`: unified entrypoint for PANews creator commands

```bash
node {Skills Directory}/panews-creator/scripts/cli.mjs <command> [options]
```

When unsure about parameters, check with `--help` first:

```bash
node {Skills Directory}/panews-creator/scripts/cli.mjs --help
node {Skills Directory}/panews-creator/scripts/cli.mjs <command> --help
```

Available commands:

```text
  validate-session    Validate session and list owned columns
     list-articles    List articles in a column
    create-article    Create an article in a column
    update-article    Update a DRAFT or REJECTED article
    delete-article    Delete a DRAFT or REJECTED article
      upload-image    Upload a local image and return CDN URL
       search-tags    Search tags by keyword
      apply-column    Submit a column application
```
