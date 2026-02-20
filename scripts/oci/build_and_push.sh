#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <ocir-region> <namespace> <repo-prefix> <image-tag>"
  echo "Example: $0 iad mytenancy prereq v0.1.0"
  exit 1
fi

OCI_REGION="$1"
OCI_NAMESPACE="$2"
REPO_PREFIX="$3"
IMAGE_TAG="$4"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_IMAGE="${OCI_REGION}.ocir.io/${OCI_NAMESPACE}/${REPO_PREFIX}-api:${IMAGE_TAG}"
WORKER_IMAGE="${OCI_REGION}.ocir.io/${OCI_NAMESPACE}/${REPO_PREFIX}-worker:${IMAGE_TAG}"

echo "Building API image: ${API_IMAGE}"
docker build -t "${API_IMAGE}" "${ROOT_DIR}/backend"

echo "Building worker image: ${WORKER_IMAGE}"
docker build -t "${WORKER_IMAGE}" "${ROOT_DIR}/backend"

echo "Pushing API image"
docker push "${API_IMAGE}"

echo "Pushing worker image"
docker push "${WORKER_IMAGE}"

echo "Done. Images pushed to OCIR."
