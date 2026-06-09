// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

package main

import (
	"time"

	"github.com/gogf/gf/v2/encoding/gjson"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// UserItem represents a user document in MongoDB
// Using BSON tags to map struct fields to MongoDB document fields
type UserItem struct {
	Id        primitive.ObjectID `bson:"_id,omitempty"`  // MongoDB document ID
	Name      string            `bson:"name,omitempty"`  // User name
	CreatedAt int64             `bson:"created_at,omitempty"` // Creation timestamp
	UpdatedAt int64             `bson:"updated_at,omitempty"` // Last update timestamp
}

// main demonstrates basic MongoDB operations using GoFrame
// Including connection, CRUD operations with proper error handling
func main() {
	// Get the initialization context
	ctx := gctx.GetInitCtx()

	// Initialize MongoDB client
	mongoClient, err := NewMongoClient()
	if err != nil {
		panic(err)
	}
	var (
		db         = mongoClient.Database("test")
		collection = db.Collection("user")
	)

	// Create: Insert a new user document
	var dataItem = UserItem{
		Name:      "john",
		CreatedAt: time.Now().UnixMilli(),
		UpdatedAt: time.Now().UnixMilli(),
	}
	result, err := collection.InsertOne(ctx, dataItem)
	if err != nil {
		panic(err)
	}
	g.Log().Infof(ctx, "InsertId: %s", result.InsertedID)

	// Query: Find the inserted user document
	var user UserItem
	err = collection.FindOne(ctx, bson.M{"_id": result.InsertedID}).Decode(&user)
	if err != nil {
		panic(err)
	}
	g.Log().Infof(ctx, "Queried: %s", gjson.MustEncodeString(user))

	// Update: Modify the user document
	_, err = collection.UpdateOne(
		ctx,
		bson.M{
			"_id": result.InsertedID,
		},
		bson.M{
			"$set": bson.M{
				"name":       "alice",
				"updated_at": time.Now().UnixMilli(),
			},
		},
	)
	if err != nil {
		panic(err)
	}

	// Query: Retrieve the updated user document
	err = collection.FindOne(ctx, bson.M{"_id": result.InsertedID}).Decode(&user)
	if err != nil {
		panic(err)
	}
	g.Log().Infof(ctx, "Updated and queried again: %s", gjson.MustEncodeString(user))
}

// MongoConfig defines the configuration structure for MongoDB connection
type MongoConfig struct {
	Address  string // MongoDB server address in URI format
	Database string // Target database name
}

// NewMongoClient creates and initializes a new MongoDB client using configuration from config.yaml
// Returns the initialized client and any error encountered during initialization
func NewMongoClient() (*mongo.Client, error) {
	var (
		err    error
		ctx    = gctx.GetInitCtx()
		config *MongoConfig
	)
	// Load MongoDB configuration from config.yaml
	err = g.Cfg().MustGet(ctx, "mongo").Scan(&config)
	if err != nil {
		return nil, err
	}
	if config == nil {
		return nil, gerror.New("mongo config not found")
	}
	g.Log().Debugf(ctx, "Mongo Config: %s", config)

	// Initialize MongoDB client with the loaded configuration
	clientOptions := options.Client().ApplyURI(config.Address)
	return mongo.Connect(ctx, clientOptions)
}
