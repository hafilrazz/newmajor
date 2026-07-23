@echo off
cd /d "%~dp0"
echo Starting NeuroLens Flask UI + API at http://127.0.0.1:5000
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m backend.app
) else (
  python -m backend.app
)
