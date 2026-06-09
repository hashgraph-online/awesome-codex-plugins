package user

import (
	"context"
	"fmt"
	"testing"

	"practices/injection/app/gateway/api/user"
	v1 "practices/injection/app/gateway/api/user/v1"
	"practices/injection/utility/injection"

	"github.com/gogf/gf/v2/test/gtest"
)

func newUserController() (user.IUserV1, context.Context) {
	ctx := context.TODO()
	injection.SetupInjectorProvides(ctx)
	ctrl := NewV1()
	return ctrl, ctx
}

func Test_Create(t *testing.T) {
	svc, ctx := newUserController()
	gtest.C(t, func(t *gtest.T) {
		result, err := svc.Create(ctx, &v1.CreateReq{
			Name: "Alice",
		})
		t.AssertNil(err)
		fmt.Println(result)
	})
}
