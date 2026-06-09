package user

import (
	"context"
	"fmt"
	"testing"

	"practices/injection/utility/injection"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/test/gtest"
)

func newUserService() (*Service, context.Context) {
	ctx := context.TODO()
	injection.SetupDefaultInjector(ctx)
	svc := New()
	return svc, ctx
}

func Test_Create(t *testing.T) {
	svc, ctx := newUserService()
	gtest.C(t, func(t *gtest.T) {
		result, err := svc.Create(ctx, "john")
		t.AssertNil(err)
		t.AssertNE(result, "")
		fmt.Println(result)
	})
}

func Test_Delete(t *testing.T) {
	var (
		svc, ctx = newUserService()
		id       = "6708ed8295ec40a90f4db583"
	)
	gtest.C(t, func(t *gtest.T) {
		err := svc.DeleteById(ctx, id)
		t.AssertNil(err)
	})
}

func Test_GetOne(t *testing.T) {
	var (
		svc, ctx = newUserService()
		id       = "67187841da7b7f684b1d8d22"
	)
	one, err := svc.GetById(ctx, id)
	if err != nil {
		t.Error(err)
	}
	g.DumpJson(one)
}

func Test_GetList(t *testing.T) {
	var svc, ctx = newUserService()
	g.Log().Infof(ctx, "默认查询：")
	gtest.C(t, func(t *gtest.T) {
		list, err := svc.GetList(ctx, nil)
		if err != nil {
			t.Error(err)
		}
		g.DumpJson(list)
	})

	g.Log().Infof(ctx, "按照ids查询：")
	gtest.C(t, func(t *gtest.T) {
		var (
			id1 = "67162b3620c191061a0ab0c0"
			id2 = "67162b46c57af6512c59ffea"
		)
		list, err := svc.GetList(ctx, []string{id1, id2})
		if err != nil {
			t.Error(err)
		}
		g.DumpJson(list)
	})

	g.Log().Infof(ctx, "查询不到数据：")
	gtest.C(t, func(t *gtest.T) {
		var (
			id1 = "67162b3620c191061a0ab0c0"
			id2 = "67162b46c57af6512c59ffea"
		)
		list, err := svc.GetList(ctx, []string{id1, id2})
		if err != nil {
			t.Error(err)
		}
		g.DumpJson(list)
	})
}
