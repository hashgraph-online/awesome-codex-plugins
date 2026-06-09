package cmd

import (
	"context"

	"github.com/gogf/gf/contrib/rpc/grpcx/v2"
	"github.com/gogf/gf/v2/os/gcmd"
	"google.golang.org/grpc"

	"practices/user-grpc-service/internal/controller/user"
)

var (
	// Main is the main command.
	Main = gcmd.Command{
		Name:  "main",
		Usage: "main",
		Brief: "start grpc server of simple goframe demos",
		Func:  mainFunc,
	}
)

// mainFunc is the main function for the "main" command, which starts the gRPC server and registers service handlers.
func mainFunc(ctx context.Context, parser *gcmd.Parser) (err error) {
	c := grpcx.Server.NewConfig()
	c.Options = append(c.Options, []grpc.ServerOption{
		grpcx.Server.ChainUnary(
			grpcx.Server.UnaryValidate,
		)}...,
	)
	s := grpcx.Server.New(c)
	user.Register(s)
	s.Run()
	return nil
}
