# CloudPulse Deployment Fixes

## Issues Fixed

### 1. Docker Networking Error ✅
**Problem:** `failed to add the host (veth6b7e2f6) <=> sandbox (veth9f2022f) pair interfaces: resource temporarily unavailable`

**Solution:** Added automatic Docker cleanup stages to Jenkinsfile:
- Pre-build cleanup stage
- Post-build cleanup (always runs)
- Aggressive cleanup on failure

### 2. Worker Service Celery Error ✅
**Problem:** `exec: "celery": executable file not found in $PATH`

**Root Cause:** The docker-compose.yml had a Celery command, but the actual worker code uses a simple Python script with Redis queue, not Celery.

**Solution:** Changed worker command from:
```yaml
command: celery -A worker.celery_worker.celery_app worker --loglevel=info
```
To:
```yaml
command: python worker/worker.py
```

### 3. Frontend API Proxy Configuration ✅
**Problem:** Frontend JavaScript calls `/api/tasks` but Nginx had no proxy configuration to route to backend.

**Solution:**
- Created `frontend/nginx.conf` with proxy configuration
- Updated `Dockerfile.frontend` to copy the Nginx config
- Routes `/api/*` requests to `backend:8000`

### 4. Port Mappings ✅
**Updated:**
- Frontend: `3000:80` (Nginx listens on 80 inside container)
- Worker: Added `8001:8001` for Prometheus metrics

## Files Modified

1. **jenkinsfile** - Added Docker cleanup stages
2. **docker-compose.yml** - Fixed worker command, added environment variables
3. **Dockerfile.frontend** - Added Nginx configuration
4. **frontend/nginx.conf** - NEW: API proxy configuration
5. **cloudpulse-terraform/main.tf** - Added security group rules for ports 3000, 8000

## Application Architecture

```
Internet
   │
   ▼
http://15.206.73.240:3000 (Nginx Frontend)
   │
   ├─ / → Serves HTML/JS
   │
   └─ /api/* → Proxies to Backend
                     │
                     ▼
              http://backend:8000 (FastAPI)
                     │
                     ├─ POST /tasks → Enqueues to Redis
                     └─ GET /tasks → Queries Database
                              │
                              ▼
                         Redis Queue
                              │
                              ▼
                    Worker (Python Script)
                    - Polls Redis queue
                    - Processes tasks
                    - Updates database
                    - Exposes metrics on :8001
```

## Services Overview

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **Frontend** | cloudpulse-frontend:latest | 3000→80 | Nginx serving UI + API proxy |
| **Backend** | cloudpulse-python:latest | 8000 | FastAPI REST API |
| **Worker** | cloudpulse-python:latest | 8001 | Background job processor |
| **Redis** | redis:alpine | 6379 | Message queue |

## Next Steps

1. **Commit and push changes:**
   ```bash
   git add .
   git commit -m "Fix worker command, add Nginx proxy, improve Jenkins cleanup"
   git push origin main
   ```

2. **Jenkins will automatically:**
   - Pull latest code
   - Build new Docker images
   - Push to DockerHub
   - Deploy with docker-compose

3. **Access your application:**
   - Frontend: http://15.206.73.240:3000
   - Backend API: http://15.206.73.240:8000/docs
   - Worker Metrics: http://15.206.73.240:8001

## Testing the Application

1. Open http://15.206.73.240:3000
2. Enter a task payload (e.g., "Process user data")
3. Click "Submit Task"
4. Watch the task appear as "PENDING"
5. After ~2 seconds, it should change to "DONE" (worker processed it)

## Troubleshooting

**If frontend shows "Error loading tasks":**
```bash
ssh -i cloudpulse-key ubuntu@15.206.73.240
docker logs cloudpulse_backend_1
```

**If worker isn't processing:**
```bash
docker logs cloudpulse_worker_1
```

**View all running containers:**
```bash
docker ps
```

**Restart all services:**
```bash
cd /var/lib/jenkins/workspace/CloudPulse
docker-compose down
docker-compose up -d
```
