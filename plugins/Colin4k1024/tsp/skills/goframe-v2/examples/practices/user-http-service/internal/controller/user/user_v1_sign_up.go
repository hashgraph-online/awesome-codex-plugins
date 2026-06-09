package user

import (
	"context"

	"practices/user-http-service/api/user/v1"
	usersvc "practices/user-http-service/internal/service/user"
)

// SignUp signs up the user.
func (c *ControllerV1) SignUp(ctx context.Context, req *v1.SignUpReq) (res *v1.SignUpRes, err error) {
	err = c.userSvc.Create(ctx, usersvc.CreateInput{
		Passport: req.Passport,
		Password: req.Password,
		Nickname: req.Nickname,
	})
	return
}
