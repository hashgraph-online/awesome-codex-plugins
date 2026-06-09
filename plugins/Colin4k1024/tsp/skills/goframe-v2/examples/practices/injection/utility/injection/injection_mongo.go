package injection

import (
	"context"

	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/samber/do"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// SetupShutdownHelper sets up a shutdown helper.
func injectMongo(ctx context.Context, injector *do.Injector) {
	do.Provide(injector, func(i *do.Injector) (*mongo.Database, error) {
		type MongoConfig struct {
			Address  string
			Database string
		}
		var (
			err    error
			config *MongoConfig
		)
		err = g.Cfg().MustGet(ctx, "mongo").Scan(&config)
		if err != nil {
			return nil, err
		}
		if config == nil {
			return nil, gerror.New("mongo config not found")
		}
		g.Log().Debugf(ctx, "Mongo Config: %s", config)
		clientOptions := options.Client().ApplyURI(config.Address)
		client, err := mongo.Connect(ctx, clientOptions)
		if err != nil {
			return nil, err
		}
		svc := client.Database(config.Database)
		SetupShutdownHelper(injector, svc, func(svc *mongo.Database) error {
			return svc.Client().Disconnect(context.Background())
		})
		return svc, nil
	})
}
