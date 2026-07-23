import os
import json
import time
import queue
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from backend.database import get_db, get_engine
from backend.models import Base, Task

# ---------------------------------------------------------------------------
# Redis / fallback in-process queue
# ---------------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "")
QUEUE_NAME = os.getenv("QUEUE_NAME", "task_queue")

_redis_client = None
_local_queue: queue.Queue = queue.Queue()   # fallback when Redis unavailable

def _try_get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not REDIS_URL:
        return None
    try:
        import redis as redis_lib
        r = redis_lib.from_url(REDIS_URL)
        r.ping()
        _redis_client = r
        print("Redis connected.")
        return _redis_client
    except Exception as e:
        print(f"Redis unavailable ({e}), using in-process queue (tasks won't persist across restarts).")
        return None

def enqueue_job(job: dict):
    r = _try_get_redis()
    if r:
        r.lpush(QUEUE_NAME, json.dumps(job))
    else:
        _local_queue.put(job)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter('request_count', 'App Request Count', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['endpoint'])

# ---------------------------------------------------------------------------
# Background worker thread (used only when Redis is unavailable)
# ---------------------------------------------------------------------------
def _local_worker_thread():
    """Process jobs from the in-process queue when Redis is not available."""
    import datetime
    from backend.database import get_session_local
    while True:
        try:
            job = _local_queue.get(timeout=1)
            task_id = job.get("task_id")
            if not task_id:
                continue
            print(f"[local-worker] Processing task {task_id}...")
            time.sleep(2)
            db = get_session_local()()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.status = "done"
                    task.completed_at = datetime.datetime.utcnow()
                    db.commit()
                    print(f"[local-worker] Task {task_id} completed.")
            finally:
                db.close()
        except queue.Empty:
            pass
        except Exception as e:
            print(f"[local-worker] Error: {e}")

# ---------------------------------------------------------------------------
# App lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    # If Redis not available, spin up the in-process worker thread
    if not _try_get_redis():
        t = threading.Thread(target=_local_worker_thread, daemon=True)
        t.start()
        print("In-process worker thread started (no Redis).")
    yield

app = FastAPI(title="CloudPulse Backend", lifespan=lifespan)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    endpoint = request.url.path
    REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, http_status=response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(process_time)
    return response

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    return {"name": "CloudPulse Backend", "status": "running"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        r = _try_get_redis()
        redis_ok = r is not None
        return {"status": "ok", "db": "ok", "redis": "ok" if redis_ok else "unavailable (using local queue)"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service Unavailable")

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

class TaskCreate(BaseModel):
    payload: str

@app.post("/tasks")
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(payload=task_in.payload)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    enqueue_job({"task_id": new_task.id, "payload": new_task.payload})
    return {"id": new_task.id}

@app.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).order_by(Task.id.desc()).limit(50).all()

@app.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
