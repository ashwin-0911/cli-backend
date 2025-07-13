import fakeredis
import pytest
from shared.schema import JobPayload
from server import redis_queue

# Patch Redis with a fake one for each test
@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis_queue, "r", fake)
    return fake

def test_create_job_and_status(fake_redis):
    job = JobPayload(
        org_id="qualgent",
        app_version_id="xyz123",
        test_path="tests/test.spec.js",
        priority=3,
        target="emulator"
    )

    job_id = redis_queue.create_job(job)

    assert job_id is not None

    status = redis_queue.get_job_status(job_id)
    assert status == "queued"

    # Check metadata
    job_data = fake_redis.hgetall(f"job:{job_id}")
    assert job_data["priority"] == "3"
    assert job_data["status"] == "queued"

def test_dequeue_and_requeue_job(fake_redis):
    job = JobPayload(
        org_id="qualgent",
        app_version_id="xyz123",
        test_path="tests/retry.spec.js",
        priority=2,
        target="emulator"
    )
    job_id = redis_queue.create_job(job)

    # Dequeue
    pulled = redis_queue.dequeue_job("xyz123", "emulator")
    assert pulled.job_id == job_id

    # Requeue
    redis_queue.requeue_job(pulled)
    re_pulled = redis_queue.dequeue_job("xyz123", "emulator")
    assert re_pulled.test_path == "tests/retry.spec.js"


def test_status_and_retries(fake_redis):
    job = JobPayload(
        org_id="qualgent",
        app_version_id="xyz123",
        test_path="tests/fail.spec.js",
        priority=1,
        target="emulator"
    )
    job_id = redis_queue.create_job(job)

    redis_queue.update_job_status(job_id, "running")
    assert redis_queue.get_job_status(job_id) == "running"

    r1 = redis_queue.increment_retry(job_id)
    r2 = redis_queue.increment_retry(job_id)
    max_r = redis_queue.get_max_retries(job_id)

    assert r1 == 1
    assert r2 == 2
    assert max_r == 3

import datetime
import json

def test_visibility_timeout(fake_redis):
    job = JobPayload(
        org_id="qualgent",
        app_version_id="xyz123",
        test_path="tests/timeout.spec.js",
        priority=4,
        target="emulator"
    )
    job_id = redis_queue.create_job(job)

    # Set job to 'running' and fake an old last_attempt timestamp
    key = f"job:{job_id}"
    fake_redis.hset(key, mapping={
        "status": "running",
        "last_attempt": (datetime.datetime.utcnow() - datetime.timedelta(seconds=60)).isoformat()
    })

    # Run timeout check
    redis_queue.check_visibility_timeouts(threshold_seconds=30)

    # Job should now be requeued and set to 'queued'
    assert fake_redis.hget(key, "status") == "queued"

    # Check if it's in the priority queue again
    queue_key = f"queue:{job.app_version_id}:{job.target}"
    jobs = fake_redis.zrange(queue_key, 0, -1)
    assert any(job_id in j for j in jobs)

def test_dequeue_batch(fake_redis):
    jobs = [
        JobPayload(org_id="org", app_version_id="v1", test_path=f"test{i}.js", priority=i, target="emulator")
        for i in [3, 1, 2]
    ]
    for job in jobs:
        redis_queue.create_job(job)

    pulled_batch = redis_queue.dequeue_batch("v1", "emulator", batch_size=2)
    assert len(pulled_batch) == 2
    assert pulled_batch[0].priority == 3  # Highest priority first
    assert pulled_batch[1].priority == 2

def test_empty_dequeue(fake_redis):
    result = redis_queue.dequeue_job("nonexistent", "emulator")
    assert result is None