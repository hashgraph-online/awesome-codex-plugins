package user

import (
	"context"
	"fmt"
	"testing"

	"practices/injection/utility/injection"
	"practices/injection/utility/mongohelper"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gtime"
	"github.com/gogf/gf/v2/test/gtest"
	"github.com/samber/do"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
)

func newUserDao() (Dao, context.Context) {
	ctx := context.TODO()
	inject := injection.SetupDefaultInjector(ctx)
	result := New(do.MustInvoke[*mongo.Database](inject))
	return result, ctx
}

func Test_Create(t *testing.T) {
	dao, ctx := newUserDao()
	gtest.C(t, func(t *gtest.T) {
		result, err := dao.Create(ctx, CreateInput{
			Name: "John-" + gtime.TimestampMilliStr(),
		})
		t.AssertNil(err)
		t.AssertNE(result, "")
		fmt.Println(result)
	})
}

func Test_Delete(t *testing.T) {
	var (
		dao, ctx = newUserDao()
		id1      = mongohelper.MustObjectIDFromHex("6708ed8295ec40a90f4db583")
		id2      = mongohelper.MustObjectIDFromHex("670a26ed3b04911806b66ee9")
	)
	gtest.C(t, func(t *gtest.T) {
		err := dao.Delete(ctx, []primitive.ObjectID{id1, id2})
		t.AssertNil(err)
	})
}

func Test_GetOne(t *testing.T) {
	var (
		dao, ctx = newUserDao()
		id       = mongohelper.MustObjectIDFromHex("67187841da7b7f684b1d8d22")
	)
	one, err := dao.GetOne(ctx, id)
	if err != nil {
		t.Error(err)
	}
	g.DumpJson(one)
}

func Test_GetList(t *testing.T) {
	var dao, ctx = newUserDao()
	g.Log().Infof(ctx, "默认查询：")
	gtest.C(t, func(t *gtest.T) {
		list, err := dao.GetList(ctx, GetListInput{})
		if err != nil {
			t.Error(err)
		}
		g.DumpJson(list)
	})

	g.Log().Infof(ctx, "按照ids查询：")
	gtest.C(t, func(t *gtest.T) {
		var (
			id1 = mongohelper.MustObjectIDFromHex("67162b3620c191061a0ab0c0")
			id2 = mongohelper.MustObjectIDFromHex("67162b46c57af6512c59ffea")
		)
		list, err := dao.GetList(ctx, GetListInput{
			Ids: []primitive.ObjectID{id1, id2},
		})
		if err != nil {
			t.Error(err)
		}
		g.DumpJson(list)
	})

	g.Log().Infof(ctx, "查询不到数据：")
	gtest.C(t, func(t *gtest.T) {
		list, err := dao.GetList(ctx, GetListInput{
			Ids: []primitive.ObjectID{primitive.NewObjectID()},
		})
		if err != nil {
			t.Error(err)
		}
		g.DumpJson(list)
	})
}
