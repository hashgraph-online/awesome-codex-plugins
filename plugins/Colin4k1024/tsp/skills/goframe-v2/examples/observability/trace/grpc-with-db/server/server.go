// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates gRPC server implementation with distributed tracing and database operations.
// It showcases how to:
// 1. Configure distributed tracing
// 2. Implement database operations
// 3. Handle trace propagation
// 4. Manage cache with Redis
//
// This example shows how to implement a gRPC server that traces
// both service calls and database operations.
package main

import (
	"context"
	"fmt"
	"time"

	_ "github.com/gogf/gf/contrib/drivers/mysql/v2"
	_ "github.com/gogf/gf/contrib/nosql/redis/v2"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gcache"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/registry/etcd/v2"
	"github.com/gogf/gf/contrib/rpc/grpcx/v2"
	"github.com/gogf/gf/contrib/trace/otlpgrpc/v2"

	"main/protobuf/user"
)

// Controller implements the User service with tracing
type Controller struct {
	user.UnimplementedUserServer
}

// Service configuration constants
const (
	serviceName = "otlp-grpc-server"                         // Name of the service for tracing
	endpoint    = "tracing-analysis-dc-bj.aliyuncs.com:8090" // Tracing endpoint
	traceToken  = "******_******"                            // Token for authentication
)

// main initializes and starts a gRPC server with tracing
func main() {
	// Configure service discovery
	grpcx.Resolver.Register(etcd.New("127.0.0.1:2379"))

	var (
		ctx           = gctx.New()
		shutdown, err = otlpgrpc.Init(serviceName, endpoint, traceToken)
	)

	if err != nil {
		g.Log().Fatal(ctx, err)
	}
	defer shutdown(ctx)

	// Configure Redis as the cache adapter for ORM
	// This enables caching of database queries
	g.DB().GetCache().SetAdapter(gcache.NewAdapterRedis(g.Redis()))

	// Create and start the gRPC server
	s := grpcx.Server.New()
	user.RegisterUserServer(s.Server, &Controller{})
	s.Run()
}

// Insert implements the Insert RPC method.
// This method:
// 1. Receives user data
// 2. Inserts into database
// 3. Returns the inserted ID
// 4. Traces the operation
func (s *Controller) Insert(ctx context.Context, req *user.InsertReq) (res *user.InsertRes, err error) {
	// Insert user data into database
	// The operation is automatically traced
	result, err := g.Model("user").Ctx(ctx).Insert(g.Map{
		"name": req.Name,
	})
	if err != nil {
		return nil, err
	}

	// Get and return the inserted ID
	id, _ := result.LastInsertId()
	res = &user.InsertRes{
		Id: int32(id),
	}
	return
}

// Query implements the Query RPC method.
// This method:
// 1. Checks Redis cache
// 2. Falls back to database
// 3. Updates cache
// 4. Traces all operations
func (s *Controller) Query(ctx context.Context, req *user.QueryReq) (res *user.QueryRes, err error) {
	// Query with cache support
	// If data exists in cache, it will be returned directly
	// Otherwise, database will be queried
	if err = g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
		Duration: 5 * time.Second,
		Name:     s.userCacheKey(req.Id),
		Force:    false,
	}).WherePri(req.Id).Scan(&res); err != nil {
		return nil, err
	}
	return
}

// Delete implements the Delete RPC method.
// This method:
// 1. Deletes user data
// 2. Invalidates cache
// 3. Traces the operation
func (s *Controller) Delete(ctx context.Context, req *user.DeleteReq) (res *user.DeleteRes, err error) {
	// Delete user and invalidate cache
	// Setting Duration to -1 removes the cache entry
	err = g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
		Duration: -1,
		Name:     s.userCacheKey(req.Id),
		Force:    false,
	}).WherePri(req.Id).Scan(&res)
	return
}

// userCacheKey generates a cache key for a user ID
func (s *Controller) userCacheKey(id int32) string {
	return fmt.Sprintf(`userInfo:%d`, id)
}
