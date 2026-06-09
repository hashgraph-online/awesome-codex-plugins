package user

import (
	"context"

	"practices/injection/app/gateway/api/user/v1"
	userSvcV1 "practices/injection/app/user/api/user/v1"
)

func (c *ControllerV1) Create(ctx context.Context, req *v1.CreateReq) (res *v1.CreateRes, err error) {
	result, err := c.userSvc.Create(ctx, &userSvcV1.CreateReq{
		Name: req.Name,
	})
	if err != nil {
		return nil, err
	}
	res = &v1.CreateRes{
		Id: result.Id,
	}
	return
}
