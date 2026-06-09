package v1

import "github.com/gogf/gf/v2/frame/g"

// SignOutReq defines the request structure for signing out the current user.
type SignOutReq struct {
	g.Meta `path:"/user/sign-out" method:"post" tags:"UserService" summary:"Sign out current user"`
}
type SignOutRes struct{}
