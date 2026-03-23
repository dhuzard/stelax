# STELAX (Sovereign Task Execution & Linear Agentic eXchange)

This repository is the open-source control-plane template for:
- structured intake via GitHub Issue Forms
- deterministic parse/normalize/triage workflows
- live execution through Veritas
- isolated worker execution through NanoClaw
- export of durable memory artifacts to a separate memory repo
- optional downstream search through a file-based knowledge agent

**Note:** This is a public template repository. It contains reusable glue, schemas, prompts, workflows, config examples, docs, and tests. Real runtime state and company memory should be stored in separate private repositories created from this template.

## Intended Architecture

1. `<org>-stelax`: The private instance of this repository, hosting your active workflows, intake queues, and runtime configurations.
2. `<org>-stelax-memory`: A separate private repository serving as the durable, searchable memory store for completed tasks and decisions.
3. `<org>-knowledge-agent`: (Optional) A downstream agent that provides search capabilities over the exported file artifacts in the memory repository.

## Getting Started

See the documentation in `docs/` for runbooks and integration details:
- `docs/architecture.md`
- `docs/runbooks.md`
- `docs/threat-model.md`
