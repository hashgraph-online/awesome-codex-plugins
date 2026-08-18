# Technical Book Lab Design Examples

Synthetic examples for technical nonfiction labs.

## Weak Lab Opening

```text
This chapter explains reverse proxies, TLS, ports, DNS, certificates, and Docker networking. First, install these packages...
```

**Problems**:
- No visible reader outcome.
- Concepts are ordered by expert taxonomy.
- The reader cannot tell what success will look like.

## Strong Lab Opening

```text
By the end of this lab, your notes app will be reachable at https://notes.example.com, and you will know how a request moves from DNS to your reverse proxy to the container.
```

**Why it works**:
- Names a concrete result.
- Connects action to mental model.
- Gives the reader a reason to care about the theory.

## Checkpoint Pattern

```text
Step: Start the service.

Run:
docker compose up -d

Check:
docker compose ps

Expected:
The app and database containers show "running" or "healthy".

If not:
- Run docker compose logs app.
- Check that the .env file exists.
- Check that port 8080 is not already in use.
```

## Troubleshooting Table

| Symptom | Likely Cause | Next Check |
|---------|--------------|------------|
| Browser shows connection refused | Service is not listening or port mapping is wrong | Check `docker compose ps` and mapped ports. |
| TLS certificate fails | DNS is not pointing at the host or port 80 is blocked | Check DNS record and firewall rules. |
| Login works locally but not remotely | App base URL or trusted proxy setting is wrong | Check app config and reverse proxy headers. |
| Works until reboot | Service is not enabled or data path is ephemeral | Check restart policy and volume mount. |

## Lab Design Table

| Section | Purpose | Reader Action | Verification |
|---------|---------|---------------|--------------|
| Choose service | Make the lab concrete | Pick one low-risk app | Reader can name what it will store or expose |
| Prepare config | Create reproducible state | Copy and edit config | Config validates or lints |
| Launch locally | Prove app works before exposure | Start containers | Local URL returns expected page |
| Add proxy | Route public request | Add reverse proxy rule | Domain reaches app |
| Secure and maintain | Reduce long-term risk | Add backups and updates | Restore or update check succeeds |

## Safety Note Examples

### Weak

```text
Now open the service to the internet.
```

### Strong

```text
This step makes the service reachable from outside your home network. Do not continue until you have changed the default password, enabled updates, and decided whether this service contains private data.
```

## Exit Criteria Example

```text
You are done when:
- The domain loads over HTTPS.
- The service survives a restart.
- Data is stored in a named volume or explicit host path.
- You can explain where to find logs.
- You have a backup or know why this service does not need one.
```
