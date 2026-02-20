# DR and Cost Controls

## Recovery Targets

Set targets per environment:
- `dev`: relaxed RPO/RTO
- `prod`: strict RPO/RTO

Recommended initial target:
- RPO <= 24h
- RTO <= 4h

## Backup Strategy

- Daily automated PostgreSQL backups
- Pre-release snapshots before major changes
- Backup bucket for critical artifacts
- Lifecycle policies for older objects

## Restore Drills

Run periodic restore validation:
1. Restore latest DB backup to test instance
2. Verify schema and key API reads
3. Measure restore time against RTO

## Cost Guardrails for $300 Credits

- Use `dev` environment first
- Start with smallest practical shapes
- Add budget alarms at 50/75/90%
- Reduce log retention for high-volume logs
- Apply bucket lifecycle transitions/deletions

## Weekly Review

- Cost by service and compartment
- Idle resources and right-sizing candidates
- Alert noise and threshold tuning
