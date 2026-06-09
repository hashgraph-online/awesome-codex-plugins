package user

import (
	"context"

	"github.com/gogf/gf/v2/errors/gerror"

	"practices/user-http-service/api/user/v1"
)

// CheckNickName checks if the given nickname is available for registration.
func (c *ControllerV1) CheckNickName(ctx context.Context, req *v1.CheckNickNameReq) (res *v1.CheckNickNameRes, err error) {
	available, err := c.userSvc.IsNicknameAvailable(ctx, req.Nickname)
	if err != nil {
		return nil, err
	}
	if !available {
		return nil, gerror.Newf(`Nickname "%s" is already token by others`, req.Nickname)
	}
	return
}
