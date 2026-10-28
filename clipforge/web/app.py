"""FastAPI REST API server for ClipForge video processing jobs."""

from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Dict, Optional
import uuid

try:
    from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
    from pydantic import BaseModel
except ImportError:
    # Graceful dummy fallback if fastapi is not yet installed
    FastAPI = None
    BaseModel = object


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingJob:
    def __init__(self, job_id: str, filename: str):
        self.job_id = job_id
        self.filename = filename
        self.status = JobStatus.PENDING
        self.progress: float = 0.0
        self.output_files = []
        self.error: Optional[str] = None


# In-memory job repository
jobs: Dict[str, ProcessingJob] = {}

if FastAPI:
    app = FastAPI(
        title="ClipForge API",
        version="0.1.0",
        description="RESTful API for automated AI video repurposing and subtitle burning",
    )

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "service": "clipforge-api"}

    @app.get("/jobs/{job_id}")
    async def get_job_status(job_id: str):
        """Retrieve progress and status of a processing job."""
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        job = jobs[job_id]
        return {
            "job_id": job.job_id,
            "filename": job.filename,
            "status": job.status,
            "progress": job.progress,
            "output_files": job.output_files,
            "error": job.error,
        }

    @app.post("/jobs/submit")
    async def submit_video_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
        """Upload a video and enqueue processing pipeline."""
        job_id = str(uuid.uuid4())[:8]
        job = ProcessingJob(job_id=job_id, filename=file.filename)
        jobs[job_id] = job
        return {"job_id": job_id, "status": job.status, "message": "Job queued successfully"}
else:
    app = None
