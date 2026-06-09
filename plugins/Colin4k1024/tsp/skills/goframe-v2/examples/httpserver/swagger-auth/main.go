// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates how to implement Basic Authentication for Swagger API documentation
// using the GoFrame framework. It includes a simple REST API endpoint and protected Swagger docs.
package main

import (
	"context"
	"fmt"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
)

// HelloReq defines the request structure for the hello endpoint.
// It uses path and method tags for routing configuration and validation tags for input validation.
type HelloReq struct {
	g.Meta `path:"/hello" method:"get" sort:"1"` // API endpoint configuration
	Name   string `v:"required" dc:"Your name"`    // Required parameter with description
}

// HelloRes defines the response structure for the hello endpoint.
type HelloRes struct {
	Reply string `dc:"Reply content"` // Response field with description
}

// Hello is the controller structure for handling hello endpoint requests.
type Hello struct{}

// Say handles the hello endpoint request and returns a greeting message.
// It demonstrates simple request handling and response generation.
func (Hello) Say(ctx context.Context, req *HelloReq) (res *HelloRes, err error) {
	res = &HelloRes{
		Reply: fmt.Sprintf(`Hi %s`, req.Name),
	}
	return
}

// main initializes and starts the HTTP server with Swagger documentation
// and Basic Authentication protection.
func main() {
	s := g.Server()
	// Enable automatic response wrapping
	s.Use(ghttp.MiddlewareHandlerResponse)
	// Configure OpenAPI and Swagger paths
	s.SetOpenApiPath("/api.json")
	s.SetSwaggerPath("/swagger")
	// Configure routing group with authentication
	s.Group("/", func(group *ghttp.RouterGroup) {
		// Add Basic Authentication to OpenAPI documentation
		group.Hook(s.GetOpenApiPath(), ghttp.HookBeforeServe, openApiBasicAuth)
		// Bind controller
		group.Bind(
			new(Hello),
		)
	})
	// Set server port and start
	s.SetPort(8000)
	s.Run()
}

// openApiBasicAuth implements Basic Authentication for the OpenAPI documentation.
// It requires username 'admin' and password '123456' for access.
func openApiBasicAuth(r *ghttp.Request) {
	if !r.BasicAuth("admin", "123456", "Restricted") {
		r.ExitAll()
		return
	}
}
