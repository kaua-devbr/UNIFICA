@echo off
cd /d "%~dp0"
if exist "instance\tls\cert.pem" (
    python app.py
) else (
    python instalar.py
)
if errorlevel 1 pause
