// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates distributed tracing across processes using programmatic management.
// It showcases how to:
// 1. Create and manage processes using gproc
// 2. Propagate trace context between processes
// 3. Execute shell commands with context
// 4. Handle process errors and logging
//
// This example uses gproc for programmatic process management and control.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/gogf/gf/v2/os/gproc"
)

// main initializes and runs the main process with trace context.
// It demonstrates:
// 1. Context initialization
// 2. Process logging with trace context
// 3. Sub-process execution with context propagation
// 4. Error handling for process execution
func main() {
	// Initialize context with tracing
	ctx := gctx.GetInitCtx()

	// Log main process execution with trace context
	g.Log().Debug(ctx, `this is main process`)

	// Execute sub-process with trace context propagation
	if err := gproc.ShellRun(ctx, `go run sub/sub.go`); err != nil {
		panic(err)
	}
}
