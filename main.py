from shared.schema import JobPayload
from server.redis_queue import create_job, dequeue_job

# Example job
job = JobPayload(
    org_id="qualgent",
    app_version_id="xyz123",
    test_path="tests/onboarding.spec.js",
    target="emulator",
    priority=1
)

# Enqueue it
job_id = create_job(job)
print(f"Job ID created: {job_id}")

# Dequeue it (simulate worker)
job_out = dequeue_job("xyz123", "emulator")
print("Dequeued job:", job_out)