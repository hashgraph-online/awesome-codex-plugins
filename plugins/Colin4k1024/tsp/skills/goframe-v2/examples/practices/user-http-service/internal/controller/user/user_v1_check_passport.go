package user

import (
	"context"

	"github.com/gogf/gf/v2/errors/gerror"

	"practices/user-http-service/api/user/v1"
)

// CheckPassport checks if the given passport is available for registration.
func (c *ControllerV1) CheckPassport(ctx context.Context, req *v1.CheckPassportReq) (res *v1.CheckPassportRes, err error) {
	available, err := c.userSvc.IsPassportAvailable(ctx, req.Passport)
	if err != nil {
		return nil, err
	}
	if !available {
		return nil, gerror.Newf(`Passport "%s" is already token by others`, req.Passport)
	}
	return
}
