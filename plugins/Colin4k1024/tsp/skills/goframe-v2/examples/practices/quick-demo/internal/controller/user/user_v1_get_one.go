package user

import (
	"context"

	"practices/quick-demo/api/user/v1"
	"practices/quick-demo/internal/dao"
)

// GetOne gets the user by Id.
func (c *ControllerV1) GetOne(ctx context.Context, req *v1.GetOneReq) (res *v1.GetOneRes, err error) {
	res = &v1.GetOneRes{}
	err = dao.User.Ctx(ctx).WherePri(req.Id).Scan(&res.User)
	return
}
