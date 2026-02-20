# OCI Day-1 Checklist

## Goal

Get a working `dev` deployment quickly while controlling spend.

## Ordered Actions

1. Create `prereq-dev` compartment and IAM groups/policies.
2. Create VCN/subnets/NSGs and HTTPS entry.
3. Provision OCI PostgreSQL and store `DATABASE_URL` in Vault.
4. Create buckets:
   - `frontend-static`
   - `uploads`
   - `exports`
   - `backups`
5. Build and push API image, deploy API container instance.
6. Build frontend, upload static assets, enable CDN.
7. Run smoke test:
   - scores upload
   - mapping upload
   - compute
   - dashboard/report
8. Enable alarms:
   - 5xx errors
   - latency
   - DB connectivity
   - queue lag

## Cost Controls (Immediate)

- Set budget alarms at 50/75/90%.
- Start with one worker replica.
- Enable lifecycle rules on uploads/exports.
- Keep short log retention for high-volume streams.
