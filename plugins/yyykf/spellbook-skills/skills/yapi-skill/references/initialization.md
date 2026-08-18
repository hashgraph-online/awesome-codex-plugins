# Yapi Skill Initialization and Configuration Guide (References)

This document is used to host "long-form instructions" such as **yapi-skill initialization / configuration / token retrieval / multi-environment switching**, avoiding burying the main `SKILL.md` with configuration details.

> Goal: Let the main Skill focus on "interface querying (search + details)", while putting initialization details in a reference document that can be loaded on demand.

## 0) What You Need

- **Python 3**: `python3` command is recommended to be available (Windows can use `py -3` or `python`).
- **YApi base_url**: e.g., `http://yapi.example.com` (just the domain/port is enough).
- **Project token (OpenAPI/Project Token)**: Configured as `projectId -> token`.

## 1) Extract base_url / projectId / interfaceId from the Interface Page URL

If you only have the interface page URL on hand, for example:

`http://yapi.example.com/project/1650/interface/api/414469`

You can extract:

- `base_url`: `http://yapi.example.com`
- `projectId`: `1650`
- `interfaceId`: `414469`

> Tip: The `--base-url` parameter of `init_config.py` also supports directly pasting the interface page URL, and the script will automatically normalize it to the domain/port (but the token is still required).

## 2) How to Get the Project Token (Required)

This skill calls data through the **OpenAPI/Project Token** of YApi and does not use browser login state (Cookie).

The typical access path is (might slightly vary depending on deployment):

- Enter the target project -> "Project Settings / Settings" -> "Token Configuration / OpenAPI" -> Copy token

Once you have the token, you need to add the mapping to the configuration:

- `project_tokens: { "<projectId>": "<token>" }`

For example: `1650=<YOUR_TOKEN>`

## 3) Initialize Configuration (Interactive: Recommended)

Run the initialization script:

```bash
python3 skills/yapi-skill/scripts/init_config.py
```

The script will:

- Write `config.json` (JSON) to the user directory.
- Interactively ask for `base_url`, TLS verification, timeout, and pagination parameters.
- Collect the token via secure input (no echo).

> Security advice: **Try not to pass tokens as command-line arguments** (they can easily enter the shell history). Interactive initialization is safer.

## 4) Initialize Configuration (CI/Scripted: Completely Non-Interactive)

In CI/no TTY scenarios, missing parameters will trigger interactive mode and fail; it is recommended to pass all parameters at once:

```bash
python3 skills/yapi-skill/scripts/init_config.py \
  --base-url http://yapi.example.com \
  --project-token 1650=<YOUR_TOKEN> \
  --verify-tls true \
  --timeout-seconds 60 \
  --page-size 2000 \
  --max-pages 10 \
  --force
```

> Note: Putting tokens on the command line poses a security risk; in CI scenarios, please combine with secret management (Environment Variables/Secrets) and pay attention to log sanitization.

## 5) Configuration File Location and Multi-Environment Switching

### Default Location (Recommended)

The script writes to the user configuration directory by default (following XDG conventions):

- macOS/Linux: `~/.config/yapi-skill-config/config.json` (or `$XDG_CONFIG_HOME/yapi-skill-config/config.json`)
- Windows: `%APPDATA%\yapi-skill-config\config.json` (deduced by script logic)

### Override Configuration Path (Multi-Environment/Multi-Instance)

You can prepare multiple configuration files and switch them in the following ways:

- Environment variable: `YAPI_SKILL_CONFIG=/path/to/config.json`
- Single command execution: `--config /path/to/config.json`
- Initialize and write to a custom location: `init_config.py --out /path/to/config.json`

> Best Practice: Do not commit the configuration file containing tokens to the repository. It can be placed in a private local path of the project (e.g., a directory covered by `.gitignore`) or the user directory.

## 6) Configuration File Structure (Example)

```json
{
  "base_url": "http://yapi.example.com",
  "project_tokens": {
    "1650": "your-token"
  },
  "http": {
    "timeout_seconds": 60,
    "verify_tls": true
  },
  "search": {
    "page_size": 2000,
    "max_pages": 10
  }
}
```

## 7) Verify if Configuration is Successful

### 7.1 Get Interface Details (Recommended Shortest Path)

```bash
python3 skills/yapi-skill/scripts/getInterfaceDetail.py \
  --url 'http://yapi.example.com/project/1650/interface/api/414469' \
  --format markdown
```

### 7.2 Search for Interfaces (Verify Search Capability)

```bash
python3 skills/yapi-skill/scripts/searchInterfaces.py --keyword coupon --format markdown
```

> By default, it will search all projects in the `project_tokens` configuration; use `--projectName` to narrow the scope.

## 8) Common Issues

### 8.1 Configuration File Not Found

- Run `init_config.py` first to initialize; or set `YAPI_SKILL_CONFIG` to point to your configuration file.

### 8.2 `errcode=40011` / "Please login..."

Usually indicates authentication failure (token missing/invalid/unauthorized) or `base_url` pointing to the wrong environment:

- Confirm that `project_tokens` contains the target `projectId`.
- Recopy the token from the project settings.
- Confirm that `base_url` only goes up to the domain/port (do not include `/project/...`).

### 8.3 TLS/Certificate Errors

- For self-signed certificates, you can set `verify_tls=false`.

### 8.4 Search Results are Incomplete or Too Slow

- Adjust `search.page_size` / `search.max_pages`.
- Try to use `--keyword/--path/--projectName` to narrow down the scope.

### 8.5 Occasional Disconnection / Empty reply / RemoteDisconnected

If you encounter errors like:

- `Remote end closed connection without response`
- `curl: (52) Empty reply from server`

This is usually caused by network fluctuations or momentary disconnection from the server. This Skill will retry a few times (default 3 times) for such network errors; if it still fails, it is recommended to try again later or check the Intranet/VPN/Proxy status.
