// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

package main

import (
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/redis/go-redis/v9"
)

// main demonstrates basic Redis operations using GoFrame
// It initializes a Redis client and performs simple SET/GET operations
func main() {
	// Get the initialization context
	ctx := gctx.GetInitCtx()
	
	// Initialize Redis client with error handling
	redisClient, err := NewRedisClient()
	if err != nil {
		panic(err)
	}

	// Demonstrate basic Redis operations
	redisClient.Set(ctx, "key", "value", 0)
	redisClient.Get(ctx, "key")
	g.Log().Info(ctx, `key:`, redisClient.Get(ctx, "key").Val())
}

// RedisConfig defines the configuration structure for Redis connection
type RedisConfig struct {
	Address  string // Redis server address in format "host:port"
	Password string // Redis server password, empty if no password is set
}

// NewRedisClient creates and initializes a new Redis client using configuration from config.yaml
// Returns the initialized client and any error encountered during initialization
func NewRedisClient() (*redis.Client, error) {
	var (
		err    error
		ctx    = gctx.GetInitCtx()
		config *RedisConfig
	)
	
	// Load Redis configuration from config.yaml
	err = g.Cfg().MustGet(ctx, "redis").Scan(&config)
	if err != nil {
		return nil, err
	}
	if config == nil {
		return nil, gerror.New("redis config not found")
	}
	g.Log().Debugf(ctx, "Redis Config: %s", config)

	// Initialize Redis client with the loaded configuration
	redisClient := redis.NewClient(&redis.Options{
		Addr:     config.Address,
		Password: config.Password,
	})
	
	// Test the connection by sending a PING command
	err = redisClient.Ping(ctx).Err()
	return redisClient, err
}
