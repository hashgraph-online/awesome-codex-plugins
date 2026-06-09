package user

import (
	"context"

	"practices/quick-demo/api/user/v1"
	"practices/quick-demo/internal/dao"
	"practices/quick-demo/internal/model/do"
)

// GetList gets the user list by age and status.
func (c *ControllerV1) GetList(ctx context.Context, req *v1.GetListReq) (res *v1.GetListRes, err error) {
	res = &v1.GetListRes{}
	err = dao.User.Ctx(ctx).Where(do.User{
		Age:    req.Age,
		Status: req.Status,
	}).Scan(&res.List)
	return
}
