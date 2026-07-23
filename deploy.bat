@echo off
echo ========================================
echo CloudPulse - Commit and Push Changes
echo ========================================
echo.

cd "C:\Users\Saaz\Desktop\devops Projects\Project 1"

echo Step 1: Checking git status...
git status
echo.

echo Step 2: Adding all changes...
git add .
echo.

echo Step 3: Committing changes...
git commit -m "Fix worker command, add Nginx proxy config, improve Docker cleanup"
echo.

echo Step 4: Pushing to GitHub...
git push origin main
echo.

echo ========================================
echo Done! Jenkins will now automatically:
echo 1. Pull the latest code
echo 2. Build new Docker images
echo 3. Push to DockerHub
echo 4. Deploy with docker-compose
echo.
echo Monitor the build at:
echo http://15.206.73.240:8080
echo.
echo Once build completes, access your app at:
echo http://15.206.73.240:3000
echo ========================================
pause
