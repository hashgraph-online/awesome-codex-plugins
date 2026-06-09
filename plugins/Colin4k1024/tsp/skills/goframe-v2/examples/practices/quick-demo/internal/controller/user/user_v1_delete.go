package user

import (
	"context"

	"practices/quick-demo/api/user/v1"
	"practices/quick-demo/internal/dao"
)

// Delete deletes the user by Id.
func (c *ControllerV1) Delete(ctx context.Context, req *v1.DeleteReq) (res *v1.DeleteRes, err error) {
	_, err = dao.User.Ctx(ctx).WherePri(req.Id).Delete()
	return
}
