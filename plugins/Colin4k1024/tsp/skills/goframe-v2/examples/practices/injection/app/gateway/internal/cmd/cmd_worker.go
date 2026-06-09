package cmd

import (
	"context"

	"practices/injection/utility/injection"

	"github.com/gogf/gf/v2/frame/g"
)

type WorkerInput struct {
	g.Meta `name:"worker" brief:"start service worker"`
}
type WorkerOutput struct{}

func (m *Main) Worker(ctx context.Context, in WorkerInput) (out *WorkerOutput, err error) {
	injection.SetupDefaultInjector(ctx)
	defer injection.ShutdownDefaultInjector()

	g.Log().Info(ctx, "service worker running")
	return
}
