# -*- mode: python ; coding: utf-8 -*-
"""
MaquedaSystems.spec
Archivo de configuración de PyInstaller para compilar MAQUEDASYSTEMS
como un único ejecutable para Windows (.exe), Linux o macOS (.app).

Este MISMO archivo .spec sirve para las tres plataformas: PyInstaller
genera automáticamente el formato correcto según el sistema operativo
donde se ejecute la compilación (no hay que tocar nada acá para
cambiar de plataforma). Lo que sí hace falta es compilar EN cada
sistema operativo por separado (Windows, Linux o macOS) — PyInstaller
no puede "cruzar" plataformas, por ejemplo no se puede generar el
.exe de Windows compilando desde Linux/Mac, ni al revés. Ver
compilar_exe.bat (Windows), compilar_linux.sh (Linux) o
compilar_mac.sh (macOS), y COMO_GENERAR_EJECUTABLES.md para más
detalle.

Analysis(['main.py']) detecta automáticamente TODOS los módulos del
sistema que main.py importa (directa o indirectamente, incluidos los
imports "perezosos" dentro de funciones como los de cada módulo del
menú lateral) — no hace falta listarlos uno por uno acá. Esto incluye,
sin necesidad de tocar este archivo, los módulos más recientes: Terminal
SQL, Asistente IA (con su configuración de proveedor/clave de API),
Idioma (Español/Guaraní/Português/English/Русский/中文/한국어/Українська/
العربية), Clima, Veterinaria, Restaurante/Comedor, Alquiler de
Streaming, Armar Venta por Locales y la Calculadora — todos usan
únicamente la librería estándar de Python (urllib, json, sqlite3,
threading, math, etc.), así que tampoco hace falta agregar nada a
requirements.txt ni a hidden_imports por ellos.

USO:
    pip install -r requirements.txt
    pip install pyinstaller
    pyinstaller MaquedaSystems.spec

El ejecutable resultante queda en la carpeta dist/:
  - Windows: dist/MaquedaSystems.exe
  - Linux:   dist/MaquedaSystems  (binario ELF)
  - macOS:   dist/MaquedaSystems.app (paquete de aplicación)
"""

import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Submódulos que PyInstaller no detecta automáticamente porque se importan
# de forma dinámica/condicional en el código (reportlab y docx, por ejemplo,
# registran varios plugins internos que el análisis estático no ve).
hidden_imports = (
    collect_submodules('reportlab')
    + collect_submodules('docx')
    + collect_submodules('odf')
    + collect_submodules('openpyxl')
    + ['PIL._tkinter_finder']
)

# pywin32 (driver de impresoras): solo aplica en Windows. 'win32timezone'
# es un módulo interno que pywin32 necesita en tiempo de ejecución pero que
# PyInstaller no detecta solo — si falta, el .exe compila bien pero al
# imprimir puede fallar con "No module named win32timezone". Se agrega acá
# a propósito para que quede embebido en el .exe y funcione en cualquier
# PC sin tener que instalar nada aparte. En Linux/Mac, driver_impresora.py
# ya cae solo a CUPS ('lp'/'lpr') sin necesitar nada de esto.
if sys.platform == 'win32':
    hidden_imports += [
        'win32print', 'win32api', 'win32con', 'win32timezone', 'win32gui',
        'pywintypes', 'pythoncom',
    ]

# Archivos de datos que deben quedar embebidos dentro del ejecutable (assets
# de solo lectura: logo del login e ícono). NO incluye la base de datos ni
# las fotos de perfil, que se crean en tiempo de ejecución junto al
# ejecutable (o junto al .app en macOS — ver utilidades_ui.obtener_carpeta_base()).
datos = [
    ('logo.jpg', '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datos,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Ícono: .ico en Windows. En Linux no aplica (PyInstaller lo ignora en ELF).
# En macOS se usaría un .icns (no incluido en este proyecto todavía); sin
# archivo .icns, se compila igual pero el .app queda con el ícono genérico
# de macOS — no impide que funcione.
if sys.platform == 'win32':
    _icono = 'icono.ico'
elif sys.platform == 'darwin' and __import__('os').path.exists('icono.icns'):
    _icono = 'icono.icns'
else:
    _icono = None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MaquedaSystems',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # False = sin ventana de consola negra detrás
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icono,
)

# En macOS, además del binario "exe" de arriba, se arma el paquete .app
# (carpeta con la estructura que espera Finder/Launchpad) para que se
# pueda abrir con doble click como cualquier aplicación de Mac. En
# Windows y Linux este paso se omite: el binario de EXE ya es el
# ejecutable final tal cual (.exe / binario ELF).
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='MaquedaSystems.app',
        icon=_icono,
        bundle_identifier='py.maquedasystems.app',
        info_plist={
            'NSHighResolutionCapable': 'True',
            # Ver ventana_novedades.py -> VERSION_ACTUAL: se calcula
            # automáticamente a partir de la primera entrada (la más
            # reciente) de la lista NOVEDADES, que sigue versionado
            # semántico MAJOR.MINOR.PATCH desde la versión histórica
            # 1.0.0. Si se agrega una novedad nueva y VERSION_ACTUAL
            # cambia, hay que actualizar este número a mano acá también
            # (no se puede importar ventana_novedades.py directamente
            # desde este .spec sin arrastrar tkinter y otras
            # dependencias pesadas al proceso de build).
            'CFBundleShortVersionString': '1.40.0',
        },
    )

