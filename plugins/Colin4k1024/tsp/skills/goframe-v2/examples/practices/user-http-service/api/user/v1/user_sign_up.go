package v1

import "github.com/gogf/gf/v2/frame/g"

// SignUpReq defines the request structure for signing up a new user account.
type SignUpReq struct {
	g.Meta    `path:"/user/sign-up" method:"post" tags:"UserService" summary:"Sign up a new user account"`
	Passport  string `v:"required|length:6,16"`
	Password  string `v:"required|length:6,16"`
	Password2 string `v:"required|length:6,16|same:Password"`
	Nickname  string
}
type SignUpRes struct{}
