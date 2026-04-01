# NanoClaw Configuration

NanoClaw provides the isolated execution environment for STELAX agent workers.
It receives tasks pushed from Veritas and runs them securely in sandboxed containers.

## Security Posture

- Assume all execution payloads are untrusted.
- No `docker.sock` access is allowed inside workers — this prevents container escape.
- No secrets are mounted directly; inject only via the NanoClaw secret store.
- Memory repositories (`stelax-memory`) must be mounted **read-only**.
- Only per-worker scratch workspaces should be read-write.

## Booting Locally

```bash
cp .env.example .env
cp mounts.example.json mount_policy.json
cp routing.example.json routing.json
docker compose up -d
```

## Channels

Each channel is a worker pool with a defined scope, team access list, and capability set.
Channel configs live in `channels/` and are mounted read-only into workers.

| Channel | Purpose | Teams |
|---|---|---|
| `engineering` | Standard tasks and lower-severity incidents | `@your-org/engineering` |
| `founders` | High-stakes work: p0 tasks, proposals, decisions | `@your-org/founders` |
| `incidents` | Dedicated p0/p1 incident response — always-on | `@your-org/engineering` + `@your-org/founders` |
| `operations` | Async work: retros and meeting summaries | `@your-org/engineering` |

Add a new channel by creating a `channels/<name>.json` file and adding routing rules for it.

## Routing

`routing.json` (copied from `routing.example.json`) controls which channel each issue is
sent to. Rules are evaluated top-to-bottom — the first match wins.

A rule can match on:
- `intake_type` — the type of issue (`task`, `incident`, `proposal`, etc.)
- `priority` — a list of priority levels (`p0`, `p1`, `p2`, `p3`)

A rule with no conditions acts as a catch-all fallback.

**Default routing behaviour:**

| Intake type | Priority | Channel |
|---|---|---|
| incident | p0, p1 | incidents |
| incident | p2, p3 | engineering |
| task | p0 | founders |
| task | p1–p3 | engineering |
| proposal | any | founders |
| decision | any | founders |
| retro | any | operations |
| meeting | any | operations |
| _(anything else)_ | any | engineering |

Customise `routing.json` to reflect your own team structure without touching the exporter code.
