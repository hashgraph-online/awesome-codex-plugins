package user

import (
	"context"

	"practices/quick-demo/api/user/v1"
	"practices/quick-demo/internal/dao"
	"practices/quick-demo/internal/model/do"
)

// Create creates a new user.
func (c *ControllerV1) Create(ctx context.Context, req *v1.CreateReq) (res *v1.CreateRes, err error) {
	insertId, err := dao.User.Ctx(ctx).Data(do.User{
		Name:   req.Name,
		Status: v1.StatusOK,
		Age:    req.Age,
	}).InsertAndGetId()
	if err != nil {
		return nil, err
	}
	res = &v1.CreateRes{
		Id: insertId,
	}
	return
}
