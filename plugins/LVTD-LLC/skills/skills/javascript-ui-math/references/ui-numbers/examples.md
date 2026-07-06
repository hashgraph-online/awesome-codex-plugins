# JavaScript UI Math Examples

Code examples demonstrating javascript ui math principles.

Source: Chapter 2: Math basics for JavaScript; see `../source-map.md`.

## Bad and Good Examples

### Carousel index wrapping

```js
index = (index - 1) % slides.length;
```

**Problems**:
- When index - 1 is negative, JavaScript returns a negative remainder.

```js
const mod = (value, size) => ((value % size) + size) % size;
index = mod(index - 1, slides.length);
```

**Why it works**:
- The helper returns a normalized index in the range 0..size - 1.
### Defaulting a valid zero

```js
const delay = options.delay || 300;
```

**Problems**:
- A user-provided delay of 0 is replaced with 300.

```js
const delay = options.delay ?? 300;
```

**Why it works**:
- Only null or undefined trigger the default.


## Refactoring Walkthrough

### Before

A value is hard-coded because it looked right in one viewport or one data state.

### After

1. Name the value being solved.
2. Identify the reference value and unit.
3. Express the relationship as a bounded formula.
4. Test the formula at minimum, middle, and maximum states.
