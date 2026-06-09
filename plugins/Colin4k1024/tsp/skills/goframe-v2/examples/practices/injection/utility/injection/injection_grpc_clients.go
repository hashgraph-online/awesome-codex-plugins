package injection

import (
	"context"

	userv1 "practices/injection/app/user/api/user/v1"

	"github.com/gogf/gf/contrib/rpc/grpcx/v2"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/samber/do"
)

// injectGrpcClients injects grpc clients.
func injectGrpcClients(ctx context.Context, injector *do.Injector) {
	// user service.
	do.Provide(injector, func(i *do.Injector) (userv1.UserClient, error) {
		serviceName := g.Cfg().MustGet(ctx, "services.user", "svc-template:8000").String()
		conn, err := grpcx.Client.NewGrpcClientConn(serviceName)
		if err != nil {
			return nil, gerror.Wrapf(err, `new grpc client connection with "%s" failed`, serviceName)
		}
		client := userv1.NewUserClient(conn)
		SetupShutdownHelper(injector, client, func(userv1.UserClient) error {
			return conn.Close()
		})
		return client, nil
	})
}
