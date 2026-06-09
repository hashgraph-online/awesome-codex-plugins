package middleware

import (
	"net/http"

	"practices/user-http-service/internal/service/bizctx"
	"practices/user-http-service/internal/service/session"
	"practices/user-http-service/internal/service/user"

	"github.com/gogf/gf/v2/net/ghttp"
)

// Service provides middleware for HTTP request.
type Service struct {
	bixCtxSvc  *bizctx.Service  // Business context service.
	sessionSvc *session.Service // Session service.
	userSvc    *user.Service    // User service.
}

// New creates and returns a new Service instance.
func New() *Service {
	return &Service{
		bixCtxSvc:  bizctx.New(),
		sessionSvc: session.New(),
		userSvc:    user.New(),
	}
}

// Ctx injects custom business context variable into context of current request.
func (s *Service) Ctx(r *ghttp.Request) {
	customCtx := &bizctx.Context{
		Session: r.Session,
	}
	s.bixCtxSvc.Init(r, customCtx)
	if userItem := s.sessionSvc.GetUser(r.Context()); userItem != nil {
		customCtx.User = &bizctx.User{
			Id:       userItem.Id,
			Passport: userItem.Passport,
			Nickname: userItem.Nickname,
		}
	}
	// Continue execution of next middleware.
	r.Middleware.Next()
}

// Auth validates the request to allow only signed-in users visit.
func (s *Service) Auth(r *ghttp.Request) {
	if s.userSvc.IsSignedIn(r.Context()) {
		r.Middleware.Next()
	} else {
		r.Response.WriteStatus(http.StatusForbidden)
	}
}

// CORS allows Cross-origin resource sharing.
func (s *Service) CORS(r *ghttp.Request) {
	r.Response.CORSDefault()
	r.Middleware.Next()
}
