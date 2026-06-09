// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates file upload handling in a HTTP server using GoFrame.
// It showcases how to:
// 1. Handle file uploads with proper validation
// 2. Serve static files for the upload interface
// 3. Process multipart/form-data requests
// 4. Implement type-safe request/response handling
package main

import (
	"context"

	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
)

// UploadReq defines the request structure for file upload.
// It uses GoFrame's metadata to specify the endpoint and request requirements.
type UploadReq struct {
	g.Meta `path:"/upload" method:"POST" tags:"Upload" mime:"multipart/form-data" summary:"Upload File"`
	File   *ghttp.UploadFile `p:"file" type:"file" dc:"File to upload" v:"required"`
	Msg    string            `p:"msg" dc:"Optional message"`
}

// UploadRes defines the response structure for file upload.
type UploadRes struct {
	FileName string `json:"fileName" dc:"Name of the uploaded file"`
	Message  string `json:"message,omitempty" dc:"Optional message if provided"`
}

// Upload is the controller structure for handling file uploads.
type Upload struct{}

// Upload handles the file upload request.
// It validates the uploaded file and returns the file information.
func (u Upload) Upload(ctx context.Context, req *UploadReq) (*UploadRes, error) {
	if req.File == nil {
		return nil, gerror.New("no file uploaded")
	}

	// Here you can add additional file processing logic
	// For example, saving the file to a specific location:
	// filename, err := req.File.Save("./uploads/")

	return &UploadRes{
		FileName: req.File.Filename,
		Message:  req.Msg,
	}, nil
}

// main initializes and starts the HTTP server with file upload capabilities.
func main() {
	s := g.Server()

	// Configure static file serving for the upload interface
	s.SetIndexFolder(true)
	s.SetServerRoot("static")

	// Configure API routes
	s.Group("/", func(group *ghttp.RouterGroup) {
		group.Middleware(ghttp.MiddlewareHandlerResponse)
		group.Bind(Upload{})
	})

	// Configure server settings
	s.SetClientMaxBodySize(600 * 1024 * 1024) // 600MB max file size
	s.SetPort(8000)
	s.SetAccessLogEnabled(true)

	// Start the server
	s.Run()
}
