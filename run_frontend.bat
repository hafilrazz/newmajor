@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\streamlit.exe" (
  ".venv\Scripts\streamlit.exe" run frontend\app.py
) else (
  streamlit run frontend\app.py
)
