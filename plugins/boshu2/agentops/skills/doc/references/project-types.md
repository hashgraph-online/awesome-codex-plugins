# Project Type Detection

Score-based classification into CODING, INFORMATIONAL, or OPS.

## CODING Signals

| Signal | Weight | Detection |
|--------|--------|-----------|
| `services/` directory | +3 | `[[ -d services ]]` |
| `src/` directory | +2 | `[[ -d src ]]` |
| `pyproject.toml` or `package.json` | +2 | Config file exists |
| `docs/code-map/` directory | +3 | Code-map docs exist |
| >50 Python/TypeScript files | +2 | File count |
| FastAPI/Express routes | +2 | `@app.get`, `router.` patterns |

**Threshold**: Score >= 5 = Likely CODING repo

---

## INFORMATIONAL Signals

| Signal | Weight | Detection |
|--------|--------|-----------|
| `docs/corpus/` directory | +3 | Knowledge corpus |
| `docs/standards/` directory | +2 | Standards docs |
| >100 markdown files | +3 | High doc count |
| No `services/` or `src/` | +2 | Not a code repo |
| Diataxis structure | +2 | `tutorials/`, `how-to/`, `reference/`, `explanation/` |

**Threshold**: Score >= 5 = Likely INFORMATIONAL repo

---

## OPS Signals

| Signal | Weight | Detection |
|--------|--------|-----------|
| `charts/` directory | +3 | Helm charts |
| `apps/` or `applications/` | +2 | ArgoCD apps |
| >5 `values.yaml` files | +3 | Multi-environment Helm |
| `config.env` files | +2 | Config rendering |
| ArgoCD manifests | +2 | `Application` kind |

**Threshold**: Score >= 5 = Likely OPS repo

---

## Tie-Breaking

When scores are equal: **CODING > OPS > INFORMATIONAL**

Rationale: Code repos need more precise docs, ops is next most critical.

---

## Type-Specific Behaviors

| Type | `/doc all` | `/doc discover` | `/doc coverage` |
|------|------------|-----------------|-----------------|
| CODING | Generate code-maps | Find services, endpoints | Entity coverage |
| INFORMATIONAL | Validate all docs | Find corpus sections | Link validation |
| OPS | Generate Helm docs | Find charts, configs | Values coverage |
