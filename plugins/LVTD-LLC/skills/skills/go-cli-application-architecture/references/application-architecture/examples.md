# Application Architecture Examples

## Inject an Effect Without a Test-Only Switch

```go
type Dependencies struct {
	Upload func(context.Context, Artifact) error
}

func run(ctx context.Context, deps Dependencies, artifact Artifact) error {
	if err := deps.Upload(ctx, artifact); err != nil {
		return fmt.Errorf("upload artifact: %w", err)
	}
	return nil
}
```

The test records calls through the function. A product-level `--dry-run` may
still exist, but it is not required merely to make the operation testable.

## Thin Command Adapter

```go
func newListCmd(svc ProjectLister) *cobra.Command {
	var limit int
	cmd := &cobra.Command{
		Use: "list",
		RunE: func(cmd *cobra.Command, _ []string) error {
			items, err := svc.List(cmd.Context(), limit)
			if err != nil {
				return err
			}
			return renderProjects(cmd.OutOrStd(), items)
		},
	}
	cmd.Flags().IntVar(&limit, "limit", 20, "maximum projects")
	return cmd
}
```

The service does not know Cobra or stdout.

## Consumer-Owned Port

```go
type ProjectLister interface {
	List(context.Context, int) ([]Project, error)
}
```

Prefer this over a broad `Repository` containing unrelated create, update,
delete, search, cache, and transaction methods.

## Composition Root

```go
func run(ctx context.Context, args []string, streams Streams) error {
	bootstrap, err := parseBootstrap(args)
	if err != nil {
		return err
	}
	if bootstrap.EarlyExit() {
		return executeEarlyCommand(args, streams)
	}
	cfg, err := loadAndValidateConfig()
	if err != nil {
		return err
	}
	client := newAPIClient(cfg)
	root := newRoot(Dependencies{Projects: client, Streams: streams})
	root.SetArgs(args)
	return root.ExecuteContext(ctx)
}
```

`main` handles signal context, error presentation, and exit status.
