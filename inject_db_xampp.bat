@echo off
setlocal EnableExtensions

REM ------------------------------------------------------------
REM Importa el script db\xampp_setup.sql en MySQL (XAMPP)
REM ------------------------------------------------------------

cd /d "%~dp0"

set "SQL_FILE=db\xampp_setup.sql"
set "MYSQL_EXE=C:\xampp\mysql\bin\mysql.exe"
set "MYSQL_HOST=127.0.0.1"
set "MYSQL_PORT=3306"
set "MYSQL_USER=root"
set "MYSQL_PASSWORD="
set "LOG_FILE=inject_db_xampp.log"
set "EXIT_CODE=0"
set "PAUSE_ON_EXIT=1"

if /I "%~1"=="--no-pause" set "PAUSE_ON_EXIT=0"

if exist "%LOG_FILE%" del /q "%LOG_FILE%" >nul 2>&1

if not exist "%SQL_FILE%" (
    echo [ERROR] No se encontro el archivo SQL: %SQL_FILE%
    set "EXIT_CODE=1"
    goto :end
)

if not exist "%MYSQL_EXE%" (
    where mysql >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No se encontro mysql.exe.
        echo         Revisa la ruta en MYSQL_EXE o agrega MySQL al PATH.
        set "EXIT_CODE=1"
        goto :end
    )
    set "MYSQL_EXE=mysql"
)

echo [INFO] Ejecutando importacion de %SQL_FILE%...
echo [INFO] Guardando log en %LOG_FILE%
echo [INFO] Destino MySQL: %MYSQL_HOST%:%MYSQL_PORT% (usuario: %MYSQL_USER%)

call :test_connection
if not errorlevel 1 goto :conn_ok

for %%P in (3307 3308 3309) do (
    set "MYSQL_PORT=%%P"
    call :test_connection
    if not errorlevel 1 goto :conn_ok
)

echo [ERROR] No se pudo conectar a MySQL antes de importar.
echo [PISTA] Verifica en XAMPP el puerto de MySQL y ajusta MYSQL_PORT en este BAT.
echo [INFO] Revisa el detalle en %LOG_FILE%
set "EXIT_CODE=1"
goto :end

:conn_ok
echo [INFO] Conexion exitosa en puerto %MYSQL_PORT%.

if defined MYSQL_PASSWORD (
    "%MYSQL_EXE%" --protocol=TCP -h %MYSQL_HOST% -P %MYSQL_PORT% -u %MYSQL_USER% -p"%MYSQL_PASSWORD%" --default-character-set=utf8mb4 < "%SQL_FILE%" >> "%LOG_FILE%" 2>&1
) else (
    "%MYSQL_EXE%" --protocol=TCP -h %MYSQL_HOST% -P %MYSQL_PORT% -u %MYSQL_USER% --default-character-set=utf8mb4 < "%SQL_FILE%" >> "%LOG_FILE%" 2>&1
)

if errorlevel 1 (
    echo [ERROR] Fallo la importacion de la base de datos.
    echo [INFO] Revisa el detalle en %LOG_FILE%
    set "EXIT_CODE=1"
    goto :end
)

echo [OK] Base de datos importada correctamente.
echo [INFO] Revisa el detalle en %LOG_FILE%
goto :end

:test_connection
echo [INFO] Probando conexion en puerto %MYSQL_PORT%...>> "%LOG_FILE%"
if defined MYSQL_PASSWORD (
    "%MYSQL_EXE%" --protocol=TCP -h %MYSQL_HOST% -P %MYSQL_PORT% -u %MYSQL_USER% -p"%MYSQL_PASSWORD%" -e "SELECT VERSION();" >> "%LOG_FILE%" 2>&1
) else (
    "%MYSQL_EXE%" --protocol=TCP -h %MYSQL_HOST% -P %MYSQL_PORT% -u %MYSQL_USER% -e "SELECT VERSION();" >> "%LOG_FILE%" 2>&1
)
exit /b %errorlevel%

:end
echo.
if "%PAUSE_ON_EXIT%"=="1" pause
exit /b %EXIT_CODE%
