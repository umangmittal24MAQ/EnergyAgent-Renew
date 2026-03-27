@echo off
echo Starting Energy Dashboard Backend on port 8000...
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
	.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
) else (
	python -m uvicorn api.main:app --reload --port 8000
)
pause
