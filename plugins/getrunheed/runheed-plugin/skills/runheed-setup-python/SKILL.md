---
name: runheed-setup-python
description: Add Runheed error reporting to a Python app (FastAPI, Django, Flask, Celery, scripts) so production errors reach the coding agent over MCP. Use when the user asks to "add error tracking", "set up Runheed", "report production exceptions" or "add monitoring" to a Python project.
---

# Set up Runheed in a Python app

Full reference, kept current: https://runheed.com/SETUP.txt (read it if anything here doesn't match the project).

## 1. The DSN (needs the user)
Ask the user to sign in at https://runheed.com/login, create a project under Projects and paste the DSN (`runheed://pk_...@runheed.com/<project-id>`). Save it as `RUNHEED_DSN` in the environment or the host's secrets. Never commit it. Django, Flask and FastAPI don't read `.env` on their own: export it in the service, or load the file with python-dotenv.

## 2. Install
```bash
pip install https://runheed.com/dl/runheed-0.1.7-py3-none-any.whl
```
Add the same URL to `requirements.txt` or `pyproject.toml` so the deploy installs it too.

## 3. Initialize
```python
import os, runheed
runheed.init(dsn=os.environ["RUNHEED_DSN"])
```
Then add the framework hook, or errors inside request handlers won't be reported:
- FastAPI: https://runheed.com/for/fastapi
- Django: https://runheed.com/for/django (put the middleware LAST in MIDDLEWARE, so it sees the exception before other middleware turns it into a response)
- Flask: https://runheed.com/for/flask
- Celery: task failures are reported on their own once `runheed.init()` runs in the worker process. Other background jobs (FastAPI BackgroundTasks, management commands, cron scripts) need `runheed.capture_exception(e)` in their own `except` blocks.
- Render or Railway (commit and environment tags): https://runheed.com/for/render, https://runheed.com/for/railway

The Python SDK sends each event before `capture_exception` returns, so there's no flush step.

## 4. Verify
Add a temporary view or script that raises, run it once, and confirm the error appears at https://runheed.com/dashboard/errors. Remove the test code.

## 5. Connect the agent
```bash
claude mcp add --transport http runheed https://runheed.com/api/mcp
```
Then `/mcp` > runheed > Authenticate. Cursor: `{"mcpServers": {"runheed": {"url": "https://runheed.com/api/mcp"}}}` in `.cursor/mcp.json`. Other clients: https://runheed.com/connect

Then use the runheed-fix-production-errors skill to work through what it records.
