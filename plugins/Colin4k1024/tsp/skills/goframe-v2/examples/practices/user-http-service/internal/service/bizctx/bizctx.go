package bizctx

import (
	"context"

	"github.com/gogf/gf/v2/net/ghttp"
)

type (
	// Service provides business context related logic.
	Service struct{}
)

const (
	ContextKey = "ContextKey"
)

// Context defines the business context object, which is injected into request context and used in business logic.
type Context struct {
	Session *ghttp.Session // Session in context.
	User    *User          // User in context.
}

// User defines the business user object, which is injected into request context and used in business logic.
type User struct {
	Id       uint   // User ID.
	Passport string // User passport.
	Nickname string // User nickname.
}

// New creates and returns a new Service instance.
func New() *Service {
	return &Service{}
}

// Init initializes and injects custom business context object into request context.
func (s *Service) Init(r *ghttp.Request, customCtx *Context) {
	r.SetCtxVar(ContextKey, customCtx)
}

// Get retrieves and returns the user object from context.
// It returns nil if nothing found in given context.
func (s *Service) Get(ctx context.Context) *Context {
	value := ctx.Value(ContextKey)
	if value == nil {
		return nil
	}
	if localCtx, ok := value.(*Context); ok {
		return localCtx
	}
	return nil
}

// SetUser injects business user object into context.
func (s *Service) SetUser(ctx context.Context, ctxUser *User) {
	s.Get(ctx).User = ctxUser
}
