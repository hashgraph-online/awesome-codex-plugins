# Knowledge coverage

Coverage shows whether each declared workstream has enough navigation and ownership to support future work.

Declare stable workstreams in Project frontmatter:

```yaml
coverage_areas:
  - authentication
  - deployment
  - billing
```

Tag relevant notes with:

```yaml
workstreams:
  - authentication
owner: optional-name-or-team
```

The coverage helper reports, per area:

- number of notes;
- accepted decisions;
- current-state notes;
- notes with an owner;
- notes overdue for review;
- a navigation-oriented coverage state: `uncovered`, `thin`, or `covered`.

Do not use this as a staff performance metric. A low state means future contributors may lack navigable evidence; it does not imply poor project work.
