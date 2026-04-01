# CLAUDE.md — STELAX Codebase Guide

This file documents the structure, conventions, and workflows of the STELAX repository for AI assistants working in this codebase.

---

## Project Overview

**STELAX** = Sovereign Task Execution & Linear Agentic eXchange

STELAX is a **public template repository** (not a live instance) that provides a control plane for structured task intake, deterministic triage, external execution, and durable memory export. Organizations fork this repo to create `<org>-stelax` (this repo) and a companion `<org>-stelax-memory` (append-only artifact storage).

**Architecture flow:**
```
GitHub Issue Forms → Parse → Normalize+Triage → Veritas (kanban board) → NanoClaw (worker execution) → Memory Repo
```

---

## Repository Structure

```
stelax/
├── .github/
│   ├── ISSUE_TEMPLATE/          # YAML issue forms: config.yml, meeting.yml, decision.yml, task.yml
│   ├── PULL_REQUEST_TEMPLATE/   # PR templates: feature.md, infra.md, docs.md
│   └── workflows/               # GitHub Actions: 01-parse, 02-normalize, 03-sync, 04-export, 05-e2e-smoke
├── apps/
│   └── exporter/
│       ├── pyproject.toml       # Python package manifest (Python 3.12+)
│       └── exporter/
│           ├── __init__.py
│           ├── normalize_issue.py   # Converts parsed issue data → canonical JSON
│           ├── triage_issue.py      # Deterministic routing: kanban | needs-info | rejected
│           ├── export_memory.py     # Writes markdown + JSON artifacts to memory repo
│           ├── sync_to_veritas.py   # Syncs kanban-labeled issues → Veritas API
│           ├── clients/
│           │   └── veritas_client.py  # REST client for Veritas API (bearer token auth)
│           └── templates/
│               ├── task_outcome.j2      # Jinja2: task artifact markdown
│               ├── meeting_summary.j2   # Jinja2: meeting artifact markdown
│               └── decision_summary.j2  # Jinja2: decision artifact markdown
├── configs/
│   ├── veritas/                 # Docker Compose + .env.example + integrations.example.json
│   └── nanoclaw/                # Docker Compose + .env.example + mounts.example.json + channels/
├── docs/
│   ├── architecture.md          # System flow and component roles
│   ├── threat-model.md          # Security threats and mitigations
│   └── acceptance-tests.md      # Manual QA checklist
├── examples/
│   └── sample-memory/           # Example exported artifact (decision markdown)
├── schemas/
│   ├── canonical/               # normalized-issue.schema.json, memory-artifact.schema.json
│   └── issue/                   # meeting.schema.json, decision.schema.json, task.schema.json
├── CLAUDE.md                    # This file
├── CONTRIBUTING.md              # PR policy
├── README.md                    # High-level overview
└── stelax.md                    # Comprehensive kickoff pack (19KB, read this for deep context)
```

---

## Development Environment

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- GitHub account with admin access (for template instantiation)

### Python Setup
```bash
cd apps/exporter
pip install -e .
```

Dependencies (from `pyproject.toml`): `requests`, `jinja2`, `pydantic`

### Configuration Files
Copy examples before running locally:
```bash
# Veritas
cp configs/veritas/.env.example configs/veritas/.env
cp configs/veritas/integrations.example.json configs/veritas/integrations.json

# NanoClaw
cp configs/nanoclaw/.env.example configs/nanoclaw/.env
cp configs/nanoclaw/mounts.example.json configs/nanoclaw/mount_policy.json
```

Required secrets (populate in `.env` files):
- `VERITAS_API_KEY` — Veritas service authentication
- `GITHUB_TOKEN` — GitHub PAT for issue access
- `VERITAS_DB_URL` — Postgres connection string
- `NANOCLAW_TASK_QUEUE_URL` — Redis connection string

GitHub repository secrets (for CI workflows):
- `VERITAS_API_KEY`
- `MEMORY_REPO_PAT` — Restricted PAT with write access to the memory repo only

---

## Key Workflows (GitHub Actions)

| Workflow | Trigger | Purpose |
|---|---|---|
| `01-parse-issue-form.yml` | Issue opened/edited | Extracts structured fields from issue body → `parsed_issue.json` |
| `02-normalize-and-triage.yml` | After parse workflow | Runs normalize + triage Python scripts |
| `03-sync-to-veritas.yml` | Every 5 min + manual | Pushes `kanban`-labeled issues to Veritas |
| `04-export-memory.yml` | Hourly | Exports completed artifacts to memory repo |
| `05-e2e-smoke.yml` | PR to main + manual | Validates schemas and runs unit tests |

---

## Python Module Conventions

### Running Scripts
All scripts are run as Python modules from the repo root:
```bash
python exporter/normalize_issue.py
python exporter/triage_issue.py
python exporter/export_memory.py --memory-dir <path>
python exporter/sync_to_veritas.py
```

### Data Flow
1. `parsed_issue.json` (output of parse workflow) → input to `normalize_issue.py`
2. `normalized_issue.json` (canonical form) → input to `triage_issue.py`
3. `triaged_issue.json` (with `triage_decision` and `ready_for_kanban` set) → used by sync + export

### Triage Logic (`triage_issue.py`)
- **Task** type: routes to `needs-info` if `Objective` field is missing; otherwise `kanban`
- All other types default to `kanban`
- Sets boolean `ready_for_kanban` flag

### Memory Export Paths
Artifacts are written to the memory repo under:
```
tasks/YYYY/<YYYY-MM-DD-slug>/
meetings/YYYY/<YYYY-MM-DD-slug>/
decisions/YYYY/<YYYY-MM-DD-slug>/
```
Each artifact includes a `.md` file (from Jinja2 template) and a `.json` sidecar.

---

## JSON Schemas

### Intake Schemas (`schemas/issue/`)
Validate data extracted from issue forms:
- `task.schema.json` — required: `objective`, `requirements`; optional: `context`
- `meeting.schema.json` — required: `date` (date format), `attendees`, `summary`; optional: `outcomes`
- `decision.schema.json` — required: `context`, `decision`; optional: `consequences`

### Canonical Schemas (`schemas/canonical/`)
Internal normalized formats:
- `normalized-issue.schema.json` — unified representation after parse/normalize; `triage_decision` enum: `kanban | needs-info | rejected`
- `memory-artifact.schema.json` — exported artifact format; `type` enum: `meeting | decision | task`

When adding new intake types or fields, update both the issue schema and the canonical schema.

---

## Git & PR Conventions

### Branch Naming
```
feat/<slug>     # new features or workflows
fix/<slug>      # bug fixes
chore/<slug>    # maintenance (deps, config)
docs/<slug>     # documentation only
infra/<slug>    # Docker, CI, security-sensitive
test/<slug>     # test additions
```

### PR Rules (from `CONTRIBUTING.md`)
- **One PR = one concern** — do not bundle unrelated changes
- **PR title format:** `[<area>] <imperative summary>` (e.g., `[exporter] Add retry logic to Veritas client`)
- **Always use a PR template** matching the change type (`feature.md`, `infra.md`, or `docs.md`)
- No direct pushes to `main`
- Squash merge only
- `infra/` and security PRs require QA + Security reviewer approval

### PR Template Selection
- Schema changes, workflow changes, exporter logic → `feature.md`
- Docker, `.env`, CI pipeline, security changes → `infra.md`
- Documentation, examples → `docs.md`

---

## Security Constraints

Key security design decisions to preserve:

1. **NanoClaw workers never mount `docker.sock`** — prevents container escape
2. **Forbidden mounts:** `~`, `/var/run/docker.sock`, `/etc`, `/.ssh`
3. **Memory repo write access** is restricted to the exporter via `MEMORY_REPO_PAT` only
4. **Issue form boundaries** are enforced — always normalize via JSON, never trust raw markdown
5. Do not inject Knowledge Agent code into this repo (it is a downstream consumer only)

---

## Testing

### Current State
Tests are minimal stubs. The `05-e2e-smoke.yml` workflow validates YAML syntax of issue forms and runs placeholder Python tests.

### Extending Tests
Add tests under `apps/exporter/tests/` using pytest:
```bash
cd apps/exporter
pip install pytest
pytest tests/
```

Priority test coverage:
- `normalize_issue.py` — validate canonical JSON output shape against `normalized-issue.schema.json`
- `triage_issue.py` — verify routing logic for each intake type and missing-field cases
- `export_memory.py` — check directory structure and file naming conventions
- Jinja2 templates — verify rendered markdown structure

Update `05-e2e-smoke.yml` to replace the `sleep 1` stub with `pytest`.

---

## Sub-Agent Roles (from `stelax.md`)

The kickoff pack defines 7 agent roles for reference:
- **A0** — Orchestrator / PM
- **A1** — Schema & Forms Architect
- **A2** — Workflow Engineer
- **A3** — Python/Exporter Engineer
- **A4** — Infrastructure Engineer
- **A5** — Security Reviewer
- **A6** — Documentation Writer
- **A7** — QA / Test Engineer

When scoping changes, identify which agent role owns the affected area to apply the right PR template and reviewer requirements.

---

## Common Tasks

### Add a new intake type
1. Create `schemas/issue/<type>.schema.json`
2. Add `.github/ISSUE_TEMPLATE/<type>.yml`
3. Update `normalize_issue.py` to handle the new type
4. Update `triage_issue.py` with routing logic
5. Add a Jinja2 template in `apps/exporter/exporter/templates/`
6. Update `export_memory.py` to create the directory and render the template
7. Update `schemas/canonical/memory-artifact.schema.json` to add the new `type` enum value

### Update Veritas integration
- Client code: `apps/exporter/exporter/clients/veritas_client.py`
- Sync logic: `apps/exporter/exporter/sync_to_veritas.py`
- Workflow: `.github/workflows/03-sync-to-veritas.yml`
- Config: `configs/veritas/integrations.example.json`

### Update memory export format
- Jinja2 templates: `apps/exporter/exporter/templates/`
- Export logic: `apps/exporter/exporter/export_memory.py`
- Schema: `schemas/canonical/memory-artifact.schema.json`
- Example: `examples/sample-memory/`

---

## Key Reference Files

- `stelax.md` — Full kickoff pack with detailed specifications, bootstrap backlog, and implementation order
- `docs/architecture.md` — System component roles and data flow
- `docs/threat-model.md` — Security threats and mitigations
- `docs/acceptance-tests.md` — Manual QA checklist for validating a working instance
