import redis
import json
import uuid
import datetime
from shared.schema import JobPayload

# Connect to Redis (Docker-safe hostname)
r = redis.Redis(host="redis", port=6379, decode_responses=True)


# -------------------------------
# Job Creation & Queueing
# -------------------------------

def create_job(job: JobPayload) -> str:
    job_id = str(uuid.uuid4())
    job.job_id = job_id
    now = datetime.datetime.utcnow().isoformat()

    # Store job metadata
    r.hset(f"job:{job_id}", mapping={
        "status": "queued",
        "org_id": job.org_id,
        "app_version_id": job.app_version_id,
        "test_path": job.test_path,
        "priority": job.priority,
        "target": job.target,
        "retries": 0,
        "max_retries": 3,
        "created_at": now,
        "last_attempt": ""
    })

    # Add job to priority queue (score = -priority for max-heap behavior)
    queue_key = f"queue:{job.app_version_id}:{job.target}"
    r.zadd(queue_key, {job.model_dump_json(exclude_unset=False): -job.priority})

    return job_id


def requeue_job(job: JobPayload):
    key = f"queue:{job.app_version_id}:{job.target}"
    r.zadd(key, {job.model_dump_json(exclude_unset=False): -job.priority})


# -------------------------------
# Job Dequeueing (Single + Batch)
# -------------------------------

def dequeue_job(app_version_id: str, target: str):
    key = f"queue:{app_version_id}:{target}"
    jobs = r.zrange(key, 0, 0)  # Top 1 job
    if jobs:
        job_json = jobs[0]
        r.zrem(key, job_json)
        return JobPayload.model_validate_json(job_json)
    return None


def dequeue_batch(app_version_id: str, target: str, batch_size: int = 3) -> list[JobPayload]:
    key = f"queue:{app_version_id}:{target}"
    jobs = r.zrange(key, 0, batch_size - 1)  # Fetch up to `batch_size` jobs
    if not jobs:
        return []

    # Remove from queue
    r.zrem(key, *jobs)
    return [JobPayload.model_validate_json(j) for j in jobs]


# -------------------------------
# Status & Retry Logic
# -------------------------------

def get_job_status(job_id: str) -> str:
    return r.hget(f"job:{job_id}", "status")


def update_job_status(job_id: str, status: str):
    now = datetime.datetime.utcnow().isoformat()
    r.hset(f"job:{job_id}", mapping={"status": status, "last_attempt": now})


def increment_retry(job_id: str) -> int:
    return r.hincrby(f"job:{job_id}", "retries", 1)


def get_max_retries(job_id: str) -> int:
    value = r.hget(f"job:{job_id}", "max_retries")
    return int(value) if value else 3


# -------------------------------
# Visibility Timeout Recovery
# -------------------------------

def check_visibility_timeouts(threshold_seconds: int = 30):
    now = datetime.datetime.utcnow()
    for key in r.keys("job:*"):
        status = r.hget(key, "status")
        last_attempt = r.hget(key, "last_attempt")

        if status == "running" and last_attempt:
            last_time = datetime.datetime.fromisoformat(last_attempt)
            if (now - last_time).total_seconds() > threshold_seconds:
                print(f"[Timeout] Job {key} stuck in running → resetting to queued")
                r.hset(key, "status", "queued")
                job_json = build_job_json_from_hash(key)
                job = JobPayload.model_validate_json(job_json)
                requeue_job(job)


def build_job_json_from_hash(job_key: str) -> str:
    data = r.hgetall(job_key)
    return json.dumps({
        "org_id": data["org_id"],
        "app_version_id": data["app_version_id"],
        "test_path": data["test_path"],
        "priority": int(data["priority"]),
        "target": data["target"],
        "job_id": job_key.split("job:")[1]
    })
