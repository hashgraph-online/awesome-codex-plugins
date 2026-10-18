@echo off
rem Purpose: P5 - start one of the plugin's scripts (the MCP server, the command line) with a Node that runs TypeScript
rem directly (Node 24 or newer). Tries the Node runtimes that Codex ships first, then a node on PATH.
rem Codex finds this file for the plugin's MCP server (.mcp.json: ./scripts/launch); scripts/launch is the macOS and
rem Linux version. Input: the script to run and its arguments. Output: whatever the script prints (the MCP stdio stream).
rem v0.4: Claude Code runs it too (.claude-plugin/plugin.json); without Codex, the node on PATH must be Node 24 or newer.
setlocal

if "%~1"=="" (
  echo codex-attachment-manager: missing script path 1>&2
  exit /b 64
)

if defined CODEX_MCP_NODE_PATH if exist "%CODEX_MCP_NODE_PATH%" (
  "%CODEX_MCP_NODE_PATH%" %*
  exit /b
)
if defined CODEX_BROWSER_USE_NODE_PATH if exist "%CODEX_BROWSER_USE_NODE_PATH%" (
  "%CODEX_BROWSER_USE_NODE_PATH%" %*
  exit /b
)
if defined CODEX_ELECTRON_RESOURCES_PATH if exist "%CODEX_ELECTRON_RESOURCES_PATH%\cua_node\bin\node.exe" (
  "%CODEX_ELECTRON_RESOURCES_PATH%\cua_node\bin\node.exe" %*
  exit /b
)
if defined CODEX_CLI_PATH for %%I in ("%CODEX_CLI_PATH%") do if exist "%%~dpIcua_node\bin\node.exe" (
  "%%~dpIcua_node\bin\node.exe" %*
  exit /b
)
if defined LOCALAPPDATA for /d %%D in ("%LOCALAPPDATA%\OpenAI\Codex\runtimes\cua_node\*") do if exist "%%~fD\bin\node.exe" (
  "%%~fD\bin\node.exe" %*
  exit /b
)
if defined USERPROFILE if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" %*
  exit /b
)

rem A node of the user's own must be new enough to run TypeScript directly.
where node >nul 2>&1
if errorlevel 1 goto missing
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 24 ? 0 : 1)" >nul 2>&1
if errorlevel 1 goto missing
node %*
exit /b

:missing
echo codex-attachment-manager: no Node 24 or newer found; install Node 24 or newer from nodejs.org ^(with Codex, updating Codex also works^) 1>&2
exit /b 127
