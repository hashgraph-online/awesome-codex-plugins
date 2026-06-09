package injection

import (
	"context"

	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/redis/go-redis/v9"
	"github.com/samber/do"
)

// SetupShutdownHelper sets up a shutdown helper.
func injectRedis(ctx context.Context, injector *do.Injector) {
	do.Provide(injector, func(i *do.Injector) (*redis.Client, error) {
		type RedisConfig struct {
			Address  string
			Password string
		}
		var (
			err    error
			config *RedisConfig
		)
		err = g.Cfg().MustGet(ctx, "redis").Scan(&config)
		if err != nil {
			return nil, err
		}
		if config == nil {
			return nil, gerror.New("redis config not found")
		}
		g.Log().Debugf(ctx, "Redis Config: %s", config)
		svc := redis.NewClient(&redis.Options{
			Addr:     config.Address,
			Password: config.Password,
		})
		SetupShutdownHelper(injector, svc, func(svc *redis.Client) error {
			return svc.Close()
		})
		return svc, nil
	})
}
