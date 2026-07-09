# Configuration

Rust services should parse configuration once at startup and pass typed config
through application state.

## Layers

Typical precedence:

1. Defaults committed to the repo.
2. Environment-specific file such as `configuration/production.yml`.
3. Environment variables from the deployment platform.
4. Secret manager values mounted as environment or files.

Document the actual precedence in code or deployment docs.

## Typed Config

```rust
#[derive(serde::Deserialize, Clone)]
pub struct Settings {
    pub application: ApplicationSettings,
    pub database: DatabaseSettings,
}

#[derive(serde::Deserialize, Clone)]
pub struct DatabaseSettings {
    pub url: secrecy::SecretString,
    pub max_connections: u32,
}
```

Validate at startup:

- Required secrets are present.
- Ports and URLs parse.
- Pool sizes and timeouts are within expected bounds.
- Production does not use local-only defaults.

## Secret Handling

- Do not commit production secrets.
- Do not print full config structs when they contain secrets.
- Keep secret values in `SecretString` or project wrappers.
- Expose secrets only at the driver boundary that needs raw text.
