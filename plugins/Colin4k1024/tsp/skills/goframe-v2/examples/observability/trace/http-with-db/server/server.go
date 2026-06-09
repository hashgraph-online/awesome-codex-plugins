// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP server implementation with distributed tracing and database operations.
// It showcases how to:
// 1. Configure distributed tracing
// 2. Implement database operations with caching
// 3. Handle trace propagation
// 4. Manage error handling and logging
//
// This example shows how to implement an HTTP server that traces
// both service calls and database operations.
package main

import (
	"context"
	"fmt"
	"time"

	_ "github.com/gogf/gf/contrib/drivers/mysql/v2"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/os/gcache"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/trace/otlphttp/v2"
)

// cTrace implements the HTTP handlers with tracing
type cTrace struct{}

// Service configuration constants
const (
	serviceName = "otlp-http-server-with-db"            // Name of the service for tracing
	endpoint    = "tracing-analysis-dc-hz.aliyuncs.com" // Tracing endpoint
	path        = "adapt_******_******/api/otlp/traces" // Tracing path
)

// main initializes and starts an HTTP server with tracing
func main() {
	var (
		ctx           = gctx.New()
		shutdown, err = otlphttp.Init(serviceName, endpoint, path)
	)
	if err != nil {
		g.Log().Fatal(ctx, err)
	}
	defer shutdown(ctx)

	// Set ORM cache adapter with redis.
	g.DB().GetCache().SetAdapter(gcache.NewAdapterRedis(g.Redis()))

	// Start HTTP server.
	s := g.Server()
	s.Use(ghttp.MiddlewareHandlerResponse)
	s.Group("/", func(group *ghttp.RouterGroup) {
		group.ALL("/user", new(cTrace))
	})
	s.SetPort(8000)
	s.Run()
}

// InsertReq is the input parameter for inserting user info.
// Required fields are marked with validation rules.
type InsertReq struct {
	Name string `v:"required#Please input user name."`
}

// InsertRes is the output parameter for inserting user info.
// Contains the ID of the newly inserted user.
type InsertRes struct {
	ID int64
}

// Insert is a route handler for inserting user info into database.
// This method:
// 1. Validates the input request
// 2. Inserts user data into database
// 3. Returns the inserted ID
// 4. Traces the operation
func (c *cTrace) Insert(ctx context.Context, req *InsertReq) (res *InsertRes, err error) {
	result, err := g.Model("user").Ctx(ctx).Insert(req)
	if err != nil {
		return nil, err
	}
	id, _ := result.LastInsertId()
	res = &InsertRes{
		ID: id,
	}
	return
}

// QueryReq is the input parameter for querying user info.
// ID must be greater than 0.
type QueryReq struct {
	ID int `v:"min:1#User id is required for querying"`
}

// QueryRes is the output parameter for querying user info.
// Contains the user record from database.
type QueryRes struct {
	User gdb.Record
}

// Query is a route handler for querying user info. It firstly retrieves the info from redis,
// if there's nothing in the redis, it then does db select.
// This method:
// 1. Checks Redis cache
// 2. Falls back to database if cache miss
// 3. Updates cache with database result
// 4. Traces all operations
func (c *cTrace) Query(ctx context.Context, req *QueryReq) (res *QueryRes, err error) {
	one, err := g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
		Duration: 5 * time.Second,
		Name:     c.userCacheKey(req.ID),
		Force:    false,
	}).WherePri(req.ID).One()
	if err != nil {
		return nil, err
	}
	res = &QueryRes{
		User: one,
	}
	return
}

// DeleteReq is the input parameter for deleting user info.
// Id must be greater than 0.
type DeleteReq struct {
	Id int `v:"min:1#User id is required for deleting."`
}

// DeleteRes is the output parameter for deleting user info.
type DeleteRes struct{}

// Delete is a route handler for deleting specified user info.
// This method:
// 1. Deletes user from database
// 2. Invalidates cache
// 3. Traces the operation
func (c *cTrace) Delete(ctx context.Context, req *DeleteReq) (res *DeleteRes, err error) {
	_, err = g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
		Duration: -1,
		Name:     c.userCacheKey(req.Id),
		Force:    false,
	}).WherePri(req.Id).Delete()
	if err != nil {
		return nil, err
	}
	return
}

// userCacheKey generates a cache key for a user ID
func (c *cTrace) userCacheKey(id int) string {
	return fmt.Sprintf(`userInfo:%d`, id)
}
