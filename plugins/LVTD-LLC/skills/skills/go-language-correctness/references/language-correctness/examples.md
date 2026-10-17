# Go Language Correctness Examples

## Validate Before Narrowing

```go
func parseWorkers(raw string) (uint16, error) {
    n, err := strconv.ParseInt(raw, 10, 64)
    if err != nil || n < 1 || n > math.MaxUint16 {
        return 0, fmt.Errorf("workers must be between 1 and %d", math.MaxUint16)
    }
    return uint16(n), nil
}
```

Converting first can silently wrap. Validate the wide value before conversion.

## Separate Slice Ownership

```go
func snapshot(src []byte) []byte {
    return append([]byte(nil), src...)
}
```

Use a capacity-clipped view instead only when shared elements are intentional
and the goal is to prevent append from overwriting the caller's tail.

## Mutate the Collection, Not the Range Copy

```go
for i := range jobs {
    jobs[i].Ready = true
}
```

`for _, job := range jobs` mutates a copied struct value.

## Produce Deterministic Map Output

```go
keys := slices.Sorted(maps.Keys(values))
for _, key := range keys {
    fmt.Fprintf(out, "%s=%s\n", key, values[key])
}
```

Check the module's minimum Go version before using newer `maps` or `slices`
helpers; otherwise collect and sort keys explicitly.

## Close Per Iteration

```go
func visit(path string) error {
    f, err := os.Open(path)
    if err != nil {
        return err
    }
    defer f.Close()
    return consume(f)
}
```

Call `visit` from the loop so each defer runs before the next file is opened.

## State the Text Unit

```go
if !utf8.ValidString(input) {
    return errors.New("input must be UTF-8")
}
if utf8.RuneCountInString(input) > maxRunes {
    return fmt.Errorf("input exceeds %d Unicode code points", maxRunes)
}
```

Do not describe this as a grapheme or visible-character limit.
