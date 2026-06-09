package v1

import (
	"practices/quick-demo/internal/model/entity"

	"github.com/gogf/gf/v2/frame/g"
)

// Status marks user status.
type Status int

const (
	StatusOK       Status = 0 // User is OK.
	StatusDisabled Status = 1 // User is disabled.
)

// CreateReq is the request for creating user.
type CreateReq struct {
	g.Meta `path:"/user" method:"post" tags:"User" summary:"Create user"`
	Name   string `v:"required|length:3,10" dc:"user name"`
	Age    uint   `v:"required|between:18,200" dc:"user age"`
}
type CreateRes struct {
	Id int64 `json:"id" dc:"user id"`
}

// UpdateReq is the request for updating user.
type UpdateReq struct {
	g.Meta `path:"/user/{id}" method:"put" tags:"User" summary:"Update user"`
	Id     int64   `v:"required" dc:"user id"`
	Name   *string `v:"length:3,10" dc:"user name"`
	Age    *uint   `v:"between:18,200" dc:"user age"`
	Status *Status `v:"in:0,1" dc:"user status"`
}
type UpdateRes struct{}

// DeleteReq is the request for deleting user.
type DeleteReq struct {
	g.Meta `path:"/user/{id}" method:"delete" tags:"User" summary:"Delete user"`
	Id     int64 `v:"required" dc:"user id"`
}
type DeleteRes struct{}

// GetOneReq is the request for getting one user.
type GetOneReq struct {
	g.Meta `path:"/user/{id}" method:"get" tags:"User" summary:"Get one user"`
	Id     int64 `v:"required" dc:"user id"`
}
type GetOneRes struct {
	*entity.User `dc:"user"`
}

// GetListReq is the request for getting user list.
type GetListReq struct {
	g.Meta `path:"/user" method:"get" tags:"User" summary:"Get users"`
	Age    *uint   `v:"between:18,200" dc:"user age"`
	Status *Status `v:"in:0,1" dc:"user age"`
}
type GetListRes struct {
	List []*entity.User `json:"list" dc:"user list"`
}
