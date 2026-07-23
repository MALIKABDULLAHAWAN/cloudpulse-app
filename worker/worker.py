import os
import json
import time
import redis
import datetime
from prometheus_client import start_http_server, Counter
from worker.database import get_engine, get_session_local
from worker.models import Base, Task

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "task_queue")

JOBS_PROCESSED = Counter('jobs_processed_total', 'Total number of jobs processed')
JOBS_FAILED = Counter('jobs_failed_total', 'Total number of jobs failed')

def main():
    print("Starting Prometheus metrics server on port 8001...")
    start_http_server(8001)
    
    print("Ensuring database is ready...")
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    print("Connecting to Redis...")
    r = redis.from_url(REDIS_URL)
    
    print("Worker is ready. Waiting for jobs...")
    while True:
        try:
            # Blocking pop from Redis queue
            job_data = r.blpop(QUEUE_NAME, timeout=0)
            if job_data:
                _, job_json = job_data
                job = json.loads(job_json)
                task_id = job.get('task_id')
                
                if not task_id:
                    continue
                
                print(f"Processing task {task_id}...")
                # Simulate work
                time.sleep(2)
                
                # Update database
                db = get_session_local()()
                try:
                    task = db.query(Task).filter(Task.id == task_id).first()
                    if task:
                        task.status = "done"
                        task.completed_at = datetime.datetime.utcnow()
                        db.commit()
                        JOBS_PROCESSED.inc()
                        print(f"Task {task_id} completed.")
                finally:
                    db.close()
                    
        except Exception as e:
            print(f"Error processing job: {e}")
            JOBS_FAILED.inc()
            time.sleep(1) # Prevent tight loop on persistent database/redis failure

if __name__ == "__main__":
    main()
