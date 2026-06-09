package user

import (
	"context"

	v1 "practices/user-grpc-service/api/user/v1"
	"practices/user-grpc-service/internal/dao"
	"practices/user-grpc-service/internal/model/do"
	"practices/user-grpc-service/internal/service/user"

	"github.com/gogf/gf/contrib/rpc/grpcx/v2"
)

// Controller implements the gRPC server for user-related operations,
// providing methods to create, retrieve, list, and delete users.
type Controller struct {
	v1.UnimplementedUserServer
	userService *user.Service
}

// Register registers the User gRPC server with the provided gRPC server instance,
// allowing it to handle incoming user-related gRPC requests.
func Register(s *grpcx.GrpcServer) {
	v1.RegisterUserServer(s.Server, &Controller{
		// Initialize the user service to handle business logic related to users.
		userService: user.New(),
	})
}

// Create creates a new user in the database based on the provided request data.
func (*Controller) Create(ctx context.Context, req *v1.CreateReq) (res *v1.CreateRes, err error) {
	_, err = dao.User.Ctx(ctx).Data(do.User{
		Passport: req.Passport,
		Password: req.Password,
		Nickname: req.Nickname,
	}).Insert()
	return
}

// GetOne retrieves a user by their ID using the user service and returns the user information in the response.
func (c *Controller) GetOne(ctx context.Context, req *v1.GetOneReq) (res *v1.GetOneRes, err error) {
	userItem, err := c.userService.GetById(ctx, req.Id)
	if err != nil {
		return nil, err
	}
	res = &v1.GetOneRes{
		User: userItem,
	}
	return
}

// GetList retrieves a paginated list of users from the database and returns it in the response.
func (*Controller) GetList(ctx context.Context, req *v1.GetListReq) (res *v1.GetListRes, err error) {
	res = &v1.GetListRes{}
	err = dao.User.Ctx(ctx).Page(int(req.Page), int(req.Size)).Scan(&res.Users)
	return
}

// Delete removes a user from the database based on the provided user ID in the request.
func (c *Controller) Delete(ctx context.Context, req *v1.DeleteReq) (res *v1.DeleteRes, err error) {
	err = c.userService.DeleteById(ctx, req.Id)
	return
}
