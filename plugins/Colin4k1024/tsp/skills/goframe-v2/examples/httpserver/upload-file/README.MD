---
title: File Upload Example
slug: /examples/httpserver/upload-file
keywords: [http, server, file, upload, goframe]
description: Demonstrates file upload handling in GoFrame HTTP servers for multipart form data processing. This example showcases single and multiple file upload support, multipart form data parsing and processing, file size validation and limits, file type validation with MIME type checking, secure file storage with unique naming, and integration with GoFrame's request handling. Features include automatic file parsing, configurable upload limits, file metadata extraction, progress tracking support, error handling for invalid uploads, and production-ready patterns. Ideal for building file upload APIs and forms, implementing image and document upload features, handling bulk file uploads, ensuring secure file processing, and creating content management systems.
hide_title: true
---

# HTTP Server File Upload


## Description

This example demonstrates how to implement file upload functionality in a HTTP server using `GoFrame`. It showcases:
- A modern and user-friendly file upload interface
- Server-side file upload handling
- Progress tracking for file uploads
- Proper error handling and validation
- Maximum file size configuration

The example provides both a REST API endpoint and a web interface for file uploads.

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## Structure

- `go.mod`: The Go module file for dependency management.
- `go.sum`: The Go module checksum file.
- `main.go`: The main application entry point that implements the file upload server.
- `static/`: Directory containing static web files
  - `index.html`: A modern web interface for file uploads with progress tracking.

The project is organized as follows:
```
upload-file/
├── go.mod           # Go module definition
├── go.sum           # Go module checksums
├── main.go          # Server implementation
└── static/          # Static web assets
    └── index.html   # Upload interface
```

## Features

- Modern web interface for file uploads
- Progress bar for upload tracking
- Support for large file uploads (up to 600MB)
- File validation and error handling
- Optional message attachment with uploads
- Access log enabled for debugging
- Clean API documentation

## Usage

1. Run the example:
   ```bash
   go run main.go
   ```

2. The server will start at http://127.0.0.1:8000

3. Access the upload interface:
   - Web Interface: http://127.0.0.1:8000/
   - API Endpoint: POST http://127.0.0.1:8000/upload

4. Upload files using either:
   - The web interface by selecting a file and clicking "Upload"
   - Using curl:
     ```bash
     curl -X POST http://127.0.0.1:8000/upload \
          -F "file=@/path/to/your/file" \
          -F "msg=Optional message"
     ```

## Implementation Details

The example implements several key features:
1. A modern HTML/CSS/JS frontend for file uploads
2. Server-side file handling using GoFrame's features
3. Progress tracking for large file uploads
4. Proper error handling and validation

Key components:
- Maximum file size limit of 600MB
- Access logging for debugging
- Clean separation of frontend and backend code
- Type-safe request/response structures

## Notes

- The maximum file size is set to 600MB
- Access logs are enabled for debugging
- The server supports multipart/form-data uploads
- Frontend provides visual feedback during uploads
- All uploads are validated server-side
