# Async Compute Migration

## Current Behavior

- `POST /api/v1/exams/{exam_id}/compute` executes pipeline inline in API request.
- Run tracking already exists via `run_id` and `compute_runs`.

## Target Behavior

- API endpoint supports async mode behind `COMPUTE_ASYNC_ENABLED`.
- In async mode:
  - create compute run with `status=queued`
  - enqueue compute payload
  - return immediately with `run_id`
- Worker consumes job, updates status:
  - `queued -> running -> success|failed`

## Migration Steps

1. Add queue service abstraction and feature flag.
2. Add worker entrypoint scaffold.
3. Extract compute execution into reusable service callable by API and worker.
4. Keep sync mode as fallback with feature flag disabled.
5. Validate parity with sample datasets.

## Payload Contract

Queue payload fields:
- `exam_id`
- `run_id`
- `alpha`
- `beta`
- `gamma`
- `threshold`
- `k`

## Acceptance Criteria

- Async submit returns quickly with `status=queued`.
- Worker completes and writes same result tables as sync mode.
- Existing run listing endpoint remains valid.
