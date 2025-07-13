import time
from shared.schema import JobPayload
from server.redis_queue import (
    dequeue_batch,
    update_job_status,
    increment_retry,
    get_max_retries,
    requeue_job,
    check_visibility_timeouts,
)

def run_worker(app_version_id: str, target: str, batch_size: int = 3):
    print(f"[Worker] Starting worker for app_version: {app_version_id}, target: {target}, batch size: {batch_size}")

    while True:
        jobs = dequeue_batch(app_version_id, target, batch_size)

        if jobs:
            print(f"[Batch Picked] {len(jobs)} job(s):")
            for job in jobs:
                print(f" └─ {job.test_path}")
                update_job_status(job.job_id, "running")

            print("[Booting] Emulator initialized once for batch...")
            time.sleep(2)  # Simulate emulator setup

            for job in jobs:
                should_fail = False  # Set True to simulate failure

                if should_fail:
                    print(f"[FAIL] {job.test_path}")
                    retries = increment_retry(job.job_id)
                    max_retries = get_max_retries(job.job_id)

                    if retries < max_retries:
                        print(f"[Retrying] ({retries}/{max_retries}) - Requeueing job")
                        requeue_job(job)
                        update_job_status(job.job_id, "queued")
                    else:
                        print("[Abandoned] Max retries reached")
                        update_job_status(job.job_id, "failed")
                else:
                    print(f"[Done] {job.test_path}")
                    update_job_status(job.job_id, "done")

        else:
            print("[Idle] No jobs in queue, sleeping...")
            time.sleep(3)
            check_visibility_timeouts(threshold_seconds=30)

if __name__ == "__main__":
    run_worker("xyz123", "emulator")
