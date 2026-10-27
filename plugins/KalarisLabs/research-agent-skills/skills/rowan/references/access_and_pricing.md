# Access, Pricing, and Credits

Free-tier access, how credits are consumed per workflow, and typical cost estimates.

## Access and pricing model

Rowan uses a credit-based usage model. All users, including free-tier users, can create API keys and use the Python API.

### Free-tier access

- Access to all Rowan core workflows
- 20 credits per week
- 500 signup credits

### Pricing and credit consumption

Credits are consumed according to compute type:

- **CPU**: 1 credit per minute
- **GPU**: 3 credits per minute
- **H100/H200 GPU**: 7 credits per minute

Purchased credits are priced per credit and remain valid for up to one year from purchase.

### Typical cost estimates

| Workflow | Typical Runtime | Estimated Credits | Notes |
|----------|----------------|-------------------|-------|
| Descriptors | <1 min | 0.5–2 | Lightweight, good for triage |
| pKa (single transition) | 2–5 min | 2–5 | Depends on molecule size |
| MacropKa (pH 0–14) | 5–15 min | 5–15 | Broader sampling, higher cost |
| Conformer search | 3–10 min | 3–10 | Ensemble quality matters |
| Tautomer search | 2–5 min | 2–5 | Heterocyclic systems |
| Docking (single ligand) | 5–20 min | 5–20 | Depends on pocket size, refinement |
| Analogue docking series (10–50 ligands) | 30–120 min | 30–100+ | Shared reference frame |
| MSA generation | 5–30 min | 5–30 | Sequence length dependent |
| Protein-ligand cofolding | 15–60 min | 20–50+ | AI structure prediction, GPU-heavy |
