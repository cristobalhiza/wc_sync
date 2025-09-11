@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "LOG=sync.log"
set "LOGDIR=logs"
set "MAX_SIZE=5242880"   rem 5 MB
set "KEEP_ROTATED=10"

set "BASE=%~dp0"
cd /d "%BASE%"

set "EXE="
for %%F in (*.exe) do if not defined EXE set "EXE=%%F"

if not defined EXE (
  echo [ERROR] No se encontró un .exe en %BASE%
  call :alert_on_error 1 "No se encontró un ejecutable (.exe) en la carpeta del script."
  exit /b 1
)

for /f %%I in ('powershell -NoP -C "(Get-Date).ToString(\"yyyyMMdd_HHmmss\")"') do set "RUNTS=%%I"
set "RUNLOG=%TEMP%\sync_run_%RUNTS%_%RANDOM%.log"

echo. >> "%RUNLOG%"
echo ================================================================ >> "%RUNLOG%"
echo [%date% %time%] Iniciando ejecucion de %EXE% >> "%RUNLOG%"
echo ================================================================ >> "%RUNLOG%"

"%EXE%" >> "%RUNLOG%" 2>&1
set "RC=%ERRORLEVEL%"

echo. >> "%RUNLOG%"
echo [%date% %time%] Ejecucion finalizada con codigo de salida: !RC! >> "%RUNLOG%"
echo. >> "%RUNLOG%"

if not "!RC!"=="0" (
  type "%RUNLOG%" >> "%LOG%"
  call :alert_on_error !RC! "Avisar a Cristobal H. El proceso %EXE% falló con código !RC!. Revisa %LOG%."
  goto :after_run
)

set "HAS_TXT_ERROR=0"
findstr /i ^
 /c:"error" /c:"failed" /c:"exception" /c:"fatal" /c:"critical" ^
 /c:"no se pudo" /c:"no fue posible" /c:"can't connect" /c:"could not connect" ^
 /c:"connection refused" /c:"communications link failure" /c:"access denied for user" ^
 /c:"unknown database" /c:"timeout" /c:"sqlstate" /c:"operationalerror" ^
 /c:"econnrefused" /c:"etimedout" /c:"errno 1045" /c:"errno 2003" /c:"lost connection" ^
 /c:"Traceback" ^
 "%RUNLOG%" >nul 2>&1 && set "HAS_TXT_ERROR=1"

type "%RUNLOG%" >> "%LOG%"

if "!HAS_TXT_ERROR!"=="1" (
  call :alert_on_error 0 "ALERTA: Se detectaron mensajes que podrían indicar un error (conexion/DB/etc.) durante la ejecucion. Por favor, revisa el archivo %LOG%."
)

:after_run
del "%RUNLOG%" >nul 2>&1
call :rotate_if_needed

endlocal
exit /b

rem ============== Funciones ===================
:rotate_if_needed
if not exist "%LOG%" goto :eof
for %%A in ("%LOG%") do set "SIZE=%%~zA"
if "!SIZE!"=="" goto :eof
if !SIZE! LSS %MAX_SIZE% goto :eof

if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1
for /f %%I in ('powershell -NoP -C "(Get-Date).ToString(\"yyyyMMdd_HHmmss\")"') do set "TS=%%I"
move "%LOG%" "%LOGDIR%\sync_!TS!.log" >nul

for /f "skip=%KEEP_ROTATED% delims=" %%F in ('
  dir /b /o-d "%LOGDIR%\sync_*.log" 2^>nul
') do del "%LOGDIR%\%%F" >nul 2>&1
goto :eof

:alert_on_error
set "RC=%~1"
set "MSG=%~2"
powershell -NoProfile -Command ^
  "Add-Type -AssemblyName System.Windows.Forms; " ^
  "[System.Windows.Forms.MessageBox]::Show('%MSG%','ALERTA DE SINCRONIZACION',0,'Error')"
goto :eof