package injection

import (
	"context"
	"fmt"
	"reflect"
	"sync"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/samber/do"
)

var (
	defaultInjector     *do.Injector
	defaultInjectorOnce sync.Once
)

// MustInvoke invokes the function with the default injector and panics if any error occurs.
func MustInvoke[T any]() T {
	return do.MustInvoke[T](defaultInjector)
}

// Invoke invokes the function with the default injector.
func Invoke[T any]() (T, error) {
	return do.Invoke[T](defaultInjector)
}

// SetupDefaultInjector initializes the default injector with the given context.
func SetupDefaultInjector(ctx context.Context) *do.Injector {
	defaultInjectorOnce.Do(func() { // make sure this is only called once
		injector := do.NewWithOpts(&do.InjectorOpts{})

		injectMongo(ctx, injector)
		injectRedis(ctx, injector)
		injectGrpcClients(ctx, injector)

		defaultInjector = injector
	})
	return defaultInjector
}

// ShutdownDefaultInjector shuts down the default injector.
func ShutdownDefaultInjector() {
	if defaultInjector != nil {
		if err := defaultInjector.Shutdown(); err != nil {
			g.Log().Debugf(context.Background(), "ShutdownDefaultInjector: %+v", err)
		}
		defaultInjector = nil
	}
}

// SetupShutdownHelper sets up a shutdown helper.
func SetupShutdownHelper[T any](injector *do.Injector, service T, onShutdown func(service T) error) {
	do.Provide(injector, func(i *do.Injector) (ShutdownHelper[T], error) {
		g.Log().Debugf(context.Background(), "NewShutdownHelper: %s", reflect.TypeOf(service))
		return NewShutdownHelper(service, onShutdown), nil
	})
	do.MustInvoke[ShutdownHelper[T]](injector)
}

// SetupShutdownHelperNamed sets up a shutdown helper with a name.
func SetupShutdownHelperNamed[T any](injector *do.Injector, service T, name string, onShutdown func(service T) error) {
	name = fmt.Sprintf("ShutdownHelper:%s", name)
	do.ProvideNamed(injector, name, func(i *do.Injector) (ShutdownHelper[T], error) {
		g.Log().Debugf(
			context.Background(),
			"NewShutdownHelper: %s, %s",
			reflect.TypeOf(service), name,
		)
		return NewShutdownHelperNamed(service, name, onShutdown), nil
	})
	do.MustInvokeNamed[ShutdownHelper[T]](injector, name)
}

// ShutdownHelper is a helper struct for shutdown.
type ShutdownHelper[T any] struct {
	name       string
	service    T
	onShutdown func(service T) error
}

// NewShutdownHelper creates a new ShutdownHelper.
func NewShutdownHelper[T any](service T, onShutdown func(service T) error) ShutdownHelper[T] {
	return ShutdownHelper[T]{
		service:    service,
		onShutdown: onShutdown,
	}
}

// NewShutdownHelperNamed creates a new ShutdownHelper with a name.
func NewShutdownHelperNamed[T any](service T, name string, onShutdown func(service T) error) ShutdownHelper[T] {
	return ShutdownHelper[T]{
		name:       name,
		service:    service,
		onShutdown: onShutdown,
	}
}

// Shutdown shuts down the service.
func (h ShutdownHelper[T]) Shutdown() error {
	g.Log().Debugf(
		context.Background(),
		"ShutdownHelper Shutdown: %s, %s",
		reflect.TypeOf(h.service), h.name,
	)
	return h.onShutdown(h.service)
}
