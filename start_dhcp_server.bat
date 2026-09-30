@echo off
setlocal
cd /d "%~dp0"
start "OIL fixed DHCP service" /min python -m oil.dhcp_server "%~dp0instruments.local.yaml"
endlocal
