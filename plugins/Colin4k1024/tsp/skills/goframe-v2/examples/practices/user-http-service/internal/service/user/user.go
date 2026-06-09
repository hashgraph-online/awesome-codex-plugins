package user

import (
	"context"

	"practices/user-http-service/internal/dao"
	"practices/user-http-service/internal/model/do"
	"practices/user-http-service/internal/model/entity"
	"practices/user-http-service/internal/service/bizctx"
	"practices/user-http-service/internal/service/session"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/errors/gerror"
)

// Service provides user-related business logic.
type Service struct {
	bizCtxSvc  *bizctx.Service  // Business context service.
	sessionSvc *session.Service // Session service.
}

// New creates and returns a new Service instance.
func New() *Service {
	return &Service{
		bizCtxSvc:  bizctx.New(),
		sessionSvc: session.New(),
	}
}

// CreateInput defines the input for Create function.
type CreateInput struct {
	Passport string
	Password string
	Nickname string
}

// Create creates user account.
func (s *Service) Create(ctx context.Context, in CreateInput) (err error) {
	// If Nickname is not specified, it then uses Passport as its default Nickname.
	if in.Nickname == "" {
		in.Nickname = in.Passport
	}
	var (
		available bool
	)
	// Passport checks.
	available, err = s.IsPassportAvailable(ctx, in.Passport)
	if err != nil {
		return err
	}
	if !available {
		return gerror.Newf(`Passport "%s" is already token by others`, in.Passport)
	}
	// Nickname checks.
	available, err = s.IsNicknameAvailable(ctx, in.Nickname)
	if err != nil {
		return err
	}
	if !available {
		return gerror.Newf(`Nickname "%s" is already token by others`, in.Nickname)
	}
	return dao.User.Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
		_, err = dao.User.Ctx(ctx).Data(do.User{
			Passport: in.Passport,
			Password: in.Password,
			Nickname: in.Nickname,
		}).Insert()
		return err
	})
}

// IsSignedIn checks and returns whether current user is already signed-in.
func (s *Service) IsSignedIn(ctx context.Context) bool {
	if v := s.bizCtxSvc.Get(ctx); v != nil && v.User != nil {
		return true
	}
	return false
}

// SignInInput defines the input for SignIn function.
type SignInInput struct {
	Passport string
	Password string
}

// SignIn creates session for given user account.
func (s *Service) SignIn(ctx context.Context, in SignInInput) (err error) {
	var user *entity.User
	err = dao.User.Ctx(ctx).Where(do.User{
		Passport: in.Passport,
		Password: in.Password,
	}).Scan(&user)
	if err != nil {
		return err
	}
	if user == nil {
		return gerror.New(`Passport or Password not correct`)
	}
	if err = s.sessionSvc.SetUser(ctx, user); err != nil {
		return err
	}
	s.bizCtxSvc.SetUser(ctx, &bizctx.User{
		Id:       user.Id,
		Passport: user.Passport,
		Nickname: user.Nickname,
	})
	return nil
}

// SignOut removes the session for current signed-in user.
func (s *Service) SignOut(ctx context.Context) error {
	return s.sessionSvc.RemoveUser(ctx)
}

// IsPassportAvailable checks and returns given passport is available for signing up.
func (s *Service) IsPassportAvailable(ctx context.Context, passport string) (bool, error) {
	count, err := dao.User.Ctx(ctx).Where(do.User{
		Passport: passport,
	}).Count()
	if err != nil {
		return false, err
	}
	return count == 0, nil
}

// IsNicknameAvailable checks and returns given nickname is available for signing up.
func (s *Service) IsNicknameAvailable(ctx context.Context, nickname string) (bool, error) {
	count, err := dao.User.Ctx(ctx).Where(do.User{
		Nickname: nickname,
	}).Count()
	if err != nil {
		return false, err
	}
	return count == 0, nil
}

// GetProfile retrieves and returns current user info in session.
func (s *Service) GetProfile(ctx context.Context) *entity.User {
	return s.sessionSvc.GetUser(ctx)
}
