# STELAX

**Sovereign Task Execution & Linear Agentic eXchange**

STELAX is an open-source template that turns your GitHub repository into a structured command center — where work is submitted through forms, automatically sorted and validated, routed to execution, and permanently archived. Think of it as a disciplined operating system for teams that use AI agents to get things done.

> This is a public template. Fork it to create your own private instance.

---

## Why STELAX?

Most teams accumulate tasks, decisions, and meeting notes across scattered tools — Notion pages no one reads, Slack threads that vanish, GitHub issues with no structure. When AI agents enter the mix, the problem compounds: agents need *clean, structured input* to act reliably, and they produce output that disappears the moment the session ends.

STELAX solves both problems:

- **Structured intake** — work enters the system through typed forms (tasks, decisions, meetings), not freeform text. No more ambiguous issues.
- **Automatic triage** — a deterministic pipeline validates, normalizes, and routes every submission. Invalid or incomplete items are flagged before they cause problems downstream.
- **Agent-ready execution** — approved work is pushed to [Veritas](https://github.com/your-org/veritas) (a kanban execution board) and picked up by [NanoClaw](https://github.com/your-org/nanoclaw) workers running in isolated containers.
- **Permanent memory** — completed work is exported as structured markdown + JSON to a separate memory repository, creating an auditable, searchable archive your team (or a knowledge agent) can query later.

---

## How It Works

```
You submit a GitHub Issue (via form)
        ↓
01  Parse      — extracts structured fields from the form body
        ↓
02  Normalize  — converts to a canonical JSON format
    Triage     — routes to kanban, needs-info, or rejected
        ↓
03  Sync       — pushes approved work to Veritas (execution board)
        ↓
    NanoClaw   — picks up tasks, runs them in isolated containers
        ↓
04  Export     — writes completed artifacts to your memory repository
        ↓
    Archive    — permanent, searchable record of everything that happened
```

Each step is a GitHub Actions workflow. The whole pipeline runs automatically whenever an issue is opened or updated.

---

## The Three-Repo Pattern

STELAX is designed around three repositories that work together:

| Repo | Purpose | Visibility |
|---|---|---|
| `<org>-stelax` | Active workflows, intake queue, runtime config | Private |
| `<org>-stelax-memory` | Durable archive of completed work | Private |
| `<org>-knowledge-agent` | (Optional) Search layer over the memory repo | Private |

Fork this template to create `<org>-stelax`. The memory repo is created separately and written to exclusively by the automated exporter — no human (or agent) writes to it directly.

---

## What Gets Submitted

Three structured intake types are supported out of the box:

**Task** — A unit of work with an objective, requirements, and optional context. Gets routed to the execution board.

**Decision** — A record of a decision made, with context and consequences. Goes straight to the archive.

**Meeting** — A meeting summary with attendees, date, and outcomes. Goes straight to the archive.

Each type has a corresponding GitHub Issue Form — contributors fill out a structured template instead of writing freeform text. This is the key constraint that makes the rest of the pipeline reliable.

---

## Repository Layout

```
stelax/
├── .github/
│   ├── ISSUE_TEMPLATE/       # The intake forms (meeting, decision, task)
│   ├── PULL_REQUEST_TEMPLATE/ # PR templates for feature/infra/docs changes
│   └── workflows/            # The 5 automated pipeline stages
├── apps/
│   └── exporter/             # Python service: normalize, triage, sync, export
├── configs/
│   ├── veritas/              # Docker Compose + config for the execution board
│   └── nanoclaw/             # Docker Compose + mount policy for worker containers
├── docs/                     # Architecture, threat model, acceptance tests
├── schemas/                  # JSON schemas for intake forms and canonical data
└── examples/                 # Sample exported memory artifact
```

---

## Getting Started

### 1. Fork this template

Click **Use this template** on GitHub to create your `<org>-stelax` repository.

### 2. Set up secrets

Add these secrets to your repository settings:

| Secret | Description |
|---|---|
| `VERITAS_API_KEY` | API key for your Veritas instance |
| `MEMORY_REPO_PAT` | GitHub PAT with write access to your memory repo only |

### 3. Configure integrations

```bash
# Veritas
cp configs/veritas/.env.example configs/veritas/.env
cp configs/veritas/integrations.example.json configs/veritas/integrations.json

# NanoClaw
cp configs/nanoclaw/.env.example configs/nanoclaw/.env
cp configs/nanoclaw/mounts.example.json configs/nanoclaw/mount_policy.json
```

Edit each file to point at your own infrastructure.

### 4. Boot services

```bash
# Start Veritas
cd configs/veritas && docker compose up -d

# Start NanoClaw workers
cd configs/nanoclaw && docker compose up -d
```

### 5. Submit your first issue

Go to the **Issues** tab in your forked repo and select one of the intake forms. Fill it out and submit — the pipeline runs automatically.

---

## Security Design

A few constraints are deliberately hard-coded and should not be changed:

- **NanoClaw workers never mount `docker.sock`** — prevents a compromised container from escaping to the host.
- **Forbidden mounts** — `~`, `/etc`, `/.ssh`, and `/var/run/docker.sock` are blocked by the mount policy.
- **Memory repo is append-only** — only the exporter workflow has write access, via a restricted PAT scoped to that repo alone.
- **Issue forms enforce structure** — raw markdown is never trusted. Everything is parsed through strict JSON normalization before reaching the execution board.

See [`docs/threat-model.md`](docs/threat-model.md) for the full breakdown.

---

## Documentation

| Document | What it covers |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Component roles and data flow |
| [`docs/threat-model.md`](docs/threat-model.md) | Security threats and mitigations |
| [`docs/acceptance-tests.md`](docs/acceptance-tests.md) | Manual QA checklist for validating your instance |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | PR policy and branch conventions |
| [`CLAUDE.md`](CLAUDE.md) | Guide for AI assistants working in this codebase |

---

## Contributing

One PR per concern. PR titles follow the format `[area] imperative summary`. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full policy.

---

## License

MIT
