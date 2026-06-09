package v1

import "github.com/gogf/gf/v2/frame/g"

type CreateReq struct {
	g.Meta `path:"/user" tags:"User Service" method:"post" summary:"Create User"`
	Name   string `v:"required"`
}
type CreateRes struct {
	Id string `json:"id" dc:"User ID"`
}

type GetOneReq struct {
	g.Meta `path:"/user/{id}" tags:"User Service" method:"get" summary:"Get User Details"`
	Id     string `v:"required" dc:"User ID"`
}
type GetOneRes struct {
	Data ListItem `json:"data" dc:"User Information"`
}

type GetListReq struct {
	g.Meta `path:"/user" tags:"User Service" method:"get" summary:"Get User List"`
	Ids    []string `v:"required" dc:"User ID List"`
}
type GetListRes struct {
	List []ListItem `json:"list" dc:"User List"`
}

type ListItem struct {
	Id        string `json:"id"         dc:"User ID"`
	Name      string `json:"name"       dc:"Username"`
	CreatedAt int64  `json:"created_at" dc:"Creation Time"`
}

type DeleteReq struct {
	g.Meta `path:"/user" tags:"User Service" method:"delete" summary:"Delete User"`
	Id     string `v:"required"`
}
type DeleteRes struct{}
