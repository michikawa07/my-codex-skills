@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "DRY_RUN="
if /i "%~1"=="--dry-run" (
    set "DRY_RUN=1"
    shift /1
)
if "%~1"=="" (
    >&2 echo Usage: print-pdf.cmd [--dry-run] "PDF path" ["printer name"]
    exit /b 2
)

set "PDF=%~f1"
set "PRINTER=%~2"
if not defined PRINTER set "PRINTER=FUJI XEROX ApeosPort-VII C2273 (31:de:9a)"
set "SUMATRA_DIR=%~dp0..\tools\SumatraPDF"
set "SUMATRA=%SUMATRA_DIR%\SumatraPDF-3.6.1-64.exe"
if not exist "%PDF%" (
    >&2 echo PDF not found: "%PDF%"
    exit /b 2
)
if not exist "%SUMATRA%" (
    >&2 echo SumatraPDF not found: "%SUMATRA%"
    exit /b 2
)

if defined DRY_RUN (
    echo "%SUMATRA%" -print-to "%PRINTER%" -print-settings "shrink,1x" -appdata "%SUMATRA_DIR%" -silent "%PDF%"
    exit /b 0
)

start "" /b /wait "%SUMATRA%" -print-to "%PRINTER%" -print-settings "shrink,1x" -appdata "%SUMATRA_DIR%" -silent "%PDF%"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
    >&2 echo Print submission failed. Exit code: %RESULT%
    exit /b %RESULT%
)

echo PDF="%PDF%"
echo Printer="%PRINTER%"
echo Status=submitted
exit /b 0
