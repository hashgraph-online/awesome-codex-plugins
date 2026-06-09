package user

import (
	"context"

	"practices/user-http-service/api/user/v1"
)

// Profile retrieves and returns the profile of the currently signed-in user.
func (c *ControllerV1) Profile(ctx context.Context, req *v1.ProfileReq) (res *v1.ProfileRes, err error) {
	res = &v1.ProfileRes{
		User: c.userSvc.GetProfile(ctx),
	}
	return
}
