// examples/httpserver/basic-auth/main.go
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
)

// main is the entry point of the application.
// It sets up an HTTP server with Basic Authentication protection.
func main() {
	// Create a new server instance
	s := g.Server()

	// Bind handler for the root path with Basic Authentication
	s.BindHandler("/", func(r *ghttp.Request) {
		// Check authentication credentials using BasicAuth method
		// If authentication succeeds, it returns true
		// If authentication fails, it automatically sends a 401 status code with WWW-Authenticate header
		// The third parameter is the realm message shown in the browser's authentication dialog
		if r.BasicAuth("user", "pass", "Please enter username and password") {
			// Process after successful authentication
			r.Response.Write("Authentication successful!")
		}
		// If authentication fails, the BasicAuth method handles the response automatically
		// No additional code is needed for the failure case
	})

	// Set the server port
	s.SetPort(8000)

	// Start the server
	s.Run()
}
