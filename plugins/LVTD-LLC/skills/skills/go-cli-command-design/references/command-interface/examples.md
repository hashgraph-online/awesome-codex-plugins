# Go CLI Command Interface Examples

Compact, original examples of testable command boundaries and predictable input.

## Help and Operand Cardinality

```go
func parse(args []string, stderr io.Writer) (options, error) {
	fs := flag.NewFlagSet("tool", flag.ContinueOnError)
	fs.SetOutput(stderr)

	var opts options
	fs.StringVar(&opts.format, "format", "text", "output format")
	if err := fs.Parse(args); err != nil {
		return options{}, err
	}
	if fs.NArg() != 1 {
		return options{}, fmt.Errorf("expected exactly one input")
	}
	opts.input = fs.Arg(0)
	return opts, nil
}
```

The process boundary maps `flag.ErrHelp` to success and other parse or
cardinality failures to invalid usage.

## Thin Process Boundary

```go
func main() {
	if err := run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr, os.LookupEnv); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
```

Only the outer boundary uses process globals or terminates the process.

## Parse with an Isolated FlagSet

```go
type options struct {
	format string
	path   string
}

func parse(args []string, stderr io.Writer) (options, []string, error) {
	fs := flag.NewFlagSet("inspect", flag.ContinueOnError)
	fs.SetOutput(stderr)
	var cfg options
	fs.StringVar(&cfg.format, "format", "text", "output format: text or json")
	fs.StringVar(&cfg.path, "path", "", "input path")
	if err := fs.Parse(args); err != nil {
		return options{}, nil, err
	}
	return cfg, fs.Args(), nil
}
```

This parser can be invoked repeatedly in tests without mutating global flags.

## Resolve Configuration Precedence

```go
func cacheDir(flagValue string, lookup func(string) (string, bool)) string {
	if flagValue != "" {
		return flagValue
	}
	if value, ok := lookup("ACME_CACHE_DIR"); ok {
		return value
	}
	return ".acme-cache"
}
```

An explicit flag wins, then an environment value, then the built-in default.

## Choose Arguments Before Stdin

```go
func readMessage(r io.Reader, args []string) (string, error) {
	if len(args) > 0 {
		return strings.Join(args, " "), nil
	}
	scanner := bufio.NewScanner(r)
	if !scanner.Scan() {
		if err := scanner.Err(); err != nil {
			return "", fmt.Errorf("read input: %w", err)
		}
		return "", errors.New("message is required")
	}
	if text := strings.TrimSpace(scanner.Text()); text != "" {
		return text, nil
	}
	return "", errors.New("message is required")
}
```

The precedence is visible, empty input is rejected, and scanner errors survive.
Use this only when the command intentionally promises stdin fallback.

## Separate Results from Diagnostics

```go
func execute(out, errOut io.Writer, result string, err error) int {
	if err != nil {
		fmt.Fprintf(errOut, "inspect: %v\n", err)
		return 1
	}
	fmt.Fprintln(out, result)
	return 0
}
```

Callers can pipe stdout without capturing human-facing errors.

## Refactoring a Global Command

### Before

```go
func main() {
	verbose := flag.Bool("verbose", false, "show details")
	flag.Parse()
	fmt.Println(load(os.Getenv("APP_FILE"), *verbose))
}
```

### After

```go
func run(args []string, out, errOut io.Writer, getenv func(string) string) error {
	fs := flag.NewFlagSet("app", flag.ContinueOnError)
	fs.SetOutput(errOut)
	verbose := fs.Bool("verbose", false, "show details")
	if err := fs.Parse(args); err != nil {
		return err
	}
	result, err := load(getenv("APP_FILE"), *verbose)
	if err != nil {
		return err
	}
	_, err = fmt.Fprintln(out, result)
	return err
}
```

The refactoring makes parsing, environment lookup, output, and failures
controllable by tests.

## Cross-Target Build

```sh
GOOS=linux GOARCH=arm64 go build -o dist/tool-linux-arm64 ./cmd/tool
GOOS=windows GOARCH=amd64 go build -o dist/tool-windows-amd64.exe ./cmd/tool
```

Follow builds with target-OS smoke tests, especially when using cgo, signals,
terminal APIs, or OS-specific files.

## Source Traceability

These examples transform concepts from:

- Chapter 1, “Building the Basic Word Counter,” “Adding Command-Line Flags,”
  and “Compiling Your Tool for Different Platforms” (normalized lines 548–937).
- Chapter 2, “Organizing Your Code,” “Creating the Initial To-Do Command-Line
  Tool,” “Handling Multiple Command-Line Options,” “Display Command-Line Tool
  Usage,” “Increasing Flexibility with Environment Variables,” and “Capturing
  Input from STDIN” (normalized lines 1012–2699).

All code is newly written and intentionally differs from the book examples.
