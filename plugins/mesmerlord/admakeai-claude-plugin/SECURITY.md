# Security

To report a security issue in this plugin or in AdMakeAI's hosted MCP server, email support@admakeai.com with the details and the steps to reproduce. Please don't open a public issue for it.

The plugin has no code and holds no credentials. It connects to `https://admakeai.com/api/mcp`, and you sign in through AdMakeAI in the browser (OAuth 2.1 with PKCE). The token that creates is scoped to the permissions you approve, and you can disconnect it any time under Connected apps in your [AdMakeAI dashboard](https://admakeai.com/dashboard/integrations/api).
