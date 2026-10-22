---
name: cometchat-self-host
description: "Run CometChat on your own infrastructure — when to self-host, the deployment models (Docker Swarm, Kubernetes, air-gapped), sizing & prerequisites, and how to point your app at the self-hosted instance. CometChat's enterprise differentiator: full data sovereignty. Triggers: 'self-host cometchat', 'on-prem cometchat', 'on premise deployment', 'private cloud chat', 'air-gapped chat', 'run cometchat in our own cloud/VPC', 'data sovereignty', 'point my app at self-hosted cometchat'."
license: "MIT"
compatibility: "CometChat on-premise (Docker Swarm 10k–200k MAU · Kubernetes 200k+ / multi-region · air-gapped). Clients: any CometChat UI Kit / SDK pointed at your domain."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat self-host on-prem on-premise kubernetes docker air-gapped data-sovereignty private-cloud enterprise"
---

> **Ground truth:** deployment detail is FETCHED from the live on-premise docs — `{DOCS_BASE}/on-premise-deployment/docker/overview`, `/docker/prerequisites`, `/docker/production-deployment`, `/docker/security`, `/docker/persistence-and-backup`, `/docker/configuration-reference`, `/docker/air-gapped-deployment`, and `/kubernetes/overview` (`DOCS_BASE = https://www.cometchat.com/docs`; append `.md`). On-prem is a licensed enterprise offering — **[contact CometChat sales](https://www.cometchat.com/contact-sales)** for the images, license, and support. The exact **client host-override** field is in the on-prem client/configuration docs — fetch it there; do not guess a setting name.

## Use this skill when
The customer needs the chat backend inside their own perimeter: data sovereignty, an offline/air-gapped network, a regulated industry, a residency clause the SaaS regions can't meet, or fixed-cost infrastructure instead of per-MAU SaaS pricing. Self-hosting (on-premise deployment) is a CometChat enterprise offering — position it as a differentiator, but don't assert what specific competitors do or don't offer without checking their current docs.

## Why self-host (vs the SaaS regions)
- **Data sovereignty** — all data (messages, media, backups) stays on infrastructure you control, which supports your GDPR/HIPAA/SOC 2 and residency obligations (compliance is the customer's to certify; self-hosting removes the SaaS data-location constraint). (Region selection in SaaS is `cometchat-compliance`; self-host is the stronger step.)
- **Air-gapped / private network** — deploy with no public internet dependency (`/docker/air-gapped-deployment`).
- **Predictable economics** — fixed infra cost, no per-user SaaS pricing.
- **Operational control** — your monitoring, your security perimeter, direct component access.

## Deployment models (pick by scale)
| Model | Target | Use when |
| --- | --- | --- |
| **Docker Swarm** | ~10k–200k MAU, ~20k peak concurrent | most on-prem deployments; lower operational overhead (`/docker/overview`) |
| **Kubernetes** | 200k+ MAU, multi-region active-active, autoscaling | large scale or multi-region (`/kubernetes/overview`) |
| **Air-gapped** | offline / isolated networks | export images, transfer, run from a local registry (`/docker/air-gapped-deployment`) |

The platform is microservices (WebSocket gateway · Chat API · Moderation · Notifications · Webhooks) over a Kafka event bus, with TiDB (distributed SQL) + MongoDB + Redis and optional S3-compatible object storage. You don't wire these by hand — the deployment scripts do — but size the hosts for them (`/docker/prerequisites`).

## Prerequisites & sizing (before you deploy)
Plan from **MAU and peak concurrent connections (PCC)**: host sizing, OS, storage volumes for the stateful services (databases, Kafka, object storage), and TLS certificates for the load balancer. The full checklist is `{DOCS_BASE}/on-premise-deployment/docker/prerequisites`; follow it rather than improvising capacity.

## Deploy (the runbook is the docs, not this file)
Deployment uses CometChat's automated scripts for consistent, zero-downtime rollouts — `{DOCS_BASE}/on-premise-deployment/docker/production-deployment`. Domains/environment values are set per `/docker/configuration-reference` (+ the domain-update guide). Do not hand-assemble the compose/stack; drive the documented scripts.

## Point your app at the self-hosted instance
Clients reach on-prem over **HTTPS + WebSocket** through your load balancer / NGINX (TLS-terminated). In the app, the CometChat init settings must target **your domain** instead of the SaaS region endpoint — the exact host/region-override field is in the on-prem client-integration + `configuration-reference` docs; **fetch it there and set it**, then keep everything else (App ID, login flow) the same. Every family's init lives in `cometchat-<family>-core`; only the host target changes for on-prem. Verify the app connects to your domain (not `*.cometchat.io`) in the network tab.

## Security & operations
- **Auth**: on-prem uses JWT-based authentication with RSA key pairs — only authorized users reach the platform (`{DOCS_BASE}/on-premise-deployment/docker/security`). Combine with the app-level access model in `cometchat-security`.
- **Network**: keep data stores on the private overlay; expose only the load balancer; enforce TLS end-to-end.
- **Backups & DR**: automated backups with point-in-time recovery and retention aligned to your compliance policy (`/docker/persistence-and-backup`) — this is where you own the retention lifecycle `cometchat-compliance` defers to.
- **Monitoring**: the stack ships Prometheus + Grafana + Loki; wire alerts to your on-call.

## Common pitfalls
1. **Treating on-prem as self-serve** — it's a licensed offering; start with sales for images + license + support.
2. **Under-sizing** — plan hosts from MAU/PCC via the prerequisites, not a guess.
3. **Hand-writing the stack** — use the documented deployment scripts; drift breaks upgrades.
4. **App still pointing at `*.cometchat.io`** — set the client host override to your domain, or you're on SaaS, not on-prem.
5. **Guessing the host-override field** — fetch the exact setting from the on-prem client docs.
6. **No TLS / exposed data stores** — terminate TLS at the LB and keep TiDB/Mongo/Redis/Kafka on the private network.

## Verify it works
The stack deploys via the documented scripts and health checks pass · the app connects to YOUR domain over HTTPS/WSS (confirmed in the network tab), logs in, sends and receives · JWT/RSA auth is enforced · data stores are private + TLS everywhere · backups run and a restore is tested · Grafana shows the services healthy.
