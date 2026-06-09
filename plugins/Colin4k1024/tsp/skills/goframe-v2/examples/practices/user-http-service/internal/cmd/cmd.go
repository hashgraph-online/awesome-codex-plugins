package cmd

import (
	"context"

	"practices/user-http-service/internal/controller/user"
	"practices/user-http-service/internal/service/middleware"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/net/goai"
	"github.com/gogf/gf/v2/os/gcmd"
)

const (
	OpenAPITitle       = `GoFrame Demos`
	OpenAPIDescription = `This is a simple demos HTTP server project that is using GoFrame. Enjoy 💖 `
)

var (
	// Main is the main command.
	Main = gcmd.Command{
		Name:  "main",
		Usage: "main",
		Brief: "start http server of simple goframe demos",
		Func:  mainFunc,
	}
)

// mainFunc is the main function for the "main" command, which starts the HTTP server and registers route handlers.
func mainFunc(ctx context.Context, parser *gcmd.Parser) (err error) {
	var (
		s             = g.Server()
		middlewareSvc = middleware.New()
	)
	s.Use(ghttp.MiddlewareHandlerResponse)
	s.Group("/", func(group *ghttp.RouterGroup) {
		// Group middlewares.
		group.Middleware(
			middlewareSvc.Ctx,
			ghttp.MiddlewareCORS,
		)
		// Register route handlers.
		var (
			userCtrl = user.NewV1()
		)
		group.Bind(
			userCtrl,
		)

		// Special handler that needs authentication.
		group.Group("/", func(group *ghttp.RouterGroup) {
			group.Middleware(middlewareSvc.Auth)
			group.ALLMap(g.Map{
				"/user/profile": userCtrl.Profile,
			})
		})
	})
	// Custom enhance API document.
	enhanceOpenAPIDoc(s)
	// Just run the server.
	s.Run()
	return nil
}

// enhanceOpenAPIDoc customizes the OpenAPI document for API specification and testing.
// It is optional, and you can customize it as you need, or even remove it if you don't need it.
func enhanceOpenAPIDoc(s *ghttp.Server) {
	openapi := s.GetOpenApi()
	openapi.Config.CommonResponse = ghttp.DefaultHandlerResponse{}
	openapi.Config.CommonResponseDataField = `Data`

	// API description.
	openapi.Info = goai.Info{
		Title:       OpenAPITitle,
		Description: OpenAPIDescription,
		Contact: &goai.Contact{
			Name: "GoFrame",
			URL:  "https://goframe.org",
		},
	}
}
