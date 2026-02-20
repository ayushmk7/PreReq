# OCI Bootstrap Runbook

## 1) Compartments

Create and tag:
- `prereq-dev`
- `prereq-stage`
- `prereq-prod`

Tags:
- `project=prereq`
- `env=dev|stage|prod`
- `owner=<your-name-or-team>`

## 2) IAM Setup

Groups:
- `prereq-admins`
- `prereq-deployers`
- `prereq-ops-readonly`

Dynamic groups:
- API runtime principals
- Worker runtime principals

Policies (least privilege):
- Deployers can manage OCIR artifacts, container instances, load balancer, and bucket objects
- Runtime principals can read required Vault secrets and access queue/object storage
- Ops-readonly can inspect logs, metrics, alarms

## 3) Networking

Create VCN with:
- Public LB subnet
- Private app subnet
- Private DB subnet

Apply NSGs:
- Allow ingress `443` to LB
- Allow LB to API port
- Allow API/worker to DB
- Deny direct internet ingress to private subnets

## 4) Vault and Secrets

Create secrets:
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `INSTRUCTOR_USERNAME`
- `INSTRUCTOR_PASSWORD`

Optional:
- `OCI_BUCKET_UPLOADS`
- `OCI_BUCKET_EXPORTS`
- `OCI_OBJECT_STORAGE_NAMESPACE`

## 5) Registry and Buckets

Create OCIR repositories:
- `prereq-api`
- `prereq-worker`

Create Object Storage buckets:
- `frontend-static`
- `uploads`
- `exports`
- `backups`

## 6) Bootstrap Verification

- Compartment and IAM policies visible
- VCN/subnet/NSG rules applied
- Vault secrets accessible by runtime principals
- OCIR repos and buckets created in expected region
