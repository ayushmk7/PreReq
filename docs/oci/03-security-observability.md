# Security and Observability Runbook

## Security Baseline

- Private subnets for API/worker/DB
- TLS for frontend and API endpoints
- Vault-backed secret injection
- No plaintext secrets in deployed hosts

## App Hardening

- Restrict CORS to configured origins in production
- Replace placeholder auth strategy for production
- Preserve request correlation IDs in logs

## Logging

Enable centralized logs for:
- Load Balancer
- API container
- Worker container
- Queue and infrastructure events

## Monitoring and Alarms

Create alarms for:
- API 5xx rate
- API p95 latency
- DB connectivity failures
- Queue lag growth
- Worker failure rate

## Incident Response Basics

For each alarm define:
- Owner
- Immediate containment step
- Rollback or scale action
- Recovery verification checklist
