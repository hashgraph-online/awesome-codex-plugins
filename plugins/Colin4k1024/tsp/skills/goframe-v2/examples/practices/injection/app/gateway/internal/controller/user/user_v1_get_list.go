package user

import (
	"context"

	userSvcV1 "practices/injection/app/user/api/user/v1"

	"practices/injection/app/gateway/api/user/v1"
)

func (c *ControllerV1) GetList(ctx context.Context, req *v1.GetListReq) (res *v1.GetListRes, err error) {
	result, err := c.userSvc.GetList(ctx, &userSvcV1.GetListReq{
		Ids: req.Ids,
	})
	if err != nil {
		return nil, err
	}
	res = &v1.GetListRes{
		List: make([]v1.ListItem, 0),
	}
	for _, v := range result.List {
		res.List = append(res.List, v1.ListItem{
			Id:        v.Id,
			Name:      v.Name,
			CreatedAt: v.CreatedAt,
		})
	}
	return
}
