package user

import (
	"context"

	userSvcV1 "practices/injection/app/user/api/user/v1"

	"practices/injection/app/gateway/api/user/v1"
)

func (c *ControllerV1) GetOne(ctx context.Context, req *v1.GetOneReq) (res *v1.GetOneRes, err error) {
	result, err := c.userSvc.GetOne(ctx, &userSvcV1.GetOneReq{
		Id: req.Id,
	})
	if err != nil {
		return nil, err
	}
	res = &v1.GetOneRes{
		Data: v1.ListItem{
			Id:        result.Data.Id,
			Name:      result.Data.Name,
			CreatedAt: result.Data.CreatedAt,
		},
	}
	return
}
