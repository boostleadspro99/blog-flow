@echo off
chcp 65001 >nul 2>nul
cd /d %~dp0

echo Starting Cookie Service...
start /B cmd /c "cd cookie_service && python server.py 2>nul"

echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul

echo Killing port 3897...
:loop
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3897') do taskkill /F /PID %%a >nul 2>&1
timeout /t 1 /nobreak >nul
netstat -ano ^| findstr :3897 >nul
if %errorlevel% equ 0 goto loop

echo Starting OpenAI Server...
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe openai_server.py
) else (
    python openai_server.py
)
