// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates a Server-Sent Events (SSE) implementation using GoFrame.
// This example shows how to create a streaming API that simulates an AI chat interface
// where responses are sent character by character to create a typing effect.
package main

import (
	"time"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/text/gstr"
)

// AiChatHandler handles AI chat requests and streams responses using SSE protocol.
// This function demonstrates the core principles of implementing SSE:
// 1. Setting proper HTTP headers for SSE
// 2. Streaming data with proper flushing
// 3. Simulating real-time typing with delays
func AiChatHandler(r *ghttp.Request) {
	// Predefined AI responses for demonstration purposes
	// In a real application, this would come from an AI model or other data source
	aiResponses := `
GoFrame is a modular, high-performance, enterprise-class Go development framework.
SSE (Server-Sent Events) is a technology that allows servers to push data to clients.
Unlike WebSocket, SSE is unidirectional, only allowing servers to send data to clients.
Using SSE enables streaming output for AI models, enhancing user experience.
`

	// Set SSE necessary HTTP headers
	// Content-Type must be text/event-stream for SSE
	r.Response.Header().Set("Content-Type", "text/event-stream")
	// Disable caching for SSE
	r.Response.Header().Set("Cache-Control", "no-cache")
	// Keep the connection alive
	r.Response.Header().Set("Connection", "keep-alive")
	// Allow cross-origin requests (CORS)
	r.Response.Header().Set("Access-Control-Allow-Origin", "*")

	// Split the response text into words
	// Using SplitAndTrim to handle extra whitespace
	var words = gstr.SplitAndTrim(aiResponses, " ")

	// Simulate initial thinking time before starting to respond
	// This creates a more realistic AI chat experience
	time.Sleep(500 * time.Millisecond)

	// Send response word by word to create a typing effect
	// In SSE, each message must be followed by a flush operation
	for _, word := range words {
		// Write the word followed by a newline
		// In SSE, each message is terminated by a newline
		r.Response.Writeln(word)
		// Flush the buffer to ensure the client receives the data immediately
		// This is crucial for SSE to work properly
		r.Response.Flush()
		// Simulate typing delay between words
		// Adjust this value to control the typing speed
		time.Sleep(250 * time.Millisecond)
	}
}

// main initializes and starts the HTTP server with the SSE endpoint.
func main() {
	// Create a new HTTP server
	s := g.Server()
	
	// Configure routing
	s.Group("/", func(group *ghttp.RouterGroup) {
		// Register the SSE endpoint at /ai/chat
		group.GET("/ai/chat", AiChatHandler)
	})
	
	// Set the server port
	s.SetPort(8000)
	
	// Start the server
	s.Run()
}
