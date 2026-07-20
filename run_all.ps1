Write-Host "Installing worker dependencies..."
.\venv\Scripts\pip install -r worker\requirements.txt

Write-Host "Starting Backend..."
Start-Process -WorkingDirectory "backend" -FilePath "..\venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "main:app", "--reload", "--port", "8000"

Write-Host "Starting Worker..."
Start-Process -WorkingDirectory "worker" -FilePath "..\venv\Scripts\python.exe" -ArgumentList "worker.py"

Write-Host "Starting Frontend Proxy Server..."
Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "proxy_server.py"

Write-Host "App is running in new windows!"
Write-Host "Frontend is accessible at http://localhost:3000"
Write-Host "Press Ctrl+C to exit this script, but background processes will need to be closed manually."
