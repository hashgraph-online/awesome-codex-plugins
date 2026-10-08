# Connection and file handoff

Use the Magic Hour creation MCP at `https://mcp.magichour.ai/`. The separate `https://docs.magichour.ai/mcp` searches documentation and cannot create media. Follow the maintained [MCP user guide](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md) for client authentication.

If creation tools are unavailable, use the official [Python SDK](https://github.com/magichourhq/magic-hour-python), [Node SDK](https://github.com/magichourhq/magic-hour-node), or direct HTTPS with `MAGIC_HOUR_API_KEY` stored outside source code. Read the [current OpenAPI document](https://docs.magichour.ai/api-reference/openapi.json) before composing a request.

For local inputs:

1. Call `video_assets_generate_presigned_url` for the real file type and extension.
2. Upload raw bytes to its `upload_url` with an HTTPS `PUT`. Do not attach the Magic Hour bearer token to this storage request.
3. Verify the upload, then pass the returned `file_path` into the creation tool.

For direct API calls, create with `POST /v1/ai-image-generator`, `POST /v1/ai-image-editor`, or `POST /v1/image-to-video`; then poll the matching image or video project GET route using the original ID. Never retry an ambiguous creation POST automatically.
