package user

import (
	"context"

	"practices/quick-demo/api/user/v1"
	"practices/quick-demo/internal/dao"
	"practices/quick-demo/internal/model/do"
)

// Update updates the user by Id.
func (c *ControllerV1) Update(ctx context.Context, req *v1.UpdateReq) (res *v1.UpdateRes, err error) {
	_, err = dao.User.Ctx(ctx).Data(do.User{
		Name:   req.Name,
		Status: req.Status,
		Age:    req.Age,
	}).WherePri(req.Id).Update()
	return
}
