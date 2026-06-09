package v1

import (
	"github.com/gogf/gf/v2/frame/g"

	"practices/user-http-service/internal/model/entity"
)

// ProfileReq defines the request structure for getting the profile of the current user.
type ProfileReq struct {
	g.Meta `path:"/user/profile" method:"get" tags:"UserService" summary:"Get the profile of current user"`
}
type ProfileRes struct {
	*entity.User
}
