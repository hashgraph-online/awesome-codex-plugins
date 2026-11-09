# Security — an item that handles input or output it does not fully trust

## When it applies

The item takes input from a user, a file, or the network, or it writes logs and errors.

## Cases

- **Untrusted input** — input from a user, a file or the network that could reach a shell, a query,
  a path or a template.
- **Secrets in logs** — tokens, passwords or personal data that could reach output, logs or errors.

## Example lines

- WHEN a token is in the input THEN the error and the log do not contain the token
