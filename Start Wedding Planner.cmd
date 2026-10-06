@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Please follow README.md to install the application first.
  pause
  exit /b 1
)
echo Wedding Planner: http://127.0.0.1:8510
echo Keep this window open while using the app. Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8510 --server.address 127.0.0.1 --server.headless false --browser.gatherUsageStats false
