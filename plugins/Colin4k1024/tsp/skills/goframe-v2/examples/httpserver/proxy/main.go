// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates a reverse proxy implementation using GoFrame.
// It consists of two servers:
// 1. A backend server that provides the actual service
// 2. A proxy server that forwards requests to the backend
package main

import (
	"net/http"
	"net/http/httputil"
	"net/url"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
)

// Constants for server configuration
const (
	// PortOfServerBackend defines the port number for the backend server
	PortOfServerBackend = 8198
	// PortOfServerProxy defines the port number for the proxy server
	PortOfServerProxy = 8000
	// UpStream defines the backend server URL that the proxy will forward requests to
	UpStream = "http://127.0.0.1:8198"
)

// StartServerBackend initializes and starts the backend server.
// It sets up two routes:
// 1. A catch-all route ("/*") that returns a generic response
// 2. A specific route ("/user/1") that returns user information
func StartServerBackend() {
	s := g.Server("backend")
	s.BindHandler("/*", func(r *ghttp.Request) {
		r.Response.Write("response from server backend")
	})
	s.BindHandler("/user/1", func(r *ghttp.Request) {
		r.Response.Write("user info from server backend")
	})
	s.SetPort(PortOfServerBackend)
	s.Run()
}

// StartServerProxy initializes and starts the proxy server.
// It creates a reverse proxy that forwards all requests with path prefix "/proxy/*"
// to the backend server. The proxy:
// 1. Rewrites the request path by removing the "/proxy" prefix
// 2. Implements error handling for backend failures
// 3. Logs all proxy operations
// 4. Ensures proper handling of request bodies
func StartServerProxy() {
	s := g.Server("proxy")
	// Parse the upstream URL
	u, _ := url.Parse(UpStream)
	// Create a new reverse proxy instance
	proxy := httputil.NewSingleHostReverseProxy(u)
	// Configure error handling for proxy failures
	proxy.ErrorHandler = func(writer http.ResponseWriter, request *http.Request, e error) {
		writer.WriteHeader(http.StatusBadGateway)
	}
	// Handle all requests with path prefix "/proxy/*"
	s.BindHandler("/proxy/*url", func(r *ghttp.Request) {
		var (
			originalPath = r.Request.URL.Path
			proxyToPath  = "/" + r.Get("url").String()
		)
		// Rewrite the request path
		r.Request.URL.Path = proxyToPath
		// Log the proxy operation
		g.Log().Infof(r.Context(), `proxy:"%s" -> backend:"%s"`, originalPath, proxyToPath)
		// Ensure request body can be read multiple times if needed
		r.MakeBodyRepeatableRead(false)
		// Forward the request to the backend server
		proxy.ServeHTTP(r.Response.Writer, r.Request)
	})
	s.SetPort(PortOfServerProxy)
	s.Run()
}

// main starts both the backend and proxy servers.
// The backend server runs in a separate goroutine while
// the proxy server runs in the main goroutine.
func main() {
	go StartServerBackend()
	StartServerProxy()
}
