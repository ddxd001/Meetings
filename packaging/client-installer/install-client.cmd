@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-client.ps1"
exit /b %ERRORLEVEL%
