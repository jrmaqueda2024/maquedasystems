#!/bin/bash
# compilar_mac.sh
# Genera la aplicación nativa de MAQUEDASYSTEMS para macOS (MaquedaSystems.app),
# usando PyInstaller. Equivalente a compilar_exe.bat pero para Mac — debe
# ejecutarse EN una Mac (no se puede generar el .app compilando desde
# Windows/Linux).

set -e

# Forzar el directorio de trabajo a la carpeta donde está este script, sin
# importar desde dónde se haya ejecutado.
cd "$(dirname "$0")"

echo "============================================================"
echo "  MAQUEDASYSTEMS - Generador de aplicación para macOS"
echo "============================================================"
echo
echo "Carpeta de trabajo: $(pwd)"
echo
echo "Este script instala las dependencias necesarias y compila"
echo "el sistema completo en MaquedaSystems.app"
echo
echo "Requisitos: tener Python 3.10+ instalado (con soporte de Tk;"
echo "la versión de python.org para Mac ya lo incluye). Si usás"
echo "Homebrew: brew install python-tk"
echo
read -p "Presiona Enter para continuar..."

echo
echo "Verificando que los archivos del proyecto esten presentes..."
if [ ! -f "requirements.txt" ]; then
    echo
    echo "ERROR: No se encontro requirements.txt en esta carpeta."
    echo "  Carpeta actual: $(pwd)"
    echo
    echo "Asegurate de que compilar_mac.sh este en la MISMA carpeta"
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
    echo "  desde https://www.python.org/downloads/macos/ (recomendado, ya"
    echo "  incluye Tk) o con Homebrew: brew install python-tk"
    exit 1
fi

echo
echo "Verificando que Tkinter este disponible..."
if ! $PYTHON_BIN -c "import tkinter" &> /dev/null; then
    echo
    echo "ERROR: Falta el soporte de Tk en este Python. Instalalo con:"
    echo "  Homebrew:  brew install python-tk"
    echo "  o reinstalá Python desde python.org (incluye Tk)."
    exit 1
fi
echo "OK."

echo
echo "[1/3] Instalando TODAS las dependencias en un solo paso"
echo "      (Pillow, reportlab, openpyxl, python-docx, odfpy, etc.)"
echo "      Puede tardar unos minutos la primera vez..."
$PYTHON_BIN -m pip install --upgrade pip
$PYTHON_BIN -m pip install -r requirements.txt
$PYTHON_BIN -m pip install pyinstaller

echo
echo "[2/3] Compilando la aplicación con PyInstaller..."
$PYTHON_BIN -m PyInstaller MaquedaSystems.spec --noconfirm

echo
echo "[3/3] Listo."
echo
echo "============================================================"
echo "  La aplicación se genero en:  dist/MaquedaSystems.app"
echo "============================================================"
echo
echo "IMPORTANTE:"
echo "- Movete/copiá MaquedaSystems.app a la carpeta donde quieras que"
echo "  viva el sistema (por ejemplo /Applications o una carpeta propia;"
echo "  la base de datos, fotos de perfil e imagenes de productos se"
echo "  crearan automaticamente junto a el)."
echo "- La primera vez que lo abras, macOS puede advertir que es de un"
echo "  'desarrollador no identificado' (no está firmado ni notarizado)."
echo "  Para abrirlo: click derecho sobre MaquedaSystems.app > Abrir, y"
echo "  confirmar en el diálogo. Solo hace falta la primera vez."
echo "- La impresión directa en ticketeras usa CUPS (lp/lpr) en macOS;"
echo "  asegurate de tener la impresora configurada en Preferencias del"
echo "  Sistema."
echo
