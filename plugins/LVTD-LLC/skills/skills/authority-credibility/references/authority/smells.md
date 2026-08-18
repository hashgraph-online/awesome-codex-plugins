# Authority Smells

Use these anti-patterns during audits and rewrites.

## Credential drift

**What it is**: A credential from one domain is used to support claims in another.

**How to detect**:
- Ask what real fact supports the cue.
- Look for missing dates, scope, source, or user benefit.
- Check whether the user can reasonably say no.

**How to fix**:
- Remove unsupported claims.
- Add truthful evidence and scope.
- Rewrite the ask so the user keeps agency.

---

## Logo laundering

**What it is**: A logo implies endorsement when the relationship is only customer, investor, or press mention.

**How to detect**:
- Ask what real fact supports the cue.
- Look for missing dates, scope, source, or user benefit.
- Check whether the user can reasonably say no.

**How to fix**:
- Remove unsupported claims.
- Add truthful evidence and scope.
- Rewrite the ask so the user keeps agency.

---

## Visual authority without substance

**What it is**: Badges, uniforms, seals, or titles appear without verifiable backing.

**How to detect**:
- Ask what real fact supports the cue.
- Look for missing dates, scope, source, or user benefit.
- Check whether the user can reasonably say no.

**How to fix**:
- Remove unsupported claims.
- Add truthful evidence and scope.
- Rewrite the ask so the user keeps agency.

## Quick Detection Table

| Smell | Key Indicator |
| --- | --- |
| Credential drift | A credential from one domain is used to support claims in another. |
| Logo laundering | A logo implies endorsement when the relationship is only customer, investor, or press mention. |
| Visual authority without substance | Badges, uniforms, seals, or titles appear without verifiable backing. |
