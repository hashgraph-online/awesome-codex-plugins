// =================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT. 
// =================================================================================

package user

import (
	userapi "practices/user-http-service/api/user"
	usersvc "practices/user-http-service/internal/service/user"
)

// ControllerV1 is the controller for user API version 1.
type ControllerV1 struct {
	userSvc *usersvc.Service
}

func NewV1() userapi.IUserV1 {
	return &ControllerV1{
		userSvc: usersvc.New(),
	}
}
