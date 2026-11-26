---
name: internal-sites
description: Open a web app that runs only inside a server — Grafana, Portainer, an admin panel, a dev server on localhost:3000, a router page — from the user's Termalin cabinet, without opening ports or exposing it to the internet. Use when the user wants to see or reach an internal dashboard, admin page or local web service on their server.
---

Termalin can put an internal web service of a server into the owner's cabinet as an "internal site". The owner opens it signed in to Termalin, through the server's Connector; nothing is published to the internet and no port is opened on the server.

## Find the service

If the user doesn't know the port, look read-only on the server:

- `ss -ltnp` (or `netstat -ltnp`) for listening ports and the process behind each;
- `docker ps --format '{{.Names}} {{.Ports}}'` for containers;
- a quick `curl -sI http://localhost:PORT` to see whether it answers and whether it is http or https.

Common ones: Grafana 3000, Portainer 9000 or 9443, Prometheus 9090, Netdata 19999, pgAdmin 5050, Jupyter 8888, Uptime Kuma 3001.

## Add it

Call `web_link_create` with:

- `server`: the server whose Connector reaches the site (from `hosts_list`);
- `target`: host:port as seen from that server, such as `localhost:3000` or `10.0.0.5:8080`, optionally with a path to land on (`localhost:3000/d/abc/`);
- `https_inside: true` if the service itself speaks https;
- `name`: a short name for the owner's list, such as "Grafana".

Only private addresses are accepted. If the same host:port already has a site, that one is returned (`reused: true`) with an `open_url` for the path you gave. To send the user to another page of the same app, call `web_link_create` again with that path; don't create duplicates.

Give the user `open_url`: it signs them in to Termalin and opens the site. The bare `url` (`<slug>.termal.ink`) shows "This link doesn't work" until it is opened from the account, so don't hand that out on its own.

## Manage

- `web_link_list` shows the owner's sites with who added them and how many people they are shared with.
- `web_link_update` renames a site or points it at a new port or start page when the app moved; it keeps the address and sharing.
- `web_link_delete` removes a site; its address stops working at once for everyone it was shared with. Ask first if it is shared.
- There is a per-account limit. When it is reached, suggest removing an unused site.

## What you can't do

You don't open or read the site, and you can't share it with anyone. Sharing with colleagues is done by the owner in the cabinet. If the site asks for a login, the user signs in themselves.

If the site doesn't load, check on the server that the service is up and listening on that address, and whether it expects https or a base path.
