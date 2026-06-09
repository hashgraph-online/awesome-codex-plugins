// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main implements a sub-process with programmatic management and tracing.
// It showcases how to:
// 1. Initialize a sub-process
// 2. Receive and handle trace context from parent
// 3. Execute sub-process logic
// 4. Report process status through logging
//
// This example demonstrates trace context propagation in a programmatically managed child process.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"
)

// main initializes and runs the sub-process with propagated trace context.
// It demonstrates:
// 1. Context initialization from parent
// 2. Process logging with propagated context
// 3. Sub-process execution and reporting
func main() {
	// Initialize context from parent with tracing
	ctx := gctx.GetInitCtx()

	// Log sub-process execution with propagated trace context
	g.Log().Debug(ctx, `this is sub process`)
}
