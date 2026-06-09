// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates distributed tracing across processes using command-line management.
// It showcases how to:
// 1. Create and manage processes using gcmd
// 2. Propagate trace context between processes
// 3. Handle command-line arguments
// 4. Manage process execution and logging
//
// This example uses gcmd for structured command-line based process management.
package main

import (
	"context"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gcmd"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/gogf/gf/v2/os/gproc"
)

// Main command definition for the main process
var (
	Main = &gcmd.Command{
		Name:  "main",                // Command name
		Brief: "main process",        // Brief description
		Func: func(ctx context.Context, parser *gcmd.Parser) (err error) {
			// Log main process execution with trace context
			g.Log().Debug(ctx, `this is main process`)
			// Execute sub-process with trace context propagation
			return gproc.ShellRun(ctx, `go run sub/sub.go`)
		},
	}
)

// main initializes and runs the main command with trace context
func main() {
	Main.Run(gctx.GetInitCtx())
}
