# JavaScript UI Math Rules

Rules for applying javascript ui math in production front-end work.

Source: Chapter 2: Math basics for JavaScript; see `../source-map.md`.

## Core Rules

### 1. Use parentheses for intent

Do not rely on readers remembering precedence in UI logic.

### 2. Use ?? instead of || when zero is valid

Avoid replacing 0 with a default value by accident.

### 3. Compare floats with a tolerance

Do not expect decimal fractions such as 0.1 + 0.2 to be exact.

### 4. Normalize modulo for wrapping

Use a positive modulo helper when indexes may move backward.

### 5. Round only at display or boundary points

Keep internal calculations precise until output needs formatting.

### 6. Do not mix BigInt and Number arithmetic

Convert deliberately and only when safe.

## Guidelines

Less strict recommendations:

- Use `Number.isNaN()` instead of global `isNaN()` for strict checks.
- Use `Number.isFinite()` before mapping values into CSS or DOM state.
- Use `Intl.NumberFormat` for user-facing formatted numbers.
- Use deterministic pseudo-randomness for tests and replayable animation demos.

## Exceptions

When these rules may be relaxed:

- **Cryptographic randomness**: Use Web Crypto APIs, not Math.random().
- **Currency and billing**: Use integer minor units or a decimal library rather than binary floats.

## Quick Reference

| Rule | Summary |
|------|---------|
| Use parentheses for intent | Do not rely on readers remembering precedence in UI logic. |
| Use ?? instead of || when zero is valid | Avoid replacing 0 with a default value by accident. |
| Compare floats with a tolerance | Do not expect decimal fractions such as 0.1 + 0.2 to be exact. |
| Normalize modulo for wrapping | Use a positive modulo helper when indexes may move backward. |
| Round only at display or boundary points | Keep internal calculations precise until output needs formatting. |
| Do not mix BigInt and Number arithmetic | Convert deliberately and only when safe. |
