---
title: Layer-Based Grouping
impact: MEDIUM
tags: layer, backend, api, grouping
---

**Rule**: Group by technical layer. Common for backend/API projects where cross-cutting concerns span domains.

### Structure

```
src/
├── controllers/    # Request handling
├── services/       # Business logic
├── models/         # Data models
├── routes/         # Route definitions
├── middleware/      # Express/Fastify middleware
└── utils/          # Shared utilities
```

Use layer-based when the project is a focused API with clear horizontal layers. Switch to feature-based when the backend grows to span multiple distinct domains.
