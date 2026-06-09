// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main implements a sub-process with command-line management and tracing.
// It showcases how to:
// 1. Create a sub-process command
// 2. Receive and handle trace context from parent
// 3. Execute sub-process logic
// 4. Report process status through logging
//
// This example demonstrates trace context propagation in a child process.
package main

import (
	"context"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gcmd"
	"github.com/gogf/gf/v2/os/gctx"
)

// Sub command definition for the sub-process
var (
	Sub = &gcmd.Command{
		Name:  "sub",                 // Command name
		Brief: "sub process",         // Brief description
		Func: func(ctx context.Context, parser *gcmd.Parser) (err error) {
			// Log sub-process execution with propagated trace context
			g.Log().Debug(ctx, `this is sub process`)
			return nil
		},
	}
)

// main initializes and runs the sub-command with propagated trace context
func main() {
	Sub.Run(gctx.GetInitCtx())
}
