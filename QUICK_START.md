# 🚀 CloudPulse - Quick Start Guide

## ✅ Current Status

All issues have been fixed! Your pipeline is ready to deploy successfully.

## 📋 What To Do Now (3 Simple Steps)

### **Step 1: Apply Terraform Changes**
Open PowerShell and run:
```powershell
cd "C:\Users\Saaz\Desktop\devops Projects\cloudpulse-terraform"
terraform apply -auto-approve
```
This opens ports 3000, 8000, and 8001 on your EC2 server.

### **Step 2: Push Code Changes to GitHub**
Double-click the file:
```
deploy.bat
```
Or manually run:
```bash
cd "C:\Users\Saaz\Desktop\devops Projects\Project 1"
git add .
git commit -m "Fix worker command, add Nginx proxy config, improve Docker cleanup"
git push origin main
```

### **Step 3: Monitor Jenkins Build**
1. Open: http://15.206.73.240:8080
2. Click on your "CloudPulse" pipeline job
3. Watch the build progress
4. Wait for "SUCCESS" ✅

## 🎉 Access Your Application

Once the Jenkins build succeeds:

| Component | URL | Description |
|-----------|-----|-------------|
| **Frontend** | http://15.206.73.240:3000 | Main UI Dashboard |
| **Backend API** | http://15.206.73.240:8000/docs | FastAPI Swagger Docs |
| **Worker Metrics** | http://15.206.73.240:8001 | Prometheus Metrics |
| **Jenkins** | http://15.206.73.240:8080 | CI/CD Dashboard |

## 🧪 Test Your Application

1. Open http://15.206.73.240:3000
2. Type a task in the input box (e.g., "Process customer data")
3. Click **Submit Task**
4. Watch it appear as **PENDING** (yellow)
5. After ~2 seconds, it changes to **DONE** (green) ✅

**This proves:**
- ✅ Frontend is serving correctly
- ✅ Nginx proxy is working
- ✅ Backend API is responding
- ✅ Redis queue is operational
- ✅ Worker is processing tasks
- ✅ Database is storing data

## 📁 Files Changed

### Application Files
- ✅ **docker-compose.yml** - Fixed worker command, added environment vars
- ✅ **Dockerfile.frontend** - Added Nginx config
- ✅ **frontend/nginx.conf** - NEW: API proxy configuration
- ✅ **jenkinsfile** - Added Docker cleanup stages

### Infrastructure Files
- ✅ **cloudpulse-terraform/main.tf** - Opened ports 3000, 8000, 8001

## 🐛 Issues Fixed

| # | Issue | Solution |
|---|-------|----------|
| 1 | Docker networking error | Added pre/post cleanup in Jenkinsfile |
| 2 | Worker Celery error | Changed to `python worker/worker.py` |
| 3 | Frontend API calls failing | Added Nginx proxy config |
| 4 | Port access blocked | Updated Terraform security group |

## 🎓 Interview Talking Points

**"What bugs did you encounter during deployment?"**

> *"During deployment, I encountered three critical issues:*
>
> *First, Docker networking failures due to veth exhaustion on the Jenkins server. I resolved this by implementing automated resource cleanup in the CI/CD pipeline.*
>
> *Second, a container startup failure because docker-compose.yml referenced Celery, but the actual worker implementation was a pure Python Redis queue consumer. I debugged this by analyzing the container logs and corrected the command to match the actual code architecture.*
>
> *Third, frontend API calls were failing because Nginx had no proxy configuration. I created a custom Nginx config that routes /api/* requests to the backend service, demonstrating understanding of reverse proxy patterns in containerized environments."*

## 📞 Need Help?

**If the build fails:**
1. Check Jenkins console output for errors
2. SSH into the server: `ssh -i cloudpulse-key ubuntu@15.206.73.240`
3. Check container logs: `docker logs cloudpulse_backend_1`

**If the app doesn't load:**
1. Verify all containers are running: `docker ps`
2. Check security group rules in AWS Console
3. Test backend directly: http://15.206.73.240:8000/docs

## ⚡ Quick Commands Reference

**SSH into Jenkins server:**
```bash
ssh -i "C:\Users\Saaz\Desktop\devops Projects\cloudpulse-terraform\cloudpulse-key" ubuntu@15.206.73.240
```

**View running containers:**
```bash
docker ps
```

**View container logs:**
```bash
docker logs cloudpulse_backend_1
docker logs cloudpulse_worker_1
docker logs cloudpulse_frontend_1
```

**Restart all services:**
```bash
cd /var/lib/jenkins/workspace/CloudPulse
docker-compose down
docker-compose up -d
```

**Check Jenkins logs:**
```bash
sudo journalctl -u jenkins -f
```

---

## 🎯 Success Checklist

Before you call it complete, verify:

- [ ] Terraform applied successfully
- [ ] Code pushed to GitHub
- [ ] Jenkins build completed with SUCCESS
- [ ] Frontend loads at http://15.206.73.240:3000
- [ ] Can submit a task
- [ ] Task status changes from PENDING to DONE
- [ ] Backend API docs accessible at http://15.206.73.240:8000/docs
- [ ] Worker metrics visible at http://15.206.73.240:8001

**When all boxes are checked: 🎉 YOUR DEVOPS PIPELINE IS LIVE! 🎉**
