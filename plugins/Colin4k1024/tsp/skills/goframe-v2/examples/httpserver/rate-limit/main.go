// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates rate limiting implementation in a HTTP server using GoFrame.
// It showcases how to:
// 1. Implement a rate limiting middleware using token bucket algorithm
// 2. Create a simple REST API endpoint with request validation
// 3. Handle rate limit exceeded scenarios properly
package main

import (
	"context"
	"fmt"

	"golang.org/x/time/rate"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
)

// HelloReq defines the request structure for the hello endpoint.
// It uses GoFrame's metadata to specify the endpoint path and HTTP method,
// and includes validation rules for the parameters.
type HelloReq struct {
	g.Meta `path:"/hello" method:"get" sort:"1"`
	Name   string `v:"required" dc:"Your name"` // Name parameter with required validation
}

// HelloRes defines the response structure for the hello endpoint.
type HelloRes struct {
	Reply string `dc:"Reply content"` // Reply message in the response
}

// Hello is the controller structure for handling hello requests.
type Hello struct{}

// Say handles the hello endpoint request.
// It receives a name parameter and returns a greeting message.
func (Hello) Say(ctx context.Context, req *HelloReq) (res *HelloRes, err error) {
	g.Log().Debugf(ctx, `receive say: %+v`, req)
	res = &HelloRes{
		Reply: fmt.Sprintf(`Hi %s`, req.Name),
	}
	return
}

// limiter is a global rate limiter instance using token bucket algorithm.
// It allows 10 requests per second with a burst size of 1.
// Note: In production environments, consider using a distributed rate limiter.
var limiter = rate.NewLimiter(rate.Limit(10), 1)

// Limiter is a middleware that implements rate limiting for all HTTP requests.
// It returns HTTP 429 (Too Many Requests) when the rate limit is exceeded.
func Limiter(r *ghttp.Request) {
	if !limiter.Allow() {
		r.Response.WriteStatusExit(429) // Return 429 Too Many Requests
		r.ExitAll()
	}
	r.Middleware.Next()
}

// main initializes and starts the HTTP server with rate limiting middleware.
// Example usage:
// curl "http://127.0.0.1:8080/hello?name=world"
func main() {
	s := g.Server()
	// Register global middlewares
	s.Use(Limiter, ghttp.MiddlewareHandlerResponse)
	// Configure routing group
	s.Group("/", func(group *ghttp.RouterGroup) {
		group.Bind(
			new(Hello),
		)
	})
	s.SetPort(8080)
	s.Run()
}
