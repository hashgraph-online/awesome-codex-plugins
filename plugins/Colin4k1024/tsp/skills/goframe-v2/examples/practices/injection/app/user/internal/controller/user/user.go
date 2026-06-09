// Package user implements the gRPC controller layer for user-related operations.
package user

import (
	"context"

	"practices/injection/app/user/internal/service/user"

	"github.com/gogf/gf/contrib/rpc/grpcx/v2"
	"github.com/gogf/gf/v2/errors/gerror"

	v1 "practices/injection/app/user/api/user/v1"
)

// ControllerV1 implements the gRPC user service interface.
type ControllerV1 struct {
	v1.UnimplementedUserServer
	userSvc *user.Service // Injected user service
}

// RegisterV1 registers the user controller with the gRPC server.
func RegisterV1(s *grpcx.GrpcServer) {
	v1.RegisterUserServer(s.Server, newUserController())
}

// newUserController creates a new instance of ControllerV1 with injected dependencies.
func newUserController() *ControllerV1 {
	return &ControllerV1{
		userSvc: user.New(),
	}
}

// Create handles the creation of a new user.
// It implements the gRPC CreateUser method.
func (c *ControllerV1) Create(ctx context.Context, req *v1.CreateReq) (res *v1.CreateRes, err error) {
	result, err := c.userSvc.Create(ctx, req.Name)
	if err != nil {
		return nil, gerror.Wrap(err, "create user failed")
	}

	return &v1.CreateRes{Id: result}, nil
}

// GetOne retrieves a single user by ID.
// It implements the gRPC GetUser method.
func (c *ControllerV1) GetOne(ctx context.Context, req *v1.GetOneReq) (res *v1.GetOneRes, err error) {
	result, err := c.userSvc.GetById(ctx, req.Id)
	if err != nil {
		return nil, gerror.Wrap(err, "get user failed")
	}

	if result == nil {
		return &v1.GetOneRes{}, nil
	}

	return &v1.GetOneRes{Data: result}, nil
}

// GetList retrieves a list of users.
// It implements the gRPC ListUsers method.
func (c *ControllerV1) GetList(ctx context.Context, req *v1.GetListReq) (res *v1.GetListRes, err error) {
	result, err := c.userSvc.GetList(ctx, req.Ids)
	if err != nil {
		return nil, gerror.Wrap(err, "get user list failed")
	}

	return &v1.GetListRes{List: result}, nil
}

// Delete removes a user by ID.
// It implements the gRPC DeleteUser method.
func (c *ControllerV1) Delete(ctx context.Context, req *v1.DeleteReq) (res *v1.DeleteRes, err error) {
	if err = c.userSvc.DeleteById(ctx, req.Id); err != nil {
		return nil, gerror.Wrap(err, "delete user failed")
	}

	return &v1.DeleteRes{}, nil
}
