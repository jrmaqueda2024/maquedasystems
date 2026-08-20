# MAQUEDASYSTEMS — Cómo generar el ejecutable (Windows, Linux y macOS)

Este proyecto está listo para compilarse como un único ejecutable nativo
para **Windows** (`.exe`), **Linux** (binario) o **macOS** (`.app`),
usando PyInstaller y el mismo archivo `MaquedaSystems.spec` para las tres
plataformas.

**Importante:** PyInstaller no "cruza" plataformas — hay que compilar EN
cada sistema operativo por separado. No se puede generar el `.exe` de
Windows compilando desde Linux/Mac, ni el binario de Linux o el `.app` de
Mac compilando desde Windows. Si necesitás los tres ejecutables, hay que
correr el script correspondiente en una PC/Mac de cada sistema operativo.

## Requisitos previos (los tres sistemas operativos)

1. Tener **Python 3.10 o superior** instalado.
   - Windows: https://www.python.org/downloads/ (marcá **"Add Python to
     PATH"** durante la instalación).
   - Linux: viene preinstalado en la mayoría de las distros, o
     `sudo apt install python3 python3-pip python3-tk` (Debian/Ubuntu).
   - macOS: https://www.python.org/downloads/macos/ (ya incluye Tk), o
     con Homebrew: `brew install python-tk`.
2. Tener este proyecto descomprimido en una carpeta de tu equipo.

---

## Windows

### Opción A — Un solo click (recomendado)

1. Hacé doble click en **`compilar_exe.bat`**.
2. Esperá a que termine (instala las dependencias y compila; puede
   tardar varios minutos la primera vez).
3. El ejecutable final queda en la carpeta `dist\MaquedaSystems.exe`.

### Opción B — Manual, paso a paso

Abrí la **Símbolo del sistema (cmd)** o **PowerShell** dentro de la
carpeta del proyecto y ejecutá:

```
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller MaquedaSystems.spec --noconfirm
```

El ejecutable queda en `dist\MaquedaSystems.exe`.

---

## Linux

### Opción A — Un solo script (recomendado)

1. Abrí una terminal dentro de la carpeta del proyecto.
2. Ejecutá:
   ```
   chmod +x compilar_linux.sh
   ./compilar_linux.sh
   ```
3. El ejecutable final queda en `dist/MaquedaSystems`.

### Opción B — Manual, paso a paso

```
python3 -m pip install -r requirements.txt --break-system-packages
python3 -m pip install pyinstaller --break-system-packages
python3 -m PyInstaller MaquedaSystems.spec --noconfirm
```

(`--break-system-packages` es necesario en distros con Python
"externally managed", como Debian 12+/Ubuntu 23.04+; en distros más
viejas simplemente se puede omitir esa opción.)

El binario queda en `dist/MaquedaSystems` — dale permiso de ejecución
si hace falta con `chmod +x dist/MaquedaSystems`.

---

## macOS

### Opción A — Un solo script (recomendado)

1. Abrí la Terminal dentro de la carpeta del proyecto.
2. Ejecutá:
   ```
   chmod +x compilar_mac.sh
   ./compilar_mac.sh
   ```
3. La aplicación final queda en `dist/MaquedaSystems.app`.

### Opción B — Manual, paso a paso

```
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller
python3 -m PyInstaller MaquedaSystems.spec --noconfirm
```

La app queda en `dist/MaquedaSystems.app`.

**Primera apertura:** macOS puede advertir que `MaquedaSystems.app` es
de un "desarrollador no identificado" (no está firmada ni notarizada
con una cuenta de Apple Developer). Para abrirla la primera vez: click
derecho sobre el `.app` → **Abrir** → confirmar en el diálogo. Las
veces siguientes se abre normal con doble click.

---

## Después de compilar (los tres sistemas operativos)

- Copiá el ejecutable/app a la carpeta donde quieras que viva el sistema
  de forma permanente (por ejemplo `C:\MaquedaSystems\` en Windows, o
  `/Applications` en Mac).
- La primera vez que se abre, se crea automáticamente junto a él:
  - `ventas.db` — la base de datos (productos, ventas, usuarios, etc.)
  - `fotos_perfil/` — fotos de perfil de los usuarios
  - `imagenes_productos/` — fotos de los productos
- Todos estos archivos persisten entre ejecuciones: se puede cerrar el
  programa y volver a abrirlo sin perder nada.
- Para hacer una copia de seguridad completa, simplemente copiá esa
  carpeta entera (el ejecutable/app + `ventas.db` + las subcarpetas).
- La impresión directa en impresoras/ticketeras usa el spooler nativo
  de Windows en `.exe`, y CUPS (`lp`/`lpr`) en Linux y macOS — no hace
  falta ningún driver adicional del sistema más allá de tener la
  impresora ya configurada en el sistema operativo.

## Notas técnicas

- Los tres ejecutables se compilan en modo `--onefile` (un único
  archivo, o `.app` autocontenido en Mac) y modo ventana
  (`console=False`), así que no aparece ninguna consola negra al
  abrirlos.
- El ícono (`icono.ico`) se usa automáticamente en Windows. En macOS,
  si existe un `icono.icns` en la carpeta del proyecto se usa para el
  `.app`; si no existe, el `.app` compila igual pero queda con el
  ícono genérico de macOS. En Linux no aplica (PyInstaller lo ignora).
- Las rutas de archivos persistentes (base de datos, fotos) están
  programadas para usar siempre la carpeta donde está el
  ejecutable/app, no una carpeta temporal — ver
  `utilidades_ui.obtener_carpeta_base()`.
- Si Windows Defender o un antivirus marca el `.exe` como sospechoso
  la primera vez, es un falso positivo común con ejecutables generados
  por PyInstaller (no están firmados digitalmente); podés agregar una
  excepción o firmarlo vos mismo con un certificado si lo vas a
  distribuir a terceros. Lo mismo aplica al aviso de "desarrollador no
  identificado" en macOS.
- `MaquedaSystems.spec` detecta automáticamente TODOS los módulos que
  `main.py` termina importando (directa o indirectamente, incluidos
  los imports "perezosos" dentro de cada módulo del menú lateral), así
  que no hace falta tocar el `.spec` cada vez que se agrega un módulo
  nuevo al sistema — esto ya se verificó compilando el proyecto
  completo con éxito.
- **Versionado del sistema:** el número de versión (visible dentro del
  sistema en el módulo Novedades, arriba a la derecha) se calcula
  automáticamente a partir de la lista `NOVEDADES` en
  `ventana_novedades.py` — cada entrada nueva etiquetada "Nuevo" sube
  el número MINOR (1.5.3 → 1.6.0) y cada "Mejora"/"Corrección" sube el
  PATCH (1.6.0 → 1.6.1), arrancando desde la versión histórica 1.0.0.
  Esta versión NO se propaga sola al instalador ni al nombre del
  ejecutable — solo se usa dentro de la app. La única excepción es
  `CFBundleShortVersionString` en `MaquedaSystems.spec` (metadata del
  `.app` de macOS), que hay que actualizar a mano si se quiere que
  coincida con la versión más reciente de Novedades.

## Dependencias incluidas

| Librería      | Uso                                                |
|---------------|-----------------------------------------------------|
| Pillow        | Fotos de perfil, logo, imágenes de productos, ícono de la Calculadora |
| reportlab     | Generación de reportes en PDF                      |
| openpyxl      | Exportar/importar Excel                            |
| python-docx   | Generación de reportes en Word                     |
| odfpy         | Generación de reportes en formato OpenDocument     |
| PyInstaller   | Compilación del ejecutable (solo necesario para build) |
| pywin32       | Driver de impresoras (solo Windows; en Linux/Mac se usa CUPS en su lugar) |

Todo lo demás (Terminal SQL, Asistente IA, Idioma, Clima, Calculadora,
Veterinaria, Restaurante/Comedor, Streaming, Locales, etc.) usa
únicamente la librería estándar de Python (`urllib`, `json`, `sqlite3`,
`threading`, `math`, `tkinter`), así que no necesita nada adicional en
`requirements.txt`.
