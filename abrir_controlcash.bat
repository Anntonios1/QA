@echo off
echo Iniciando ControlCash con microfono habilitado...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --unsafely-treat-insecure-origin-as-secure=http://26.80.35.167:8080 ^
  --user-data-dir="%TEMP%\chrome_controlcash" ^
  http://26.80.35.167:8080/controlcash/
