// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates JSON array response handling in a HTTP server using GoFrame.
// It showcases how to:
// 1. Structure and return JSON array responses
// 2. Configure OpenAPI/Swagger documentation
// 3. Use middleware for consistent response handling
// 4. Define type-safe request and response structures
package main

import (
	"context"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
)

// Req defines the request structure for the user endpoint.
// It uses GoFrame's metadata to specify the endpoint path and HTTP method.
type Req struct {
	g.Meta `path:"/user" method:"get"`
}

// Res defines the response structure as a slice of Item.
// This will be serialized as a JSON array in the response.
type Res []Item

// Item represents a single user item in the response array.
// Each field will be properly serialized in the JSON response.
type Item struct {
	Id   int64  `json:"id" dc:"User ID"`
	Name string `json:"name" dc:"User name"`
}

// User is the controller structure for handling user-related requests.
type User struct{}

// GetList handles the user list endpoint request.
// It returns a list of users as a JSON array.
func (User) GetList(ctx context.Context, req *Req) (res *Res, err error) {
	res = &Res{
		{Id: 1, Name: "john"},
		{Id: 2, Name: "smith"},
		{Id: 3, Name: "alice"},
	}
	return
}

// main initializes and starts the HTTP server with OpenAPI documentation.
// The server provides:
// 1. A /user endpoint returning JSON array response
// 2. OpenAPI documentation at /api
// 3. Swagger UI at /swagger
func main() {
	s := g.Server()
	// Configure routing group with response handler middleware
	s.Group("/", func(group *ghttp.RouterGroup) {
		group.Middleware(ghttp.MiddlewareHandlerResponse)
		group.Bind(
			new(User),
		)
	})
	// Configure OpenAPI documentation
	oai := s.GetOpenApi()
	oai.Config.CommonResponse = ghttp.DefaultHandlerResponse{}
	oai.Config.CommonResponseDataField = "Data"
	// Set up API documentation paths
	s.SetOpenApiPath("/api")
	s.SetSwaggerPath("/swagger")
	s.SetPort(8000)
	s.Run()
}
