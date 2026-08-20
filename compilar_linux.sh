#!/bin/bash
# compilar_linux.sh
# Genera el ejecutable nativo de MAQUEDASYSTEMS para Linux (binario ELF de
# archivo único), usando PyInstaller. Equivalente a compilar_exe.bat pero
# para Linux — debe ejecutarse EN una PC con Linux (no se puede generar
# el binario de Linux compilando desde Windows/Mac).

set -e

# Forzar el directorio de trabajo a la carpeta donde está este script, sin
# importar desde dónde se haya ejecutado (doble click, otra terminal
# abierta en otra carpeta, etc.).
cd "$(dirname "$0")"

echo "============================================================"
echo "  MAQUEDASYSTEMS - Generador de ejecutable para Linux"
echo "============================================================"
echo
echo "Carpeta de trabajo: $(pwd)"
echo
echo "Este script instala las dependencias necesarias y compila"
echo "el sistema completo en un unico binario 'MaquedaSystems'."
echo
echo "Requisitos: tener Python 3.10+ instalado (python3 y pip3), y"
echo "el paquete de Tk del sistema operativo (python3-tk) — en"
echo "Debian/Ubuntu: sudo apt install python3-tk"
echo
read -p "Presiona Enter para continuar..."

echo
echo "Verificando que los archivos del proyecto esten presentes..."
if [ ! -f "requirements.txt" ]; then
    echo
    echo "ERROR: No se encontro requirements.txt en esta carpeta."
    echo "  Carpeta actual: $(pwd)"
    echo
    echo "Asegurate de que compilar_linux.sh este en la MISMA carpeta"
    echo "que requirements.txt, MaquedaSystems.spec y main.py"
    echo "(es decir, dentro de la carpeta MaquedaSystems extraida del zip)."
    exit 1
fi
if [ ! -f "main.py" ]; then
    echo
    echo "ERROR: No se encontro main.py en esta carpeta."
    echo "  Carpeta actual: $(pwd)"
    exit 1
fi
echo "OK."

PYTHON_BIN="python3"
if ! command -v $PYTHON_BIN &> /dev/null; then
    echo
    echo "ERROR: No se encontro 'python3'. Instala Python 3.10 o superior"
    echo "  (por ejemplo: sudo apt install python3 python3-pip python3-venv python3-tk)."
    exit 1
fi

echo
echo "Verificando que Tkinter este disponible (python3-tk)..."
if ! $PYTHON_BIN -c "import tkinter" &> /dev/null; then
    echo
    echo "ERROR: Falta el paquete de Tk del sistema. Instalalo con:"
    echo "  Debian/Ubuntu:  sudo apt install python3-tk"
    echo "  Fedora:         sudo dnf install python3-tkinter"
    echo "  Arch:           sudo pacman -S tk"
    exit 1
fi
echo "OK."

echo
echo "[1/3] Instalando TODAS las dependencias en un solo paso"
echo "      (Pillow, reportlab, openpyxl, python-docx, odfpy, etc.)"
echo "      Puede tardar unos minutos la primera vez..."

# NOTA: no se actualiza pip en sí (paso opcional) porque en distros con
# Python "externally managed" (Debian 12+/Ubuntu 23.04+) intentar
# reinstalar el pip que vino con el sistema puede fallar sin que eso
# afecte la compilación en absoluto — mejor omitirlo directamente.
# --break-system-packages es necesario en esas mismas distros para poder
# instalar paquetes de PyPI; en versiones de pip que no reconocen esa
# opción, se reintenta sin ella.
if ! $PYTHON_BIN -m pip install -r requirements.txt --break-system-packages; then
    echo "Reintentando sin --break-system-packages..."
    $PYTHON_BIN -m pip install -r requirements.txt
fi
if ! $PYTHON_BIN -m pip install pyinstaller --break-system-packages; then
    echo "Reintentando sin --break-system-packages..."
    $PYTHON_BIN -m pip install pyinstaller
fi

echo
echo "[2/3] Compilando el ejecutable con PyInstaller..."
$PYTHON_BIN -m PyInstaller MaquedaSystems.spec --noconfirm

echo
echo "[3/3] Listo."
echo
echo "============================================================"
echo "  El ejecutable se genero en:  dist/MaquedaSystems"
echo "============================================================"
echo
echo "IMPORTANTE:"
echo "- Dale permiso de ejecucion si hace falta:  chmod +x dist/MaquedaSystems"
echo "- Copia ese binario a la carpeta donde quieras que viva el"
echo "  sistema (la base de datos, fotos de perfil e imagenes de"
echo "  productos se crearan automaticamente junto a el)."
echo "- La impresion directa en ticketeras usa CUPS (lp/lpr) en Linux;"
echo "  asegurate de tener la impresora configurada en el sistema."
echo
