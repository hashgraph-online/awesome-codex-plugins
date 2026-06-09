// Package user implements the user service layer with dependency injection support.
package user

import (
	"context"

	"practices/injection/app/user/api/entity"
	"practices/injection/app/user/internal/dao/user"
	"practices/injection/utility/injection"
	"practices/injection/utility/mongohelper"

	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/util/gconv"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
)

// Service encapsulates the user business logic with dependency injection.
type Service struct {
	user user.Dao // User data access interface
}

// New creates a new Service instance with injected dependencies.
// It uses the dependency injection container to get the MongoDB database instance.
func New() *Service {
	return &Service{
		user: user.New(injection.MustInvoke[*mongo.Database]()),
	}
}

// Create creates a new user with the given name.
// It returns the created user's ID or an error if the operation fails.
func (s *Service) Create(ctx context.Context, name string) (string, error) {
	if name == "" {
		return "", gerror.New("user name should not be empty")
	}

	result, err := s.user.Create(ctx, user.CreateInput{
		Name: name,
	})
	if err != nil {
		return "", err
	}
	return result, nil
}

// GetById retrieves a user by their ID.
// It returns the user entity or an error if the operation fails.
func (s *Service) GetById(ctx context.Context, id string) (*entity.User, error) {
	if id == "" {
		return nil, gerror.New("user id should not be empty")
	}

	var (
		item   *entity.User
		userId = mongohelper.MustObjectIDFromHex(id)
	)

	result, err := s.user.GetOne(ctx, userId)
	if err != nil {
		return nil, err
	}
	if result == nil {
		return nil, nil
	}

	if err = gconv.Scan(result, &item); err != nil {
		return nil, err
	}
	return item, nil
}

// GetList retrieves a list of users based on the provided IDs.
// If ids is empty, it returns all users.
func (s *Service) GetList(ctx context.Context, ids []string) ([]*entity.User, error) {
	var (
		items   []*entity.User
		userIds []primitive.ObjectID
	)

	// Convert string IDs to ObjectIDs only if IDs are provided
	if len(ids) > 0 {
		userIds = mongohelper.MustObjectIDsFromHexes(ids)
	}

	result, err := s.user.GetList(ctx, user.GetListInput{
		Ids: userIds,
	})
	if err != nil {
		return nil, err
	}

	// Return empty slice if no results
	if len(result) == 0 {
		return make([]*entity.User, 0), nil
	}

	// Convert dao entities to service entities
	if err = gconv.Scan(result, &items); err != nil {
		return nil, err
	}
	return items, nil
}

// DeleteById removes a user by their ID.
// It returns an error if the operation fails.
func (s *Service) DeleteById(ctx context.Context, id string) error {
	if id == "" {
		return gerror.New("user id should not be empty")
	}

	userId := mongohelper.MustObjectIDFromHex(id)
	return s.user.Delete(ctx, []primitive.ObjectID{userId})
}
