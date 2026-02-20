# OCI Deploy Runbook (Manual)

This project uses manual deployment runbooks (no CI/CD pipeline automation).

## 1) Build and Push Images

1. Build API and worker images.
2. Login to OCIR.
3. Push tags:
   - `prereq-api:<tag>`
   - `prereq-worker:<tag>`

Use immutable tags (commit SHA or release tag).

## 2) Database Setup

1. Provision OCI PostgreSQL in private subnet.
2. Create app DB user with least privileges.
3. Store `DATABASE_URL` in Vault.
4. Run migrations from `backend/`:
   - `alembic upgrade head`

## 3) API Deployment

1. Deploy API container instance in private app subnet.
2. Inject env via Vault-backed values.
3. Expose via OCI Load Balancer (HTTPS).
4. Validate:
   - `GET /health`
   - `GET /docs`

## 4) Worker Deployment

1. Create queue and permissions.
2. Deploy worker container instance in private app subnet.
3. Set worker env:
   - `COMPUTE_ASYNC_ENABLED=true`
   - queue backend settings
4. Confirm worker receives jobs and updates run status.

## 5) Frontend Deployment

1. Build frontend with OCI API URL in `VITE_API_BASE_URL`.
2. Upload `frontend/dist` to `frontend-static` bucket.
3. Enable static hosting and OCI CDN.
4. Point DNS to CDN.

## 6) Smoke Test

1. Upload scores CSV
2. Upload mapping CSV
3. Trigger compute
4. Verify run transitions and dashboard output

Success:
- No unexpected 5xx responses
- Compute runs complete
- Dashboard and student report render correctly
