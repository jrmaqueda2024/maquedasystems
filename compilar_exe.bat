@echo off
chcp 65001 >nul

REM Forzar el directorio de trabajo a la carpeta donde está este .bat,
REM sin importar desde dónde se haya ejecutado (doble click, acceso
REM directo, otra terminal abierta en otra carpeta, etc.). Sin esto,
REM "pip install -r requirements.txt" puede fallar con "No such file"
REM si Windows abrió la consola con otro directorio de trabajo activo.
cd /d "%~dp0"

echo ============================================================
echo   MAQUEDASYSTEMS - Generador de ejecutable .exe
echo ============================================================
echo.
echo Carpeta de trabajo: %cd%
echo.
echo Este script instala las dependencias necesarias y compila
echo el sistema completo en un unico archivo MaquedaSystems.exe
echo.
echo Requisitos: tener Python 3.10+ instalado y agregado al PATH.
echo.
pause

echo.
echo Verificando que los archivos del proyecto esten presentes...
if not exist "requirements.txt" (
    echo.
    echo ERROR: No se encontro requirements.txt en esta carpeta.
    echo   Carpeta actual: %cd%
    echo.
    echo Asegurate de que compilar_exe.bat este en la MISMA carpeta
    echo que requirements.txt, MaquedaSystems.spec y main.py
    echo ^(es decir, dentro de la carpeta MaquedaSystems extraida del zip^).
    pause
    exit /b 1
)
if not exist "main.py" (
    echo.
    echo ERROR: No se encontro main.py en esta carpeta.
    echo   Carpeta actual: %cd%
    pause
    exit /b 1
)
echo OK.

echo.
echo [1/3] Instalando TODAS las dependencias en un solo paso
echo       (Pillow, reportlab, openpyxl, python-docx, odfpy, pywin32, etc.)
echo       Puede tardar unos minutos la primera vez...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: No se pudieron instalar las dependencias.
    echo Verifica que Python este instalado y agregado al PATH.
    pause
    exit /b 1
)

echo.
echo       Verificando que el driver de impresoras (pywin32) haya quedado
echo       instalado correctamente...
python -c "import win32print, win32api" 2>nul
if errorlevel 1 (
    echo.
    echo ADVERTENCIA: pywin32 no se instalo correctamente. La deteccion e
    echo impresion directa en ticketeras no va a funcionar, pero el resto
    echo del sistema si. Se puede reintentar con:
    echo     python -m pip install --force-reinstall pywin32
    echo.
    pause
) else (
    echo       OK - driver de impresoras listo.
)

echo.
echo [2/3] Compilando el ejecutable con PyInstaller...
python -m PyInstaller MaquedaSystems.spec --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Fallo la compilacion. Revisa los mensajes de arriba.
    pause
    exit /b 1
)

echo.
echo [3/3] Listo.
echo.
echo ============================================================
echo   El ejecutable se genero en:  dist\MaquedaSystems.exe
echo ============================================================
echo.
echo IMPORTANTE: copia ese .exe a la carpeta donde quieras que
echo viva el sistema (la base de datos, fotos de perfil e imagenes
echo de productos se crearan automaticamente junto a el).
echo.
pause
