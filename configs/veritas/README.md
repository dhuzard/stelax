# Veritas Configuration

This directory contains the example deployment configuration for Veritas.

Veritas serves as the STELAX operational truth. It uses a pull-based integration with GitHub Issues formatted via the canonical templates. 

## Running Locally

1. Copy `.env.example` to `.env`.
2. Populate the needed API tokens.
3. Review `integrations.example.json` to ensure it targets your test repository.
4. Run `docker-compose up -d`.
