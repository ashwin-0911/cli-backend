# QualGent Backend Challenge: CLI-Driven Test Queue System

This project implements a backend system to manage, queue, and execute AppWright test jobs across local environments, emulators, and remote devices. It is designed for robustness, concurrency, and clear status tracking of each job.

## Features

### Job Queueing

Submit test jobs using the `/submit` endpoint with fields like `org_id`, `app_version_id`, `test_path`, `priority`, and `target`. Each job is stored in Redis with a unique `job_id` and metadata, including creation time and retry count.

### Priority Scheduling

Jobs are stored in Redis sorted sets, allowing high-priority jobs (higher `priority` value) to be processed before lower-priority ones.

### Batch Processing

Jobs are dequeued in batches (default size 3) based on their `app_version_id` and `target`. This minimizes emulator boot overhead and improves resource utilization.

### Horizontal Scalability

Multiple worker containers can be spawned using Docker Compose. For example:

```
docker-compose up --build --scale qg-worker=3
```

Each worker polls Redis independently and processes available jobs. This allows concurrent job handling and dynamic scaling.

### Job Status Tracking

Each job's current status (`queued`, `running`, `done`, or `failed`) is stored in a Redis hash and can be queried via:

```
GET /status/<job_id>
```

### Retry Logic with Limits

Failed jobs are retried automatically. Each job has a `retries` counter and a `max_retries` limit (default: 3). Once the limit is exceeded, the job is marked as `failed` and will not be retried further.

### Visibility Timeout

If a job remains in the `running` state beyond a threshold (default: 30 seconds), it is assumed to be stuck and automatically requeued. This prevents deadlocks and ensures resilience in the case of crashed or slow workers.

### FastAPI Backend with Swagger UI

The system exposes a REST API to submit and monitor jobs. Interactive documentation is available at:

```
http://localhost:8000/docs
```

### Unit Tests with FakeRedis

The Redis job queue logic is covered by a suite of unit tests using `pytest` and `fakeredis`, ensuring isolation and reliability. This includes tests for job creation, status updates, retries, and visibility timeout logic.

### CI Integration

GitHub Actions workflow (`.github/workflows/ci.yml`) runs all tests on every push. It:

* Installs Python 3.11
* Installs test dependencies from `requirements-dev.txt`
* Runs the test suite and fails the build on any test error

## Architecture Overview

```
client (CLI / API consumer)
    |
    v
FastAPI backend --> Redis (job store + queues)
    |
    v
worker simulator(s) (via Docker)
```

* Jobs are stored in Redis hashes
* Queues use sorted sets (`queue:<app_version_id>:<target>`)
* Workers poll Redis in batches, simulate test execution, and update job status

## Installation (Local)

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

### Submit a job

```
curl -X POST http://localhost:8000/submit -H "Content-Type: application/json" -d '{
  "org_id": "qualgent",
  "app_version_id": "xyz123",
  "test_path": "tests/onboarding.spec.js",
  "priority": 3,
  "target": "emulator"
}'
```

### Check job status

```
GET http://localhost:8000/status/<job_id>
```

## Docker Deployment

### Build and run the system

```
docker-compose up --build --scale qg-worker=3
```

This starts:

* The FastAPI backend (on port 8000)
* A Redis container with persistent volume `redis-data`
* 3 worker containers to process jobs concurrently

### Tear down

```
docker-compose down
```

### Redis volume

Redis state is stored in a Docker volume (`redis-data`) to preserve job data, retry counts, and visibility timeout information across restarts.

## Testing

Run the full test suite:

```
pytest
```

Covered scenarios:

* Job creation and metadata
* Job dequeue and requeue
* Retry logic up to `max_retries`
* Visibility timeout recovery
* Status endpoint accuracy

## CI/CD

CI is configured using GitHub Actions (`.github/workflows/ci.yml`). It:

* Uses `ubuntu-latest` runner
* Sets up Python 3.11
* Installs all test dependencies
* Runs all tests with `pytest`
* Fails the build if any test fails (exit code != 0)

## Design Decisions

* Redis was chosen for its atomic operations, support for sorted sets (for prioritization), and TTL-based recovery mechanisms.
* Jobs use UUIDs for global traceability.
* Docker-based horizontal scaling makes it easy to spawn multiple workers with a single flag.
* Visibility timeout ensures fault-tolerance for jobs stuck due to system issues.
* Batch execution amortizes expensive emulator boot time.

## License

MIT License. See `LICENSE` file for full terms.
