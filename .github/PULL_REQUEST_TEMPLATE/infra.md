## Goal
Infrastructure or runtime config change.

## Files Touched
- docker-compose/envs/configs

## Risk Level
- High (requires A7 / Security review)

## Test Evidence
- local boot logs or sandbox validation

## Rollback Note
- config revert steps

## Reviewer Checklist
- [ ] No secrets exposed in env.example
- [ ] No excessive mounts added to NanoClaw
- [ ] Docker configurations remain secure
