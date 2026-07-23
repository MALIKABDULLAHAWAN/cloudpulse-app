# Jenkins Docker Networking Issue - Fix Steps

## Immediate Fix (Run on Jenkins Server)

SSH into your Jenkins server and execute these commands:

```bash
# 1. Stop all running containers
docker stop $(docker ps -aq) 2>/dev/null || true

# 2. Remove all stopped containers
docker container prune -f

# 3. Remove unused networks
docker network prune -f

# 4. Remove dangling images
docker image prune -f

# 5. Restart Docker daemon
sudo systemctl restart docker

# 6. Verify Docker is running
docker ps
```

## Alternative: Aggressive Cleanup (if above doesn't work)

```bash
# WARNING: This removes ALL unused Docker resources
docker system prune -af --volumes
sudo systemctl restart docker
```

## What Was Changed in Jenkinsfile

1. **Pre-Build Cleanup Stage**: Cleans up containers and networks BEFORE building to prevent resource exhaustion
2. **Post-Build Cleanup**: Automatically cleans up after every build (success or failure)
3. **Aggressive Cleanup on Failure**: Runs `docker system prune` when pipeline fails

## Verify the Fix

After running the manual cleanup:
1. Commit and push the updated Jenkinsfile to your repository
2. Trigger a new Jenkins build
3. The build should now complete successfully

## Prevention

The updated Jenkinsfile now includes automatic cleanup, so this issue should not occur again. The cleanup runs:
- **Before each build**: Removes old containers and networks
- **After each build**: Cleans up resources created during the build
- **On failure**: Performs more aggressive cleanup

## If Problem Persists

If you continue to see networking errors, you may need to increase system limits:

```bash
# Add to /etc/sysctl.conf
echo "net.core.netdev_max_backlog = 5000" | sudo tee -a /etc/sysctl.conf
echo "fs.file-max = 100000" | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p
```

## Optional: Upgrade to Docker BuildKit

Consider upgrading to BuildKit for better performance and reliability:

```bash
# In your Jenkinsfile, replace docker.build() with:
sh 'DOCKER_BUILDKIT=1 docker build -t ${PYTHON_IMAGE}:${TAG} -f Dockerfile.python .'
```
