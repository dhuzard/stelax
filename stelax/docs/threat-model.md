# Threat Model

This document outlines the security assumptions, boundaries, and mitigations in STELAX.

## 1. Untrusted Agent Workers (NanoClaw)
**Threat:** A rogue task or compromised agent attempts to escalate privileges from within NanoClaw.
**Mitigation:** 
- Strict volume mount whitelists (`mount_policy.json`).
- `docker.sock` is never mounted.
- Memory volumes are attached strictly `ro` (read-only).

## 2. Integrity of Memory
**Threat:** An attacker corrupts the durable memory repository (`stelax-memory`).
**Mitigation:** 
- Only the `exporter` service (A5) running in GitHub actions has write access to the memory repository via a restricted PAT.
- NanoClaw workers operate on scratch disk or read-only memory.

## 3. GitHub Issue Form Injections
**Threat:** An attacker inputs malformed markdown or payloads into issue forms.
**Mitigation:**
- Strict `01-parse` boundaries and JSON normalization schema.
- Automatic `needs-info` triage routing for invalid payloads before they hit Veritas.
