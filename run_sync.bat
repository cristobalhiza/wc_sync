@echo off
setlocal ENABLEDELAYEDEXPANSION

set BASE=%~dp0
cd /d "%BASE%"

set EXE=
for %%F in (*.exe) do set EXE=%%F

if "%EXE%"=="" (
  echo [ERROR] No se encontró un .exe en %BASE%
  pause
  exit /b 1
)

echo [%date% %time%] Running %EXE% >> sync.log
"%EXE%" >> sync.log 2>&1
echo [%date% %time%] Done >> sync.log
