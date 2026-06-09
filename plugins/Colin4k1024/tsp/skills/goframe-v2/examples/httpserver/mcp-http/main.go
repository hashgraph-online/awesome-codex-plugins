package main

import (
	"context"
	"fmt"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func main() {
	// 1. Create MCP Server
	mcpSrv := server.NewMCPServer(
		"GoFrame MCP HTTP Demo",
		"1.0.0",
	)

	// 2. Add an addition tool
	tool := mcp.NewTool("add",
		mcp.WithDescription("Add two numbers"),
		mcp.WithNumber("a", mcp.Required(), mcp.Description("First number")),
		mcp.WithNumber("b", mcp.Required(), mcp.Description("Second number")),
	)

	mcpSrv.AddTool(tool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		a, err := request.RequireFloat("a")
		if err != nil {
			return mcp.NewToolResultError("参数a错误: " + err.Error()), nil
		}
		b, err := request.RequireFloat("b")
		if err != nil {
			return mcp.NewToolResultError("参数b错误: " + err.Error()), nil
		}
		result := a + b
		return mcp.NewToolResultText(fmt.Sprintf("结果: %v + %v = %v", a, b, result)), nil
	})

	// 3. StreamableHTTP
	httpSrv := server.NewStreamableHTTPServer(mcpSrv)

	// 4. Start GoFrame Server
	s := g.Server()
	s.SetPort(8080)

	// 5. Bind MCP Handlers using ghttp.WrapH
	s.BindHandler("/mcp", ghttp.WrapH(httpSrv))

	s.Run()
}
