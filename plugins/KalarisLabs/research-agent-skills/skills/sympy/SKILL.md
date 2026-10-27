---
name: sympy
description: Use when you need exact symbolic math in Python — algebra, calculus, equation solving, symbolic linear algebra, or code generation via lambdify/LaTeX. Prefer NumPy or SciPy when floating-point approximations are sufficient.
license: https://github.com/sympy/sympy/blob/master/LICENSE
compatibility: Requires Python 3.9+ and SymPy 1.14+. Optional NumPy/SciPy/Matplotlib for lambdify examples; C/Fortran compiler for autowrap/codegen.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.3'
  category: data-science-and-ml
  maintainer: Kalaris Labs
  tags: symbolic math, computer algebra, calculus, mathematics, Python
---

# SymPy - Symbolic Mathematics in Python

## Overview

SymPy is a Python library for symbolic mathematics that enables exact computation using mathematical symbols rather than numerical approximations. This skill provides comprehensive guidance for performing symbolic algebra, calculus, linear algebra, equation solving, physics calculations, and code generation using SymPy.

## Installation

Tested against **SymPy 1.14.0** (stable; April 2025). Requires **Python 3.9+**.

```bash
# Install SymPy using uv
uv pip install "sympy>=1.14"

# Optional: for lambdify and plotting examples
uv pip install numpy scipy matplotlib
```

Check your version:

```python
import sympy
print(sympy.__version__)
```

## When to Use This Skill

Use this skill when:
- Solving equations symbolically (algebraic, differential, systems of equations)
- Performing calculus operations (derivatives, integrals, limits, series)
- Manipulating and simplifying algebraic expressions
- Working with matrices and linear algebra symbolically
- Doing physics calculations (mechanics, quantum mechanics, vector analysis)
- Number theory computations (primes, factorization, modular arithmetic)
- Geometric calculations (2D/3D geometry, analytic geometry)
- Converting mathematical expressions to executable code (Python, C, Fortran)
- Generating LaTeX or other formatted mathematical output
- Needing exact mathematical results (e.g., `sqrt(2)` not `1.414...`)

## Core Capabilities

Seven capability areas are documented in
[references/core_capabilities.md](references/core_capabilities.md):

1. **Symbolic computation basics** — symbols, expressions, simplification, substitution.
2. **Calculus** — differentiation, integration, limits, series.
3. **Equation solving** — `solve`, `solveset`, linear and nonlinear systems, ODEs.
4. **Matrices and linear algebra** — see
   [references/matrices-linear-algebra.md](references/matrices-linear-algebra.md).
5. **Physics and mechanics** — see
   [references/physics-mechanics.md](references/physics-mechanics.md).
6. **Advanced mathematics** — see
   [references/advanced-topics.md](references/advanced-topics.md).
7. **Code generation and output** — see
   [references/code-generation-printing.md](references/code-generation-printing.md).

Deeper treatment of the first three is in
[references/core-capabilities.md](references/core-capabilities.md).

## Working with SymPy: Best Practices

### 1. Always Define Symbols First

```python
from sympy import symbols
x, y, z = symbols('x y z')
# Now x, y, z can be used in expressions
```

### 2. Use Assumptions for Better Simplification

```python
x = symbols('x', positive=True, real=True)
sqrt(x**2)  # Returns x (not Abs(x)) due to positive assumption
```

Common assumptions: `real`, `positive`, `negative`, `integer`, `rational`, `complex`, `even`, `odd`

### 3. Use Exact Arithmetic

```python
from sympy import Rational, S
# Correct (exact):
expr = Rational(1, 2) * x
expr = S(1)/2 * x

# Incorrect (floating-point):
expr = 0.5 * x  # Creates approximate value
```

### 4. Numerical Evaluation When Needed

```python
from sympy import pi, sqrt
result = sqrt(8) + pi
result.evalf()    # 5.96371554103586
result.evalf(50)  # 50 digits of precision
```

### 5. Convert to NumPy for Performance

```python
# Slow for many evaluations:
for x_val in range(1000):
    result = expr.subs(x, x_val).evalf()

# Fast:
f = lambdify(x, expr, 'numpy')
results = f(np.arange(1000))
```

### 6. Use Appropriate Solvers

- `solveset`: Algebraic equations (primary)
- `linsolve`: Linear systems
- `nonlinsolve`: Nonlinear systems
- `dsolve`: Differential equations
- `solve`: General purpose (legacy, but flexible)

## Reference Files Structure

This skill uses modular reference files for different capabilities:

1. **`core-capabilities.md`**: Symbols, algebra, calculus, simplification, equation solving
   - Load when: Basic symbolic computation, calculus, or solving equations

2. **`matrices-linear-algebra.md`**: Matrix operations, eigenvalues, linear systems
   - Load when: Working with matrices or linear algebra problems

3. **`physics-mechanics.md`**: Classical mechanics, quantum mechanics, vectors, units
   - Load when: Physics calculations or mechanics problems

4. **`advanced-topics.md`**: Geometry, number theory, combinatorics, logic, statistics
   - Load when: Advanced mathematical topics beyond basic algebra and calculus

5. **`code-generation-printing.md`**: Lambdify, codegen, LaTeX output, printing
   - Load when: Converting expressions to code or generating formatted output

## Common Use Case Patterns

### Pattern 1: Solve and Verify

```python
from sympy import symbols, solve, simplify
x = symbols('x')

# Solve equation
equation = x**2 - 5*x + 6
solutions = solve(equation, x)  # [2, 3]

# Verify solutions
for sol in solutions:
    result = simplify(equation.subs(x, sol))
    assert result == 0
```

### Pattern 2: Symbolic to Numeric Pipeline

```python
# 1. Define symbolic problem
x, y = symbols('x y')
expr = sin(x) + cos(y)

# 2. Manipulate symbolically
simplified = simplify(expr)
derivative = diff(simplified, x)

# 3. Convert to numerical function
f = lambdify((x, y), derivative, 'numpy')

# 4. Evaluate numerically
results = f(x_data, y_data)
```

### Pattern 3: Document Mathematical Results

```python
# Compute result symbolically
integral_expr = Integral(x**2, (x, 0, 1))
result = integral_expr.doit()

# Generate documentation
print(f"LaTeX: {latex(integral_expr)} = {latex(result)}")
print(f"Pretty: {pretty(integral_expr)} = {pretty(result)}")
print(f"Numerical: {result.evalf()}")
```

## Integration with Scientific Workflows

### With NumPy

```python
import numpy as np
from sympy import symbols, lambdify

x = symbols('x')
expr = x**2 + 2*x + 1

f = lambdify(x, expr, 'numpy')
x_array = np.linspace(-5, 5, 100)
y_array = f(x_array)
```

### With Matplotlib

```python
import matplotlib.pyplot as plt
import numpy as np
from sympy import symbols, lambdify, sin

x = symbols('x')
expr = sin(x) / x

f = lambdify(x, expr, 'numpy')
x_vals = np.linspace(-10, 10, 1000)
y_vals = f(x_vals)

plt.plot(x_vals, y_vals)
plt.show()
```

### With SciPy

```python
from scipy.optimize import fsolve
from sympy import symbols, lambdify

# Define equation symbolically
x = symbols('x')
equation = x**3 - 2*x - 5

# Convert to numerical function
f = lambdify(x, equation, 'numpy')

# Solve numerically with initial guess
solution = fsolve(f, 2)
```

## Quick Reference: Most Common Functions

```python
# Symbols
from sympy import symbols, Symbol
x, y = symbols('x y')

# Basic operations
from sympy import simplify, expand, factor, collect, cancel
from sympy import sqrt, exp, log, sin, cos, tan, pi, E, I, oo

# Calculus
from sympy import diff, integrate, limit, series, Derivative, Integral

# Solving
from sympy import solve, solveset, linsolve, nonlinsolve, dsolve

# Matrices
from sympy import Matrix, eye, zeros, ones, diag

# Logic and sets
from sympy import And, Or, Not, Implies, FiniteSet, Interval, Union

# Output
from sympy import latex, pprint, lambdify, init_printing

# Utilities
from sympy import evalf, N, nsimplify
```

## Getting Started Examples

### Example 1: Solve Quadratic Equation
```python
from sympy import symbols, solve, sqrt
x = symbols('x')
solution = solve(x**2 - 5*x + 6, x)
# [2, 3]
```

### Example 2: Calculate Derivative
```python
from sympy import symbols, diff, sin
x = symbols('x')
f = sin(x**2)
df_dx = diff(f, x)
# 2*x*cos(x**2)
```

### Example 3: Evaluate Integral
```python
from sympy import symbols, integrate, exp
x = symbols('x')
integral = integrate(x * exp(-x**2), (x, 0, oo))
# 1/2
```

### Example 4: Matrix Eigenvalues
```python
from sympy import Matrix
M = Matrix([[1, 2], [2, 1]])
eigenvals = M.eigenvals()
# {3: 1, -1: 1}
```

### Example 5: Generate Python Function
```python
from sympy import symbols, lambdify
import numpy as np
x = symbols('x')
expr = x**2 + 2*x + 1
f = lambdify(x, expr, 'numpy')
f(np.array([1, 2, 3]))
# array([ 4,  9, 16])
```

## Troubleshooting Common Issues

1. **"NameError: name 'x' is not defined"**
   - Solution: Always define symbols using `symbols()` before use

2. **Unexpected numerical results**
   - Issue: Using floating-point numbers like `0.5` instead of `Rational(1, 2)`
   - Solution: Use `Rational()` or `S()` for exact arithmetic

3. **Slow performance in loops**
   - Issue: Using `subs()` and `evalf()` repeatedly
   - Solution: Use `lambdify()` to create a fast numerical function

4. **"Can't solve this equation"**
   - Try different solvers: `solve`, `solveset`, `nsolve` (numerical)
   - Check if the equation is solvable algebraically
   - Use numerical methods if no closed-form solution exists

5. **Simplification not working as expected**
   - Try different simplification functions: `simplify`, `factor`, `expand`, `trigsimp`
   - Add assumptions to symbols (e.g., `positive=True`)
   - Use `simplify(expr, force=True)` for aggressive simplification

## Additional Resources

- Official Documentation: https://docs.sympy.org/
- Tutorial: https://docs.sympy.org/latest/tutorials/intro-tutorial/index.html
- API Reference: https://docs.sympy.org/latest/reference/index.html
- Examples: https://github.com/sympy/sympy/tree/master/examples

## Agent operating procedure

1. **Check the environment.** Confirm the Python environment and library versions (`python -c "import pkg; print(pkg.__version__)"`) and inspect the data's shape, types and missing values.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run on a sample or a single fold first and check runtime and memory.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Use held-out data, fixed random seeds and appropriate metrics; check for leakage; report uncertainty (CIs, std over seeds).
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Out-of-memory or very slow execution | Subsample, use chunked or lazy computation, or reduce model size, and tell the user what changed. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never report a metric you did not compute in this session; show the code path that produced every number.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.
