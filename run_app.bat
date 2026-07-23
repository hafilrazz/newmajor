@echo off
cd /d "%~dp0"
echo.
echo  NeuroLens — Flask clinical workspace
echo  Open: http://127.0.0.1:5000
echo.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m backend.app
) else (
  python -m backend.app
)
