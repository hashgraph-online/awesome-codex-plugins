package cmd

import (
	"context"

	"practices/injection/utility/injection"

	"github.com/gogf/gf/contrib/rpc/grpcx/v2"
	"github.com/gogf/gf/v2/frame/g"
	"google.golang.org/grpc"

	"practices/injection/app/user/internal/controller/user"
)

type ServerInput struct {
	g.Meta `name:"server" brief:"start service server"`
}
type ServerOutput struct{}

func (m *Main) Server(ctx context.Context, in ServerInput) (out *ServerOutput, err error) {
	injection.SetupDefaultInjector(ctx)
	defer injection.ShutdownDefaultInjector()

	c := grpcx.Server.NewConfig()
	c.Options = append(c.Options, []grpc.ServerOption{
		grpcx.Server.ChainUnary(
			grpcx.Server.UnaryValidate,
		)}...,
	)
	s := grpcx.Server.New(c)
	user.RegisterV1(s)
	s.Run()
	return
}
