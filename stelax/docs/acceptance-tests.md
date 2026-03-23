# Acceptance Tests

The STELAX bootstrap is validated via the following manual and automated paths.

## 1. Issue Intake Pipeline
- [ ] A user can submit a Meeting Issue Form.
- [ ] The Issue Form is parsed correctly without schema errors.
- [ ] The Triage pipeline successfully routes it based on completion metrics.

## 2. Veritas
- [ ] `docker-compose up` completes on local without crash loops.
- [ ] Adding the `kanban` tag successfully drops the item into Veritas cache.

## 3. Memory Extraction
- [ ] A closed `kanban` item successfully yields a valid markdown and metadata JSON in `stelax-memory`.
- [ ] Running extraction idempotently on the same payload does not duplicate values.
