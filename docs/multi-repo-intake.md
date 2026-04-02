# Multi-Repo Intake

This document explains how to configure multiple `<org>-stelax` instances to
fan their exported artifacts into a single shared `<org>-stelax-memory` repository.

This is the recommended setup for large organisations with multiple teams, each
running their own STELAX fork, who want a unified searchable memory archive.

---

## Architecture

```
team-a-stelax  ─┐
team-b-stelax  ─┼──► org-stelax-memory  ──► search-index.json
team-c-stelax  ─┘
```

Each team fork runs its own intake pipeline (issues → triage → Veritas → NanoClaw).
The export step writes to a shared memory repo using namespaced paths so artifacts
from different teams never collide.

---

## Namespaced export paths

Each team fork must set a `STELAX_NAMESPACE` environment variable (e.g. `team-a`).
The export workflow uses this to write artifacts under a team-specific prefix:

```
org-stelax-memory/
├── team-a/
│   ├── tasks/2026/
│   ├── incidents/2026/
│   └── audit/2026/
├── team-b/
│   ├── tasks/2026/
│   └── decisions/2026/
└── search-index.json   ← rebuilt across all namespaces after each export
```

---

## Setup steps

### 1. Create the shared memory repo

Create a single private `<org>-stelax-memory` repository. This is the only repo
that all team forks write to.

### 2. Create a shared MEMORY_REPO_PAT

Generate one GitHub PAT with `Contents: write` scope scoped to the memory repo.
Add it as a secret (`MEMORY_REPO_PAT`) in every team fork's repository settings.

If you prefer per-team tokens with narrower scope, create one PAT per team and
add each to the corresponding fork only.

### 3. Set STELAX_NAMESPACE in each fork

In each team fork's repository settings, add a repository variable (not secret):

```
STELAX_NAMESPACE = team-a   # or team-b, team-c, etc.
```

### 4. Update the export workflow

In each fork's `.github/workflows/04-export-memory.yml`, pass the namespace to
the exporter:

```yaml
- name: Run Exporter
  run: |
    python exporter/export_memory.py \
      --memory-dir ../../../memory-repo \
      --namespace ${{ vars.STELAX_NAMESPACE }}
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    VERITAS_API_KEY: ${{ secrets.VERITAS_API_KEY }}
```

### 5. Update the search index and audit trail workflows

Workflows `07-build-search-index.yml` and `08-audit-trail.yml` should run from
one designated fork (or a separate automation repo) that has access to the shared
memory repo. They automatically handle the full tree including all namespaces.

---

## Triage policy per team

Each fork can carry its own `triage-policy.json` (see `configs/triage-policy.example.json`).
Teams with stricter or looser requirements can customise their required fields,
priority keywords, and routing rules independently without affecting other forks.

---

## Routing policy per team

Each fork can carry its own `routing.json` (see `configs/nanoclaw/routing.example.json`).
Different teams can route to different NanoClaw worker pools or channels without
sharing infrastructure.

---

## Considerations

| Concern | Recommendation |
|---|---|
| Write conflicts | Namespaced paths ensure teams never overwrite each other's artifacts |
| PAT scope | Use a single PAT with write access to the memory repo only — never org-wide |
| Search index freshness | Run `07-build-search-index.yml` after any fork's export completes |
| Memory repo growth | The memory repo is append-only; plan for periodic archival if volume is high |
| Cross-team visibility | The shared memory repo gives all teams read access to each other's artifacts — scope access carefully |
