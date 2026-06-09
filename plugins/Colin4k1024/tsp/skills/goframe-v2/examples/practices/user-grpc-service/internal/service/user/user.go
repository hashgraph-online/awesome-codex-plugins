package user

import (
	"context"

	"practices/user-grpc-service/api/pbentity"
	"practices/user-grpc-service/internal/dao"
	"practices/user-grpc-service/internal/model/do"
)

type (
	// Service provides user-related business logic.
	Service struct{}
)

// New creates and returns a new Service instance.
func New() *Service {
	return &Service{}
}

// GetById retrieves a user by their ID from the database.
func (s *Service) GetById(ctx context.Context, uid uint64) (*pbentity.User, error) {
	var user *pbentity.User
	err := dao.User.Ctx(ctx).Where(do.User{
		Id: uid,
	}).Scan(&user)
	return user, err
}

// DeleteById deletes a user by their ID from the database.
func (s *Service) DeleteById(ctx context.Context, uid uint64) error {
	_, err := dao.User.Ctx(ctx).Where(do.User{
		Id: uid,
	}).Delete()
	return err
}
