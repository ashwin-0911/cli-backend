from fastapi import FastAPI, HTTPException
from shared.schema import JobPayload
from server.redis_queue import create_job
from server.redis_queue import get_job_status

app = FastAPI()

@app.post("/submit")
def submit_job(payload: JobPayload):
    job_id = create_job(payload)
    return {"message": "Job submitted", "job_id": job_id}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    status = get_job_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return {"job_id": job_id, "status": status}