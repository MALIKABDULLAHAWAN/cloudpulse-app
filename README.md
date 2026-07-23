# ☁️ CloudPulse — DevOps Capstone Project

**A full-stack cloud monitoring web application built with a complete DevOps pipeline.**

> **Author:** Malik Abdullah Awan | **AWS Account:** `142559108147` | **Region:** `ap-south-1` (Mumbai)

---

## 📋 Table of Contents
- [What is CloudPulse?](#what-is-cloudpulse)
- [Architecture Overview](#architecture-overview)
- [Tech Stack & Why We Chose It](#tech-stack--why-we-chose-it)
- [What Has Been Built (Step by Step)](#what-has-been-built-step-by-step)
- [Architecture Decision: EKS → EC2 + Docker Compose](#architecture-decision-eks--ec2--docker-compose)
- [Current Status](#current-status)
- [Next Steps (What Still Needs to Be Done)](#next-steps-what-still-needs-to-be-done)
- [Directory Structure](#directory-structure)
- [Interview Talking Points](#interview-talking-points)

---

## What is CloudPulse?

CloudPulse is a real-time cloud resource monitoring web application. It has three main components running as microservices:

| Service | Language | Role | 
|---|---|---|
| **Frontend** | HTML/JS | Browser UI that displays cloud metrics |
| **Backend** | Python (Flask) | REST API that serves data to the frontend |
| **Worker** | Python | Background process that polls cloud metrics |

The goal of this project is not just the application itself — it is to build a **fully automated DevOps pipeline** around it that mirrors real-world production engineering.

---

## Architecture Overview

```
Developer pushes code to GitHub
        │
        ▼
┌───────────────────┐
│   Jenkins (CI/CD) │  ← Running on EC2 (15.206.73.240)
│   Port: 8080      │
└───────┬───────────┘
        │  1. Pulls code from GitHub
        │  2. Builds Docker Images
        │  3. Runs Docker Compose to deploy
        ▼
┌───────────────────┐
│  Docker Compose   │  ← Orchestrates all containers on EC2
│  - frontend       │
│  - backend        │
│  - worker         │
│  - redis          │
└───────────────────┘
        │
        ▼
  Live App accessible at:
  http://15.206.73.240:3000
```

---

## Tech Stack & Why We Chose It

### 1. 🐳 Docker — The Packaging Tool
- **What it does:** Wraps the app and all its dependencies into a portable container image.
- **Why we need it:** Guarantees the app runs identically on any machine — your laptop, the EC2 server, or any cloud. Eliminates the "it works on my machine" problem forever.
- **Files:** `Dockerfile.frontend`, `Dockerfile.python`

### 2. 🔧 Jenkins — The Automation Engine (CI/CD)
- **What it does:** Watches GitHub for new code commits. When a developer pushes code, Jenkins automatically builds, tests, and deploys the new version without any human involvement.
- **Why we need it:** This is Continuous Integration / Continuous Deployment (CI/CD). Without it, deploying the app is a manual, error-prone, 30-minute process every single time. Jenkins reduces that to 0 minutes of human effort.
- **Files:** `jenkinsfile`

### 3. 🏗️ Terraform — The Infrastructure Builder
- **What it does:** Defines your entire cloud infrastructure as code. Instead of clicking around the AWS console, you write HCL files and Terraform provisions everything automatically.
- **Why we need it:** Infrastructure as Code (IaC) means your entire server setup is version-controlled, repeatable, and documented. If the server dies, you run one command (`terraform apply`) and it's recreated in minutes.
- **Files:** `cloudpulse-terraform/main.tf`

### 4. 📜 Shell Scripting — The Configuration Tool
- **What it does:** After Terraform creates the raw, empty EC2 server, this installs Jenkins, Docker, and Docker Compose on it automatically via EC2 User Data.
- **Why we need it:** Configuration Management means the software setup of the server is also code, not manual work. If you replace the server, it self-configures using `jenkins-init.sh`.
- **Files:** `cloudpulse-terraform/jenkins-init.sh`

### 5. 🐙 Docker Compose — The Orchestrator
- **What it does:** Runs multiple Docker containers together and manages the network between them.
- **Why we chose this over Kubernetes:** See the Architecture Decision section below.
- **Files:** `docker-compose.yml`

---

## What Has Been Built (Step by Step)

### ✅ Step 1: Application Code
- CloudPulse app exists with Frontend, Backend, and Worker microservices.

### ✅ Step 2: Docker
- `Dockerfile.frontend` — builds the Frontend container.
- `Dockerfile.python` — builds the Backend and Worker containers.

### ✅ Step 3: Jenkins Pipeline Definition
- `jenkinsfile` — defines the CI/CD stages: Build → Push to DockerHub → Deploy via Docker Compose.

### ✅ Step 4: AWS IAM Permissions
- Created IAM Group `mydevice` to bypass the 10-policy-per-user AWS limit.
- Attached all required policies to the group: EKS, EC2, VPC, KMS, SSM, CloudWatch, S3, DynamoDB.
- Added inline policy `EKSFullAccess` directly on the group to grant `eks:*` permissions.
- **Why groups?** IAM Users are limited to 10 attached policies max. Groups have no limit, so we moved policies there.

### ✅ Step 5: Terraform Infrastructure & SSH Injection
- Default VPC mapped with 3 subnets across availability zones.
- Security Group `jenkins-sg-new` — allows port 22 (SSH), 8080 (Jenkins), 80 (HTTP).
- EC2 Instance `t3.micro` provisioned with Ubuntu — **Jenkins server at `15.206.73.240`**.
- Generated an RSA SSH Key locally and injected it into Terraform (`aws_key_pair`) so we could securely log into the server to debug silent installation failures.

### ✅ Step 6: EKS Attempt & Pivot (Blocked by AWS Sandbox Limits)
- EKS Control Plane was successfully created (`cloudpulse-cluster`, Kubernetes v1.31).
- Node group creation failed due to `VcpuLimitExceeded` — AWS Sandbox accounts have a hard cap of 8 vCPUs for On-Demand instances. See Architecture Decision below.

### ✅ Step 7: EC2 User Data Script
- `cloudpulse-terraform/jenkins-init.sh` — Bash script that installs Java 21, Jenkins, Docker, and Docker Compose automatically.
- **Overcame silent failures:** The Jenkins GPG key signature failed and Jenkins deprecated Java 17. By SSHing into the server, we found the errors in `/var/log/cloud-init-output.log`, updated the keyserver, removed Java 17, and successfully installed Java 21.

### ✅ Step 8: Docker Compose Integration
- Created `docker-compose.yml` for local orchestration.
- Updated `jenkinsfile` to deploy using Docker Compose.

---

## Architecture Decision: EKS → EC2 + Docker Compose

### Original Plan: AWS EKS (Kubernetes)
The original architecture called for an **Amazon EKS** Kubernetes cluster with:
- 2x `t3.micro` worker nodes
- Helm Charts for deployment manifests
- Jenkins deploying to the cluster via `kubectl`

### Why We Pivoted
After successfully creating the EKS Control Plane, node group creation failed with:
> `VcpuLimitExceeded: You have requested more vCPU capacity than your current vCPU limit of 8 allows`

AWS Sandbox/Free Tier accounts have a hard **8 vCPU On-Demand limit** that cannot be bypassed without a formal AWS Support quota increase request.

### The Solution: Docker Compose on EC2
Instead of Kubernetes, we use **Docker Compose** on the single EC2 instance. This is:
- ✅ A legitimate, industry-used architecture for small-to-medium workloads.
- ✅ Completely Free Tier eligible (1x `t3.micro` only).
- ✅ Still demonstrates CI/CD, containerization, and Infrastructure as Code.

**Interview Explanation:**
> *"AWS account limits blocked a multi-node Kubernetes deployment. Rather than letting infrastructure constraints block the release cycle, I pivoted to a Docker Compose architecture on EC2. This reduced infrastructure cost to zero while maintaining full CI/CD automation. In production, this would scale to EKS once the account quota is increased."*

---

## Current Status

| Component | Status | Notes |
|---|---|---|
| CloudPulse App Code | ✅ Done | Frontend, Backend, Worker |
| Dockerfiles | ✅ Done | `Dockerfile.frontend`, `Dockerfile.python` |
| Jenkinsfile | ✅ Done | Updated for Docker Compose deploy |
| Terraform — EC2 Server | ✅ Done | Jenkins server at `15.206.73.240` |
| Terraform — EKS Cluster | ⛔ Blocked | vCPU limit in AWS sandbox account |
| `jenkins-init.sh` User Data | ✅ Done | Fixed GPG and Java 21 requirements |
| Jenkins Installed on EC2 | ✅ Done | Running perfectly on `15.206.73.240:8080` |
| `docker-compose.yml` | ✅ Done | Orchestrates frontend, backend, worker, redis |
| App Live on Internet | ⏳ Pending | Needs Jenkins pipeline execution |

---

## Next Steps (What Still Needs to Be Done)

### Step 1: Configure Jenkins Jobs
Open `http://15.206.73.240:8080`, finish the initial setup, install suggested plugins, and create an admin user.
Then, create a new "Pipeline" job pointing to this GitHub repository.

### Step 2: Set Jenkins Credentials
Add DockerHub credentials into Jenkins:
- ID: `dockerhub-credentials`
- Type: Username with password (your Docker Hub username and password).

### Step 3: Run the Pipeline
Click "Build Now" in Jenkins. Jenkins will:
1. Pull your code.
2. Build the Docker images.
3. Push them to DockerHub.
4. Run `docker-compose up -d` directly on the server to start the app.

### Step 4: View the Application
Once the pipeline is green, open `http://15.206.73.240:3000` to see your live CloudPulse application!

---

## Directory Structure

```
devops Projects/
│
├── Project 1/                    ← The CloudPulse Application
│   ├── frontend/                 ← Frontend source code
│   ├── backend/                  ← Backend source code
│   ├── worker/                   ← Worker source code
│   ├── Dockerfile.frontend       ← ✅ Docker build for frontend
│   ├── Dockerfile.python         ← ✅ Docker build for backend/worker
│   ├── jenkinsfile               ← ✅ CI/CD pipeline
│   ├── docker-compose.yml        ← ✅ Orchestrates all containers
│   └── README.md                 ← 📖 This file
│
├── cloudpulse-terraform/         ← Infrastructure as Code
│   ├── main.tf                   ← ✅ EC2, VPC, Security Groups, SSH Key
│   └── jenkins-init.sh           ← ✅ Auto-install script for EC2
│
└── cloudpulse-ansible/           ← Configuration Management (Deprecated for User Data)
    ├── inventory.ini             
    └── install-jenkins.yaml      
```

---

## Interview Talking Points

**"What did you build?"**
> A complete DevOps pipeline for a cloud monitoring web application — containerization with Docker, CI/CD with Jenkins, and infrastructure provisioned as code using Terraform on AWS.

**"What was the hardest challenge?"**
> Debugging silent EC2 User Data failures. Jenkins quietly changed their minimum requirement from Java 17 to Java 21 and rotated their GPG signing keys, causing the installation to fail silently on boot. To fix this, I generated an RSA SSH key, injected it into the Terraform code, rebuilt the server, SSH'd in, and trailed `/var/log/cloud-init-output.log`. From there I successfully diagnosed the missing GPG fingerprint and the Java version conflict, applying the fix live and updating the IaC script to prevent future failures.

**"Why Docker Compose instead of Kubernetes?"**
> I successfully provisioned an EKS Kubernetes control plane, but the AWS sandbox account's 8 vCPU On-Demand limit blocked worker node creation. Rather than blocking the pipeline, I pivoted to Docker Compose — a real production architecture used at many companies — while designing the system so that migrating back to EKS requires only a Jenkinsfile change.

**"What is Infrastructure as Code?"**
> Instead of manually clicking through the AWS console, I wrote Terraform files that describe the desired infrastructure. The entire environment is version-controlled, auditable, and can be recreated from scratch in minutes by running one command.
