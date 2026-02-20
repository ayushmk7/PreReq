#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
PreReq OCI Manual Deployment Checklist
=====================================

1) Verify OCI auth
   - oci iam compartment list --all

2) Verify required secrets exist in Vault
   - DATABASE_URL
   - OPENAI_API_KEY
   - INSTRUCTOR_USERNAME
   - INSTRUCTOR_PASSWORD

3) Verify object storage buckets exist
   - frontend-static
   - uploads
   - exports
   - backups

4) Deploy API container instance
   - Confirm /health
   - Confirm /docs

5) Deploy worker container instance
   - Ensure COMPUTE_ASYNC_ENABLED=true
   - Ensure queue settings are present

6) Build and upload frontend
   - Set VITE_API_BASE_URL
   - Upload dist assets to frontend-static bucket
   - Purge CDN cache if needed

7) Smoke test full flow
   - Upload scores
   - Upload mapping
   - Trigger compute
   - Verify dashboard/report

8) Confirm alarms
   - 5xx
   - latency
   - DB connectivity
   - queue lag
EOF
