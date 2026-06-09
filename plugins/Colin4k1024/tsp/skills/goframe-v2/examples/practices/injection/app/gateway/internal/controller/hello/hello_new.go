// =================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// =================================================================================

package hello

import (
	"practices/injection/app/gateway/api/hello"
)

type ControllerV1 struct{}

func NewV1() hello.IHelloV1 {
	return &ControllerV1{}
}
