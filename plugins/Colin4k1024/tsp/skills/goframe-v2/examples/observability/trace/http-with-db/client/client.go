// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP client implementation with distributed tracing.
// It showcases how to:
// 1. Configure distributed tracing
// 2. Make traced HTTP requests
// 3. Handle trace propagation
// 4. Set trace baggage
//
// This example shows how to implement an HTTP client that traces
// all requests to the server.
package main

import (
	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/net/gtrace"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/trace/otlphttp/v2"
)

// Service configuration constants
const (
	serviceName = "otlp-http-client-with-db"            // Name of the service for tracing
	endpoint    = "tracing-analysis-dc-hz.aliyuncs.com" // Tracing endpoint
	path        = "adapt_******_******/api/otlp/traces" // Tracing path
)

// main initializes and starts an HTTP client with tracing
func main() {
	var (
		ctx           = gctx.New()
		shutdown, err = otlphttp.Init(serviceName, endpoint, path)
	)
	if err != nil {
		g.Log().Fatal(ctx, err)
	}
	defer shutdown(ctx)

	StartRequests()
}

// StartRequests demonstrates traced HTTP requests.
// This function:
// 1. Creates a new trace span
// 2. Makes HTTP requests with tracing
// 3. Handles responses and errors
func StartRequests() {
	// Create a new trace span
	ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
	defer span.End()

	var (
		err    error
		client = g.Client()
	)
	// Add user info.
	// This operation will be traced
	var insertRes = struct {
		ghttp.DefaultHandlerResponse
		Data struct{ ID int64 } `json:"data"`
	}{}
	err = client.PostVar(ctx, "http://127.0.0.1:8000/user/insert", g.Map{
		"name": "john",
	}).Scan(&insertRes)
	if err != nil {
		panic(err)
	}
	g.Log().Info(ctx, "insert result:", insertRes)
	if insertRes.Data.ID == 0 {
		g.Log().Error(ctx, "retrieve empty id string")
		return
	}

	// Query user info.
	// This operation will be traced
	var queryRes = struct {
		ghttp.DefaultHandlerResponse
		Data struct{ User gdb.Record } `json:"data"`
	}{}
	err = client.GetVar(ctx, "http://127.0.0.1:8000/user/query", g.Map{
		"id": insertRes.Data.ID,
	}).Scan(&queryRes)
	if err != nil {
		panic(err)
	}
	g.Log().Info(ctx, "query result:", queryRes)

	// Delete user info.
	// This operation will be traced
	var deleteRes = struct {
		ghttp.DefaultHandlerResponse
	}{}
	err = client.PostVar(ctx, "http://127.0.0.1:8000/user/delete", g.Map{
		"id": insertRes.Data.ID,
	}).Scan(&deleteRes)
	if err != nil {
		panic(err)
	}
	g.Log().Info(ctx, "delete result:", deleteRes)
}
