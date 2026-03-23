# NanoClaw Configuration

NanoClaw provides the isolated execution environment for STELAX agent workers. 
It receives tasks pushed from Veritas and runs them securely.

## Security Posture
- Assume all execution payloads are untrusted.
- No `docker.sock` access is allowed inside the workers.
- No secrets are mounted directly; inject only via the NanoClaw secret store.
- Memory repositories (`stelax-memory`) should be mounted as **read-only**.
- Only scratch workspaces should be read-write.

## Booting Locally
Rename `.env.example` to `.env` and `mounts.example.json` to `mount_policy.json` to boot tests via `docker-compose`.
