# Shell Aliases

Source: https://pi.dev/docs/latest/shell-aliases

Pi runs bash in non-interactive mode (`bash -c`), which does not expand aliases by default.

To enable your shell aliases, set `shellCommandPrefix` in `~/.pi/agent/settings.json`:

```json
{
  "shellCommandPrefix": "shopt -s expand_aliases\neval \"$(grep '^alias ' ~/.zshrc)\""
}
```

The value is a JSON string: `\n` is an escaped newline inside the prefix and the inner double quotes are backslash-escaped. Adjust the path (`~/.zshrc`, `~/.bashrc`, …) to match your shell config. The prefix is prepended to every bash command Pi runs.
