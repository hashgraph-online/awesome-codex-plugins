package user

import (
	"context"

	"practices/user-http-service/api/user/v1"
)

// SignOut signs out the user.
func (c *ControllerV1) SignOut(ctx context.Context, req *v1.SignOutReq) (res *v1.SignOutRes, err error) {
	err = c.userSvc.SignOut(ctx)
	return
}
