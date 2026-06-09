package v1

import (
	"time"

	"github.com/gogf/gf/v2/frame/g"
)

// LoginReq is the request struct for login
type LoginReq struct {
	g.Meta   `path:"/login" method:"post" tags:"Auth" summary:"User login api"`
	Username string `v:"required#Please input username" dc:"Username for authentication"`
	Password string `v:"required#Please input password" dc:"Password for authentication"`
}

// LoginRes is the response struct for login
type LoginRes struct {
	Token string `json:"token" dc:"JWT token for authentication"`
}

// ProtectedReq is the request struct for protected endpoint
type ProtectedReq struct {
	g.Meta `path:"/protected" method:"get" tags:"Auth" summary:"Protected api that requires authentication"`
}

// ProtectedRes is the response struct for protected endpoint
type ProtectedRes struct {
	Username string    `json:"username" dc:"Username from JWT token"`
	Time     time.Time `json:"time"     dc:"Current server time"`
}
