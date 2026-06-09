package user

import (
	"context"
	"testing"

	v1 "practices/injection/app/user/api/user/v1"
	"practices/injection/utility/injection"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/test/gtest"
)

// newUserControllerForTest creates a new controller instance for testing
func newUserControllerForTest() (*ControllerV1, context.Context) {
	ctx := context.TODO()
	injection.SetupDefaultInjector(ctx)
	return newUserController(), ctx
}

// Test_Create tests the Create method of the controller
func Test_Create(t *testing.T) {
	ctrl, ctx := newUserControllerForTest()

	gtest.C(t, func(t *gtest.T) {
		// Test successful creation
		res, err := ctrl.Create(ctx, &v1.CreateReq{Name: "john"})
		t.AssertNil(err)
		t.AssertNE(res.Id, "")

		g.Log().Debug(ctx, "Created user ID:", res.Id)

		// Test creation with empty name
		_, err = ctrl.Create(ctx, &v1.CreateReq{Name: ""})
		t.AssertNE(err, nil)
	})
}

// Test_GetOne tests the GetOne method of the controller
func Test_GetOne(t *testing.T) {
	ctrl, ctx := newUserControllerForTest()

	gtest.C(t, func(t *gtest.T) {
		// First create a user
		createRes, err := ctrl.Create(ctx, &v1.CreateReq{Name: "test_user"})
		t.AssertNil(err)

		// Test getting the created user
		getRes, err := ctrl.GetOne(ctx, &v1.GetOneReq{Id: createRes.Id})
		t.AssertNil(err)
		t.Assert(getRes.Data.Name, "test_user")

		// Test getting non-existent user
		_, err = ctrl.GetOne(ctx, &v1.GetOneReq{Id: "non_existent_id"})
		t.AssertNE(err, nil)
	})
}

// Test_GetList tests the GetList method of the controller
func Test_GetList(t *testing.T) {
	ctrl, ctx := newUserControllerForTest()

	gtest.C(t, func(t *gtest.T) {
		// Create two users first
		user1, err := ctrl.Create(ctx, &v1.CreateReq{Name: "user1"})
		t.AssertNil(err)
		user2, err := ctrl.Create(ctx, &v1.CreateReq{Name: "user2"})
		t.AssertNil(err)

		// Test getting list with specific IDs
		listRes, err := ctrl.GetList(ctx, &v1.GetListReq{Ids: []string{user1.Id, user2.Id}})
		t.AssertNil(err)
		t.Assert(len(listRes.List), 2)

		// Test getting all users (empty IDs)
		allRes, err := ctrl.GetList(ctx, &v1.GetListReq{})
		t.AssertNil(err)
		t.AssertGE(len(allRes.List), 2)

		// Test getting list with non-existent IDs
		nonExistRes, err := ctrl.GetList(ctx, &v1.GetListReq{Ids: []string{"non_existent_id"}})
		t.AssertNil(err)
		t.Assert(len(nonExistRes.List), 0)
	})
}

// Test_Delete tests the Delete method of the controller
func Test_Delete(t *testing.T) {
	ctrl, ctx := newUserControllerForTest()

	gtest.C(t, func(t *gtest.T) {
		// First create a user
		createRes, err := ctrl.Create(ctx, &v1.CreateReq{Name: "to_be_deleted"})
		t.AssertNil(err)

		// Test deleting the created user
		_, err = ctrl.Delete(ctx, &v1.DeleteReq{Id: createRes.Id})
		t.AssertNil(err)

		// Verify deletion by trying to get the user
		_, err = ctrl.GetOne(ctx, &v1.GetOneReq{Id: createRes.Id})
		t.AssertNE(err, nil)

		// Test deleting non-existent user
		_, err = ctrl.Delete(ctx, &v1.DeleteReq{Id: "non_existent_id"})
		t.AssertNE(err, nil)
	})
}
