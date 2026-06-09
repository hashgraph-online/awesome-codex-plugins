package user

import (
	"context"
	"time"

	"practices/injection/app/user/internal/model/entity"

	"github.com/gogf/gf/v2/util/gconv"
	"github.com/pkg/errors"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// Dao defines the interface for user data access operations.
type Dao interface {
	// Create creates a new user and returns its ID.
	Create(ctx context.Context, in CreateInput) (string, error)

	// Update modifies an existing user by ID.
	Update(ctx context.Context, id primitive.ObjectID, in UpdateInput) error

	// Delete removes users by their IDs (hard delete).
	Delete(ctx context.Context, id []primitive.ObjectID) error

	// GetOne retrieves a single user by ID.
	GetOne(ctx context.Context, id primitive.ObjectID) (*entity.User, error)

	// GetList retrieves a list of users based on input criteria.
	GetList(ctx context.Context, in GetListInput) ([]*entity.User, error)
}

// implDao implements the Dao interface using MongoDB.
type implDao struct {
	database   *mongo.Database      // MongoDB database instance
	collection *mongo.Collection    // Collection for user data
	fields     collectionFieldNames // Field names mapping
}

// collectionFieldNames defines the mapping of struct fields to MongoDB field names.
type collectionFieldNames struct {
	Id        string // MongoDB document ID field
	Name      string // User name field
	CreatedAt string // Creation timestamp field
	UpdatedAt string // Update timestamp field
}

// New creates a new instance of the Dao interface.
// It initializes the MongoDB collection and field mappings.
func New(db *mongo.Database) Dao {
	return &implDao{
		database:   db,
		collection: db.Collection("user"),
		fields: collectionFieldNames{
			Id:        "_id",
			Name:      "name",
			CreatedAt: "created_at",
			UpdatedAt: "updated_at",
		},
	}
}

// CreateInput defines the input data for creating a new user.
type CreateInput struct {
	Name string `bson:"name,omitempty"`
}

// Create creates a new user in the database.
func (d *implDao) Create(ctx context.Context, in CreateInput) (string, error) {
	var dataItem = entity.User{
		CreatedAt: time.Now().UnixMilli(),
		UpdatedAt: time.Now().UnixMilli(),
	}
	if err := gconv.Scan(in, &dataItem); err != nil {
		return "", err
	}
	result, err := d.collection.InsertOne(ctx, dataItem)
	if err != nil {
		return "", errors.Wrap(err, "insert user data failed")
	}
	return result.InsertedID.(primitive.ObjectID).Hex(), nil
}

// UpdateInput defines the input data for updating a user.
type UpdateInput struct {
	Name string `bson:"name,omitempty"`
}

// Update modifies an existing user in the database.
func (d *implDao) Update(ctx context.Context, id primitive.ObjectID, in UpdateInput) error {
	var dataItem = entity.User{
		UpdatedAt: time.Now().UnixMilli(),
	}
	if err := gconv.Scan(in, &dataItem); err != nil {
		return err
	}
	filter := bson.D{
		{d.fields.Id, id},
	}
	update := bson.M{
		"$set": dataItem,
	}
	_, err := d.collection.UpdateOne(ctx, filter, update)
	if err != nil {
		return errors.Wrap(err, "update user data failed")
	}
	return nil
}

// Delete removes users from the database (hard delete).
func (d *implDao) Delete(ctx context.Context, ids []primitive.ObjectID) error {
	if len(ids) == 0 {
		return nil
	}
	filter := bson.D{
		{d.fields.Id, bson.M{"$in": ids}},
	}
	_, err := d.collection.DeleteMany(ctx, filter)
	if err != nil {
		return errors.Wrap(err, "delete user data failed")
	}
	return nil
}

// GetOne retrieves a single user from the database by ID.
func (d *implDao) GetOne(ctx context.Context, id primitive.ObjectID) (*entity.User, error) {
	var (
		dataItem *entity.User
		filter   = bson.D{
			{d.fields.Id, id},
		}
	)
	err := d.collection.FindOne(ctx, filter).Decode(&dataItem)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, nil
		}
		return nil, errors.Wrap(err, "find one user data failed")
	}
	return dataItem, nil
}

// GetListInput defines the input criteria for listing users.
type GetListInput struct {
	Ids []primitive.ObjectID // List of user IDs to query
}

// GetList retrieves a list of users from the database based on the input criteria.
func (d *implDao) GetList(ctx context.Context, in GetListInput) ([]*entity.User, error) {
	var (
		filter = bson.D{}
		opts   = options.Find().SetSort(bson.M{d.fields.Id: 1})
	)
	if len(in.Ids) > 0 {
		filter = append(filter, bson.E{Key: d.fields.Id, Value: bson.M{"$in": in.Ids}})
	}
	cur, err := d.collection.Find(ctx, filter, opts)
	if err != nil {
		return nil, errors.Wrap(err, `search GetList failed`)
	}
	defer cur.Close(ctx)
	// Scan results into entity objects
	var dataItems = make([]*entity.User, 0)
	if err = cur.All(ctx, &dataItems); err != nil {
		return nil, errors.Wrap(err, `mongodb scan result failed`)
	}
	return dataItems, nil
}
