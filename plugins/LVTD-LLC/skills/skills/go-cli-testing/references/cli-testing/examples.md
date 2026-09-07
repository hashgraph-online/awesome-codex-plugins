# Go CLI Testing Examples

Compact original examples of high-value CLI test seams.

## Inject Streams

Production code accepts streams and returns an error:

```go
func run(in io.Reader, out, errOut io.Writer) error {
	s := bufio.NewScanner(in)
	for s.Scan() {
		fmt.Fprintln(out, strings.ToUpper(s.Text()))
	}
	return s.Err()
}
```

The test observes output without replacing process globals:

```go
func TestRun(t *testing.T) {
	var stdout, stderr bytes.Buffer
	err := run(strings.NewReader("one\n"), &stdout, &stderr)
	if err != nil {
		t.Fatal(err)
	}
	if got, want := stdout.String(), "ONE\n"; got != want {
		t.Fatalf("stdout = %q, want %q", got, want)
	}
	if stderr.Len() != 0 {
		t.Fatalf("stderr = %q", stderr.String())
	}
}
```

## Table-Test Behavior Classes

```go
func TestParseLimit(t *testing.T) {
	tests := []struct {
		name string
		arg  string
		want int
		err  error
	}{
		{"valid", "10", 10, nil},
		{"zero", "0", 0, ErrInvalidLimit},
		{"text", "many", 0, ErrInvalidLimit},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := parseLimit(tt.arg)
			if !errors.Is(err, tt.err) {
				t.Fatalf("error = %v, want %v", err, tt.err)
			}
			if got != tt.want {
				t.Fatalf("limit = %d, want %d", got, tt.want)
			}
		})
	}
}
```

## Parser Subtests with Fresh State

```go
func TestParse(t *testing.T) {
	tests := []struct {
		name string
		args []string
		want options
		err  error
	}{
		{"help", []string{"-h"}, options{}, flag.ErrHelp},
		{"operand", []string{"input.txt"}, options{input: "input.txt"}, nil},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var stderr bytes.Buffer
			got, err := parse(tt.args, &stderr)
			if !errors.Is(err, tt.err) {
				t.Fatalf("parse(%q) error = %v, want %v", tt.args, err, tt.err)
			}
			if diff := cmp.Diff(tt.want, got); diff != "" {
				t.Fatalf("parse(%q) mismatch (-want +got):\n%s", tt.args, diff)
			}
		})
	}
}
```

## Temporary Filesystem Helper

```go
func writeFixture(t *testing.T, body string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "input.txt")
	if err := os.WriteFile(path, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
	return path
}
```

`t.TempDir` owns cleanup, while `t.Helper` reports failures at the caller.

## Fake Repository

```go
type memoryJobs struct{ names []string }

func (m *memoryJobs) Add(_ context.Context, name string) error {
	m.names = append(m.names, name)
	return nil
}

func TestAddJob(t *testing.T) {
	repo := &memoryJobs{}
	var out bytes.Buffer
	if err := addJob(context.Background(), repo, &out, "backup"); err != nil {
		t.Fatal(err)
	}
	if diff := cmp.Diff([]string{"backup"}, repo.names); diff != "" {
		t.Fatalf("jobs mismatch (-want +got):\n%s", diff)
	}
}
```

Use a handwritten comparison instead of `cmp` when avoiding external test
dependencies matters.

## Process Runner Boundary

```go
type runnerFunc func(context.Context, string, ...string) ([]byte, error)

func (f runnerFunc) Run(ctx context.Context, name string, args ...string) ([]byte, error) {
	return f(ctx, name, args...)
}

func TestVersionUsesGit(t *testing.T) {
	fake := runnerFunc(func(_ context.Context, name string, args ...string) ([]byte, error) {
		if name != "git" || !slices.Equal(args, []string{"describe", "--always"}) {
			t.Fatalf("command = %s %v", name, args)
		}
		return []byte("v1.2.3\n"), nil
	})
	got, err := version(context.Background(), fake)
	if err != nil || got != "v1.2.3" {
		t.Fatalf("version = %q, %v", got, err)
	}
}
```

## Local HTTP Contract

```go
func TestCreateRequest(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/jobs" {
			t.Errorf("request = %s %s", r.Method, r.URL.Path)
		}
		if got := r.Header.Get("Content-Type"); got != "application/json" {
			t.Errorf("content-type = %q", got)
		}
		w.WriteHeader(http.StatusCreated)
	}))
	t.Cleanup(srv.Close)

	if err := createJob(context.Background(), srv.Client(), srv.URL, "backup"); err != nil {
		t.Fatal(err)
	}
}
```

## Opt-In Integration Test

```go
//go:build integration

package cli_test

func TestLiveVersion(t *testing.T) {
	baseURL := os.Getenv("EXAMPLE_API_URL")
	if baseURL == "" {
		t.Skip("EXAMPLE_API_URL is required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if _, err := fetchVersion(ctx, http.DefaultClient, baseURL); err != nil {
		t.Fatal(err)
	}
}
```

Run it explicitly with `go test -count=1 -tags=integration ./...`.

## Source Traceability

Concepts were transformed into new examples from:

- Stream injection and golden-file tests, normalized lines 3006–4789.
- Table tests and temporary-resource helpers, normalized lines 4790–9381.
- Process fakes and helper processes, normalized lines 9382–13235.
- Action-function and local HTTP tests, normalized lines 13236–18981.
- Tagged integration and interchangeable repository tests, normalized lines 18982–24644.
