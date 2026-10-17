# Cobra Applications Examples

Compact original examples of a modern, testable Cobra boundary.

## Fresh Command Tree With Injected Dependencies

```go
type Services struct {
	Projects ProjectService
	Out      io.Writer
	Err      io.Writer
}

func NewRoot(s Services) *cobra.Command {
	root := &cobra.Command{
		Use:           "forge",
		Short:         "Manage build projects",
		SilenceErrors: true,
	}
	root.SetOut(s.Out)
	root.SetErr(s.Err)
	root.AddCommand(newProjectCommand(s))
	return root
}
```

`main` stays small and owns process exit behavior:

```go
func run(ctx context.Context, args []string, s Services) error {
	root := NewRoot(s)
	root.SetArgs(args)
	return root.ExecuteContext(ctx)
}
```

## Thin Handler, Typed Application Call

```go
func newProjectAddCommand(s Services) *cobra.Command {
	var archived bool
	cmd := &cobra.Command{
		Use:   "add NAME",
		Short: "Add a project",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			p, err := s.Projects.Add(cmd.Context(), args[0], archived)
			if err != nil {
				return fmt.Errorf("add project %q: %w", args[0], err)
			}
			_, err = fmt.Fprintln(cmd.OutOrStdout(), p.ID)
			return err
		},
	}
	cmd.Flags().BoolVar(&archived, "archived", false, "create as archived")
	return cmd
}
```

The application service receives ordinary Go values and does not know about
Cobra, flags, or terminal streams.

## Local and Persistent Flags

```go
func newProjectCommand(s Services) *cobra.Command {
	project := &cobra.Command{Use: "project", Short: "Manage projects"}
	project.AddCommand(newProjectAddCommand(s), newProjectListCommand(s))
	return project
}

func addGlobalFlags(root *cobra.Command, cfg *Options) {
	root.PersistentFlags().StringVar(
		&cfg.Profile, "profile", "default", "configuration profile",
	)
}
```

`--archived` belongs only to `project add`; `--profile` is inherited because it
applies throughout the application.

## Command Test

```go
func TestProjectAdd(t *testing.T) {
	var stdout, stderr bytes.Buffer
	fake := &fakeProjects{created: Project{ID: "p_123"}}
	root := NewRoot(Services{Projects: fake, Out: &stdout, Err: &stderr})
	root.SetArgs([]string{"project", "add", "demo", "--archived"})

	err := root.ExecuteContext(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if got := stdout.String(); got != "p_123\n" {
		t.Fatalf("stdout = %q", got)
	}
	if !fake.archived {
		t.Fatal("expected archived option")
	}
}
```

Build a new root inside each test. This captures output without mutating
`os.Stdout` and verifies the parser-to-service boundary.

## Explicit Configuration Precedence

```go
func Resolve(base Options, env map[string]string, flagSet bool, flag string) Options {
	out := base
	if v, ok := env["FORGE_PROFILE"]; ok {
		out.Profile = v
	}
	if flagSet {
		out.Profile = flag
	}
	return out
}
```

Test each source independently and test collisions. If Viper is used to perform
this resolution, preserve the same explicit contract.

## Shell-Specific Completion Shape

```go
func newCompletionCommand(root *cobra.Command) *cobra.Command {
	return &cobra.Command{
		Use:       "completion SHELL",
		Short:     "Generate shell completion",
		Args:      cobra.ExactArgs(1),
		ValidArgs: []string{"bash", "fish", "powershell", "zsh"},
		RunE: func(cmd *cobra.Command, args []string) error {
			return writeCompletion(root, cmd.OutOrStdout(), args[0])
		},
	}
}
```

Keep the shell switch and generator calls in `writeCompletion`, where each path
can be tested and updated independently.

## Historical API Verification

**Upstream verification required:** before compiling these examples, verify
`cobra.Command` fields `Use`, `Short`, `Args`, `RunE`, `SilenceErrors`, and
`ValidArgs`; methods `SetOut`, `SetErr`, `OutOrStdout`, `Context`, `SetArgs`,
`ExecuteContext`, `AddCommand`, `Flags`, and `PersistentFlags`; validators
`ExactArgs`; and each shell generator used inside `writeCompletion` against the
pinned Cobra version.

## Source Traceability

- Chapter 7, “Navigating Your New Cobra Application” and “Adding the First
  Subcommand to Your Application,” normalized lines 12027-12360.
- “Creating the Subcommands to Manage Hosts” and “Testing the Manage Hosts
  Subcommands,” normalized lines 12804-13698.
- “Adding the Port Scanning Functionality,” normalized lines 14251-14721.
- “Using Viper for Configuration Management,” normalized lines 14722-14948.
- “Generating Command Completion and Documentation,” normalized lines
  14949-15235.
