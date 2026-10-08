# Connection and reference images

Use the Magic Hour creation MCP at `https://mcp.magichour.ai/`. The separate `https://docs.magichour.ai/mcp` searches documentation and cannot create media. Follow the maintained [MCP user guide](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md) for client authentication.

If creation tools are unavailable, use the official [Python SDK](https://github.com/magichourhq/magic-hour-python), [Node SDK](https://github.com/magichourhq/magic-hour-node), or direct HTTPS with `MAGIC_HOUR_API_KEY` stored outside source code. Read the [current OpenAPI document](https://docs.magichour.ai/api-reference/openapi.json) before composing a request.

For a local reference image:

1. Call `video_assets_generate_presigned_url` with its real image extension.
2. Upload the raw bytes to its `upload_url` with an HTTPS `PUT`. Do not attach the Magic Hour bearer token to this storage request.
3. Verify the upload, then pass its returned `file_path` to the editor.

For direct API calls, create with `POST /v1/ai-image-generator` or `POST /v1/ai-image-editor`, then poll `GET /v1/image-projects/{id}` using the original ID. Never retry an ambiguous creation POST automatically.
