package v1

import "github.com/gogf/gf/v2/frame/g"

// IsSignedInReq defines the request structure for checking if the current user is signed in.
type IsSignedInReq struct {
	g.Meta `path:"/user/is-signed-in" method:"post" tags:"UserService" summary:"Check current user is already signed-in"`
}
type IsSignedInRes struct {
	OK bool `dc:"True if current user is signed in; or else false"`
}
