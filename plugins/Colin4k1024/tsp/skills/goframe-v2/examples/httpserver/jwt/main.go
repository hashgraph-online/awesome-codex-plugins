package main

import (
	"main/internal/controller"
	"main/internal/middleware"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
)

// main is the entry point of the application
// It sets up the HTTP server with JWT authentication
func main() {
	s := g.Server()

	// Enable default middleware for standardized response handling
	s.Use(ghttp.MiddlewareHandlerResponse)

	// Create auth controller instance
	auth := controller.Auth{}

	s.Group("/", func(group *ghttp.RouterGroup) {
		// Public endpoints
		group.Bind(
			auth.Login,
		)

		// Protected endpoints requiring JWT authentication
		group.Group("/api", func(group *ghttp.RouterGroup) {
			group.Middleware(middleware.JWTAuth)
			group.Bind(
				auth.Protected,
			)
		})
	})

	s.SetPort(8000)
	s.Run()
}
