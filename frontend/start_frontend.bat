@echo off
echo Starting Energy Dashboard Frontend...
cd /d "%~dp0"
set "NODE_DIR=C:\Program Files\nodejs"
set "NPM_CMD=%NODE_DIR%\npm.cmd"

if exist "%NPM_CMD%" (
	set "PATH=%NODE_DIR%;%PATH%"
	"%NPM_CMD%" run dev
) else (
	npm run dev
)
pause
