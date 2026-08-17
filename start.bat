@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "PORT=8010"
set "APP_URL=http://127.0.0.1:%PORT%/"
set "PYTHON=.venv\Scripts\python.exe"

echo.
echo [1/4] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
  echo Python 3.11+ was not found. Install Python and add it to PATH.
  pause
  exit /b 1
)

if not exist "%PYTHON%" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto :failed
)

"%PYTHON%" -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
  echo Installing backend dependencies...
  "%PYTHON%" -m pip install -e .
  if errorlevel 1 goto :failed
)

if not exist ".env" if exist ".env.example" (
  echo Creating .env from .env.example...
  copy /y ".env.example" ".env" >nul
)

echo [2/4] Checking frontend tools...
where pnpm >nul 2>&1
if errorlevel 1 (
  echo pnpm was not found. Run: npm install -g pnpm
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo Installing frontend dependencies. This may take a few minutes...
  call pnpm --dir frontend install --frozen-lockfile
  if errorlevel 1 goto :failed
)

echo [3/4] Building frontend...
call pnpm --dir frontend run build
if errorlevel 1 goto :failed

echo [4/4] Starting server...
netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul
if not errorlevel 1 goto :open_browser

start "Grand Canal Agent Server" /D "%CD%" cmd /k ""%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%"

for /L %%I in (1,1,20) do (
  netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul
  if not errorlevel 1 goto :open_browser
  ping 127.0.0.1 -n 2 >nul
)

echo Server did not start within 20 seconds. Check the server window.
pause
exit /b 1

:open_browser
echo Server is ready. Opening %APP_URL%
start "" "%APP_URL%"
exit /b 0

:failed
echo Startup failed. Check the error above and try again.
pause
exit /b 1
