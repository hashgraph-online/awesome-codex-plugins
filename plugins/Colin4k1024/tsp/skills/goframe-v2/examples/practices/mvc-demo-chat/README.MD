---
title: 'MVC Demo Chat'
slug: '/docs/practices/mvc-demo-chat'
description: 'Real-time chat application built with GoFrame v2.10.0 MVC pattern, featuring WebSocket communication, session management, HTML template rendering, unique nickname validation, and message throttling.'
keywords: [GoFrame, MVC Pattern, WebSocket, Real-time Chat, Session Management, Template Engine, HTML Rendering, WebSocket Chat, Message Broadcasting, Nickname Validation, Rate Limiting, Message Throttling, Concurrent Safe, Cache Management, Frontend Backend Integration, Full Stack Application, Go Web Framework, Interactive Application, User Management, Live Communication]
hide_title: true
---

# MVC Project Demo

## Introduction

`mvc-demo-chat` is a real-time chat application demonstrating GoFrame's MVC (Model-View-Controller) pattern implementation with WebSocket technology. It provides a complete chat room experience with features like unique nickname validation, real-time message broadcasting, user list management, and message sending throttling. This example showcases how to build interactive full-stack web applications using GoFrame's template engine, session management, and WebSocket support.

## Project Structure

```text
mvc-demo-chat/
├── api/                          # API interface definitions
│   └── v1/
│       └── chat.go               # Chat API definitions
├── internal/                     # Internal implementation
│   ├── cmd/
│   │   └── cmd.go                # Server initialization and routing
│   ├── consts/
│   │   ├── consts.go             # General constants
│   │   └── consts_chat.go        # Chat-specific constants
│   ├── controller/
│   │   └── chat.go               # Chat controller with WebSocket logic
│   └── model/
│       └── chat.go               # Chat message model
├── manifest/                     # Application manifest
│   ├── config/
│   │   └── config.yaml           # Server and logging configuration
│   ├── deploy/                   # Deployment configurations
│   └── docker/                   # Docker configurations
├── resource/                     # Static resources and templates
│   ├── public/                   # Static files (CSS, JavaScript, images)
│   │   ├── plugin/               # Frontend plugins
│   │   └── resource/             # Static resources
│   └── template/                 # HTML templates
│       └── chat/
│           ├── include/          # Partial templates
│           └── index.html        # Main page template
├── main.go                       # Application entry point
└── go.mod                        # Go module definition
```

## Features

- **Real-time WebSocket Communication**: Bidirectional communication for instant message delivery
- **MVC Architecture**: Clean separation of concerns with Model-View-Controller pattern
- **Session Management**: User session handling for nickname persistence
- **Template Rendering**: Server-side HTML template rendering with dynamic content
- **Unique Nickname Validation**: Ensures no duplicate nicknames in chat room
- **User List Broadcasting**: Real-time user list updates when users join/leave
- **Message Throttling**: 1-second rate limit prevents message flooding
- **Concurrent-safe Operations**: Thread-safe user and nickname management
- **HTML Sanitization**: XSS protection with HTML entity encoding
- **Error Handling**: User-friendly error messages for validation and rate limiting
- **OpenAPI Documentation**: Automatic API documentation with Swagger UI
- **Static File Serving**: Serves frontend resources from `resource/public`

## Requirements

- Go 1.23.0 or higher

## Installation

```bash
cd /path/to/examples/practices/mvc-demo-chat
go mod tidy
```

## Usage

**Start the server:**

```bash
go run main.go
```

The server will start on `http://localhost:8199`.

**Access the application:**

- Chat Application: http://localhost:8199/chat
- Swagger UI: http://localhost:8199/swagger
- OpenAPI Spec: http://localhost:8199/api.json

## How It Works

### User Flow

1. **Enter Nickname**: Users first enter a unique nickname (3-21 characters)
2. **Join Chat**: After validation, users enter the chat room
3. **Send Messages**: Users can send messages with 1-second throttling
4. **Real-time Updates**: All users see new messages and user list changes instantly
5. **Leave Chat**: Closing the browser tab removes user from the chat room

### Message Types

The application handles three types of messages:

- **`send`**: Regular chat messages sent by users
- **`list`**: User list updates when someone joins or leaves
- **`error`**: Error messages for validation failures or rate limiting

### Session Management

User nicknames are stored in session storage:

- `ChatName`: Confirmed nickname after validation
- `ChatNameTemp`: Temporary nickname during validation
- `ChatNameError`: Error message if nickname is taken

## API Reference

### GET /chat

Displays the chat home page. Shows nickname input form if user hasn't set a nickname, otherwise shows the chat interface.

```bash
curl http://localhost:8199/chat
```

### POST /chat/name

Sets the user's nickname. Validates uniqueness and length (max 21 characters).

**Request:**

```bash
curl -X POST http://localhost:8199/chat/name \
  -H "Content-Type: application/json" \
  -d '{
    "name": "john"
  }'
```

**Validation Rules:**

- Required field
- Maximum 21 characters
- Must be unique (not taken by another user)

**Response on duplicate:**

```json
{
  "code": 51,
  "message": "Nickname \"john\" is already token by others",
  "data": null
}
```

### GET /chat/websocket

Establishes WebSocket connection for real-time chat communication.

**WebSocket URL:**

```
ws://localhost:8199/chat/websocket
```

**Message Format:**

```json
{
  "type": "send",
  "data": "Hello, everyone!",
  "name": "john"
}
```

**Server Response (broadcast to all users):**

```json
{
  "type": "send",
  "data": "Hello, everyone!",
  "name": "john"
}
```

**User List Update:**

```json
{
  "type": "list",
  "data": ["alice", "bob", "john"],
  "name": ""
}
```

**Error Response (rate limit):**

```json
{
  "type": "error",
  "data": "Message sending too frequently, why not a rest first",
  "name": ""
}
```

## Implementation Details

### Controller Architecture

The `hChat` controller manages all chat operations:

```go
type hChat struct {
    Users *gmap.Map    // All users in chat (websocket -> nickname mapping)
    Names *gset.StrSet // All nicknames for uniqueness check
}
```

**Key Features:**

- **Concurrent-safe Collections**: Uses `gmap.Map` and `gset.StrSet` for thread-safe operations
- **WebSocket Management**: Maintains active WebSocket connections
- **Broadcast Mechanism**: Sends messages to all connected clients

### WebSocket Lifecycle

1. **Connection**: User connects via `/chat/websocket`
2. **Registration**: Nickname added to user list, broadcast to all clients
3. **Message Loop**: Continuously reads messages from client
4. **Disconnection**: Removes user from list, notifies all clients
5. **Cleanup**: Session data cleared on connection close

### Rate Limiting

Message throttling uses GoFrame's cache with TTL:

```go
cacheKey := fmt.Sprintf("ChatWebSocket:%p", ws)
gcache.SetIfNotExist(ctx, cacheKey, struct{}{}, consts.ChatIntervalLimit)
```

- **Limit**: 1 second between messages
- **Method**: Cache-based with pointer key
- **Feedback**: Error message sent to user if violated

### HTML Sanitization

User input is sanitized to prevent XSS attacks:

- **Nicknames**: `ghtml.Entities()` converts special characters
- **Messages**: `ghtml.SpecialChars()` escapes HTML entities
- **Protection**: Prevents malicious script injection

### Template Rendering

The application uses GoFrame's template engine:

- **Main Template**: `resource/template/chat/index.html`
- **Includes**: Conditional rendering based on session state
  - `resource/template/chat/include/main.html`: Nickname input form
  - `resource/template/chat/include/chat.html`: Chat interface

## Configuration

Configuration is managed through `manifest/config/config.yaml`:

```yaml
server:
  address: ":8199"
  serverRoot: "resource/public"
  openapiPath: "/api.json"
  swaggerPath: "/swagger"
  dumpRouterMap: true
  routeOverWrite: true
  accessLogEnabled: true

logger:
  level: "all"
  stdout: true
```

**Key Settings:**

- **serverRoot**: Serves static files from `resource/public`
- **accessLogEnabled**: Logs all HTTP requests
- **dumpRouterMap**: Displays route mapping on startup

## Frontend Integration

The application uses static resources served from `resource/public/`:

- **CSS**: Styling for chat interface
- **JavaScript**: WebSocket client logic and DOM manipulation
- **Images**: Icons and avatars
- **Plugins**: Third-party frontend libraries

