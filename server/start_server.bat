@echo off
setlocal
cd /d "%~dp0"

rem --- find Python 3 (works even if it isn't on PATH) ---
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && python -c "import sys" >nul 2>nul && set "PY=python"
)
if not defined PY (
  for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*" "%ProgramFiles%\Python3*" "C:\Python3*") do (
    if exist "%%~D\python.exe" set PY="%%~D\python.exe"
  )
)
if not defined PY (
  echo.
  echo Python 3 was not found on this PC.
  echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH",
  echo then run this file again.
  echo.
  pause
  exit /b 1
)
echo Using Python: %PY%

rem --- make sure tinytuya is installed ---
%PY% -c "import tinytuya" >nul 2>nul || %PY% -m pip install -r requirements.txt

if not exist config.json (
  echo.
  echo config.json is missing. Copy config.example.json to config.json and fill it in.
  echo.
  pause
  exit /b 1
)

%PY% alexa_button_server.py
pause
