# Frontend Math Foundations Rules

Rules for applying frontend math foundations in production front-end work.

Source: Chapter 1: Web dev math fundamentals; see `../source-map.md`.

## Core Rules

### 1. Name the unknown

State what value you are solving for before choosing a formula.

### 2. Preserve units through calculations

Do not mix lengths, angles, ratios, and counts without conversion.

### 3. Use ratios for scalable relationships

Represent design proportions as relationships rather than hard-coded values.

### 4. Use inequalities for constraints

Express minimums, maximums, and breakpoints as bounds.

### 5. Use coordinates for position and motion

Model transforms, canvases, and pointer interactions as coordinate problems.

### 6. Choose CSS for declarative relationships

Use CSS when the browser can solve the relationship from known layout inputs.

## Guidelines

Less strict recommendations:

- Use JavaScript when the calculation depends on live measurements, events, randomness, or state.
- Use CSS math when the relationship is declarative and can update with layout.
- Reduce formulas to named intermediate values before coding them.
- Check the formula at boundary values, not just the expected middle value.

## Exceptions

When these rules may be relaxed:

- **Performance-sensitive animation**: Prefer CSS transforms when the browser can optimize them.
- **Measured content**: Use JavaScript or observer APIs when the required input is only known at runtime.

## Quick Reference

| Rule | Summary |
|------|---------|
| Name the unknown | State what value you are solving for before choosing a formula. |
| Preserve units through calculations | Do not mix lengths, angles, ratios, and counts without conversion. |
| Use ratios for scalable relationships | Represent design proportions as relationships rather than hard-coded values. |
| Use inequalities for constraints | Express minimums, maximums, and breakpoints as bounds. |
| Use coordinates for position and motion | Model transforms, canvases, and pointer interactions as coordinate problems. |
| Choose CSS for declarative relationships | Use CSS when the browser can solve the relationship from known layout inputs. |
