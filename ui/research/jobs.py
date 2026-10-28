import threading
import uuid

# In-memory store of all jobs: job_id -> info dict.
# Fine for development (runserver). Use a database/Redis for production.
JOBS = {}


def start_job(user_id, topic, depth, perspectives):
    """Queue a research run in a background thread and return its job id."""
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {
        "user": user_id,
        "topic": topic,
        "status": "running",
        "step": 0,
        "message": "Starting...",
        "result": None,
        "error": None,
    }

    def progress(step, text):
        """Update the active job state as the pipeline reports progress."""
        JOBS[job_id]["step"] = step
        JOBS[job_id]["message"] = text

    def work():
        """Run the research pipeline off the request thread."""
        try:
            # Import lazily so the project root is on sys.path in Django runserver.
            from pipeline import run_research_pipeline

            JOBS[job_id]["result"] = run_research_pipeline(
                topic, depth, perspectives, progress
            )
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["error"] = None
        except Exception as exc:  # pragma: no cover - job state is recorded for UI polling.
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(exc)
            JOBS[job_id]["message"] = "The job failed."

    threading.Thread(target=work, daemon=True).start()
    return job_id
