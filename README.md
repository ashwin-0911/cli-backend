# QualGent Backend Challenge: CLI-Driven Test Queue System

This project implements a backend system to manage, queue, and execute AppWright test jobs across local environments, emulators, and remote devices. It is designed for robustness, concurrency, and clear status tracking of each job.

## Features

- Job Queueing  
  Submit test jobs with org_id, app_version, target device, and priority. Each job is stored with metadata in Redis.

- Priority Scheduling  
  Jobs are processed based on priority using Redis sorted sets.

- Batch Processing  
  Jobs are dequeued in batches per target-app_version pair, optimizing emulator boot time and resource efficiency.

- Horizontal Scalability  
  Multiple worker containers can run in parallel with `docker-compose --scale`, enabling distributed load handling.

- Job Status Tracking  
  Each job has a UUID and status (queued, running, done, failed) tracked via Redis hash.

- Retry Logic with Limits  
  Jobs failing during execution are retried up to a configurable limit (max_retries), after which they are marked as failed.

- Visibility Timeout  
  Jobs stuck in running state beyond a threshold are automatically requeued to prevent deadlocks.

- FastAPI Backend with Swagger UI  
  Submit jobs and query status through a clean REST API (available at /docs).

- Unit Tests with FakeRedis  
  Fully tested Redis logic using pytest and fakeredis for isolated, deterministic test runs.

- CI Integration  
  GitHub Actions workflow runs all tests on push to ensure reliability.

## Architecture Overview

```
client (CLI / API consumer)
    │
    ▼
 FastAPI backend ───> Redis (job store + queues)
    │
    ▼
 Worker simulator(s) (via Docker)
```

Jobs are stored as Redis hashes.  
Priority queues use Redis sorted sets per (app_version, target) key.  
Workers pull jobs in batches, run them, and update Redis.

## Installation

```
git clone https://github.com/<your-username>/cli-backend.git
cd cli-backend
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Usage

### Run API server locally

```
uvicorn server.app:app --reload
```

### Submit a job (example)

```
curl -X POST http://localhost:8000/submit -H "Content-Type: application/json" -d '{
  "org_id": "qualgent",
  "app_version_id": "xyz123",
  "test_path": "tests/onboarding.spec.js",
  "priority": 3,
  "target": "emulator"
}'
```

### Check status

```
GET http://localhost:8000/status/<job_id>
```

## Docker Deployment

### Build and run

```
docker-compose up --build --scale qg-worker=3
```

### Tear down

```
docker-compose down
```

### Redis volume

Redis data persists using a Docker volume (redis-data) to ensure visibility timeout logic works reliably across restarts.

## Testing

Run all unit tests:

```
pytest
```

Tests cover:
- Job creation and status updates
- Dequeueing and requeueing
- Retry logic and visibility timeout handling

## CI/CD

CI workflow is defined in `.github/workflows/ci.yml`. It:
- Sets up Python 3.11
- Installs development dependencies
- Runs unit tests with pytest
- Fails on any test error (exit code ≠ 0)

## Design Decisions

- Redis as the job store was chosen for fast access, sorted set support, and visibility timeout patterns.
- UUIDs for job IDs ensure traceability across distributed workers.
- Dockerized architecture allows easy horizontal scaling, batch simulation, and cross-environment use.
- Batch processing ensures emulator booting is amortized over multiple jobs, improving efficiency.

## License

MIT License. See LICENSE for details.
