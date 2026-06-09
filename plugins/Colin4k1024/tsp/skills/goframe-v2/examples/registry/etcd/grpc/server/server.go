// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

package main

import (
	"github.com/gogf/gf/contrib/registry/etcd/v2"
	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/grpc/controller"
)

// docker run -d --name etcd -p 2379:2379 -e ALLOW_NONE_AUTHENTICATION=yes bitnami/etcd:3.4.24
func main() {
	grpcx.Resolver.Register(etcd.New("127.0.0.1:2379"))

	s := grpcx.Server.New()
	controller.Register(s)
	s.Run()
}
