package session

import (
	"context"

	"practices/user-http-service/internal/model/entity"
	"practices/user-http-service/internal/service/bizctx"
)

// Service provides session management logic.
type Service struct {
	bizCtxSvc *bizctx.Service // Business context service.
}

const (
	// UserSessionKey is the key used to store user information in session.
	UserSessionKey = "UserSessionKey"
)

// New creates and returns a new Service instance.
func New() *Service {
	return &Service{
		bizCtxSvc: bizctx.New(),
	}
}

// SetUser sets user into the session.
func (s *Service) SetUser(ctx context.Context, user *entity.User) error {
	return s.bizCtxSvc.Get(ctx).Session.Set(UserSessionKey, user)
}

// GetUser retrieves and returns the user from session.
// It returns nil if the user did not sign in.
func (s *Service) GetUser(ctx context.Context) *entity.User {
	customCtx := s.bizCtxSvc.Get(ctx)
	if customCtx != nil {
		if v := customCtx.Session.MustGet(UserSessionKey); !v.IsNil() {
			var user *entity.User
			_ = v.Struct(&user)
			return user
		}
	}
	return nil
}

// RemoveUser removes user rom session.
func (s *Service) RemoveUser(ctx context.Context) error {
	customCtx := s.bizCtxSvc.Get(ctx)
	if customCtx != nil {
		return customCtx.Session.Remove(UserSessionKey)
	}
	return nil
}
