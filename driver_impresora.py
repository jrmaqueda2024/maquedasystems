"""
driver_impresora.py
Driver universal de impresión para MAQUEDASYSTEMS.

Objetivo: comunicarse con CUALQUIER impresora instalada en Windows, sin
importar marca ni modelo, tanto impresoras normales (láser/inyección,
hoja A4) como impresoras ticketeras térmicas (58mm/80mm).

Cómo lo logra (sin necesitar un driver específico por marca):
- Usa el spooler de Windows (win32print), que ya sabe hablar con cualquier
  impresora que el usuario tenga instalada en "Dispositivos e impresoras"
  — Epson, Xprinter, HP, Canon, Bixolon, genéricas, etc. No hace falta que
  este programa conozca el modelo puntual.
- Para documentos de página completa (Factura A4): entrega el PDF ya
  generado a la impresora elegida usando el verbo "printto" de Windows
  (lo mismo que hace un usuario al click derecho > Imprimir sobre un PDF,
  pero eligiendo la impresora por código en vez de por diálogo).
- Para tickets angostos (Ticketera 80mm/58mm): en vez de mandar un PDF
  (que muchas impresoras térmicas económicas no renderizan bien), manda el
  TEXTO PLANO del comprobante directamente al spooler en modo RAW. Esto es
  el estándar de la industria para impresoras de punto de venta: cualquier
  impresora térmica ESC/POS lo acepta sin necesitar controlador propio,
  porque Windows simplemente reenvía los bytes tal cual.

Todo lo de acá es Windows-only (pywin32); en otros sistemas operativos cae
de forma segura a alternativas (CUPS 'lp'/'lpr' en Linux/Mac, o simplemente
abrir el archivo) para que el desarrollo/pruebas fuera de Windows no rompan.
"""
import sys
import os
import subprocess

try:
    import win32print
    import win32api
    WIN32_OK = True
except ImportError:
    WIN32_OK = False


class ErrorImpresora(Exception):
    """Cualquier problema al listar impresoras o enviar un trabajo de
    impresión termina acá, con un mensaje pensado para mostrarle
    directamente al usuario (no un traceback técnico)."""
    pass


# ─────────────────────────────────────────────────────────────
#  DETECCIÓN DE IMPRESORAS INSTALADAS
# ─────────────────────────────────────────────────────────────

def listar_impresoras() -> list[str]:
    """Devuelve los nombres de todas las impresoras instaladas en el
    equipo (locales, de red, y virtuales como 'Microsoft Print to PDF'),
    sin importar marca o modelo. Lista vacía si no se puede detectar
    (plataforma no soportada, o sin impresoras instaladas)."""
    if WIN32_OK:
        try:
            banderas = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            impresoras = win32print.EnumPrinters(banderas)
            # Cada elemento es una tupla (flags, description, name, comment)
            return sorted({p[2] for p in impresoras})
        except Exception:
            return []
    if sys.platform.startswith("linux") or sys.platform == "darwin":
        try:
            salida = subprocess.run(["lpstat", "-a"], capture_output=True, text=True, timeout=3)
            return [linea.split()[0] for linea in salida.stdout.splitlines() if linea.strip()]
        except Exception:
            return []
    return []


def impresora_predeterminada() -> str:
    """Nombre de la impresora predeterminada del sistema, o '' si no se
    pudo determinar."""
    if WIN32_OK:
        try:
            return win32print.GetDefaultPrinter()
        except Exception:
            return ""
    return ""


def hay_impresoras_disponibles() -> bool:
    return len(listar_impresoras()) > 0


# ─────────────────────────────────────────────────────────────
#  IMPRESIÓN DE PDF (Factura A4, o cualquier documento de página
#  completa) EN UNA IMPRESORA ESPECÍFICA
# ─────────────────────────────────────────────────────────────

def imprimir_pdf(ruta: str, nombre_impresora: str = None):
    """Envía un PDF ya generado a imprimir. Si se indica 'nombre_impresora',
    se imprime específicamente ahí (sin importar cuál sea la
    predeterminada); si no, usa la predeterminada del sistema.

    Requiere que el sistema tenga una aplicación asociada a PDF capaz de
    imprimir (Adobe Reader, Microsoft Edge, etc. — Windows 10/11 ya trae
    uno por defecto)."""
    if not os.path.exists(ruta):
        raise ErrorImpresora(f"No se encontró el archivo a imprimir:\n{ruta}")

    if sys.platform == "win32":
        try:
            if nombre_impresora:
                # 'printto' permite elegir la impresora explícitamente.
                win32api.ShellExecute(0, "printto", ruta, f'"{nombre_impresora}"', ".", 0)
            else:
                win32api.ShellExecute(0, "print", ruta, None, ".", 0)
        except Exception as e:
            raise ErrorImpresora(
                f"No se pudo enviar el PDF a la impresora.\n\n"
                f"Verificá que tengas un lector de PDF instalado (Adobe Reader, "
                f"Microsoft Edge, etc.) con soporte de impresión.\n\nDetalle: {e}"
            )
    elif sys.platform == "darwin":
        cmd = ["lp"]
        if nombre_impresora:
            cmd += ["-d", nombre_impresora]
        cmd.append(ruta)
        subprocess.run(cmd, check=False)
    else:
        cmd = ["lp"]
        if nombre_impresora:
            cmd += ["-d", nombre_impresora]
        cmd.append(ruta)
        subprocess.run(cmd, check=False)


# ─────────────────────────────────────────────────────────────
#  IMPRESIÓN "CRUDA" (RAW / ESC-POS) — IDEAL PARA TICKETERAS
#  TÉRMICAS DE 58mm/80mm, SIN IMPORTAR MARCA
# ─────────────────────────────────────────────────────────────

# Comandos ESC/POS básicos, soportados por prácticamente cualquier
# impresora térmica (Epson TM-T, Xprinter, Bixolon, genéricas chinas, etc.)
ESC_POS_INICIALIZAR = b"\x1b\x40"          # ESC @  → resetear impresora
ESC_POS_CORTE_PAPEL = b"\x1d\x56\x00"      # GS V 0 → corte total de papel
ESC_POS_ABRIR_CAJON = b"\x1b\x70\x00\x19\xfa"  # ESC p → abrir cajón de dinero (si está conectado)


def imprimir_texto_raw(texto: str, nombre_impresora: str = None,
                        cortar_papel: bool = True, abrir_cajon: bool = False,
                        nombre_trabajo: str = "Comprobante"):
    """Envía texto plano DIRECTO al spooler de Windows en modo RAW, sin
    pasar por ningún renderizador de páginas. Es el método estándar para
    imprimir tickets en impresoras térmicas de punto de venta: cualquier
    impresora ESC/POS (sea cual sea la marca) lo entiende, porque Windows
    simplemente reenvía los bytes tal cual, sin necesitar un driver que
    sepa "maquetar" una página.

    Si no se indica 'nombre_impresora', usa la predeterminada del sistema.
    """
    if not WIN32_OK:
        raise ErrorImpresora(
            "La impresión directa en ticketeras requiere pywin32, que no "
            "está disponible en este sistema.\n\n"
            "Instalalo con: pip install pywin32"
        )

    destino = nombre_impresora or impresora_predeterminada()
    if not destino:
        raise ErrorImpresora(
            "No se encontró ninguna impresora predeterminada ni se indicó "
            "una impresora específica. Conectá/configurá una impresora en "
            "Windows (Configuración → Impresoras y escáneres)."
        )

    cuerpo = texto.encode("cp437", errors="replace")  # codificación clásica ESC/POS
    datos = ESC_POS_INICIALIZAR + cuerpo + b"\n\n\n"
    if cortar_papel:
        datos += ESC_POS_CORTE_PAPEL
    if abrir_cajon:
        datos += ESC_POS_ABRIR_CAJON

    try:
        handle = win32print.OpenPrinter(destino)
    except Exception as e:
        raise ErrorImpresora(
            f"No se pudo abrir la impresora '{destino}'.\n\n"
            f"Verificá que esté encendida, conectada, y que Windows la "
            f"detecte en 'Impresoras y escáneres'.\n\nDetalle: {e}"
        )

    try:
        win32print.StartDocPrinter(handle, 1, (nombre_trabajo, None, "RAW"))
        try:
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, datos)
            win32print.EndPagePrinter(handle)
        finally:
            win32print.EndDocPrinter(handle)
    except Exception as e:
        raise ErrorImpresora(f"No se pudo enviar el trabajo de impresión:\n{e}")
    finally:
        win32print.ClosePrinter(handle)


# ─────────────────────────────────────────────────────────────
#  FUNCIÓN DE ALTO NIVEL: elige automáticamente RAW (ticketera) o
#  PDF (hoja completa) según el formato configurado.
# ─────────────────────────────────────────────────────────────

def imprimir_documento(formato: str, nombre_impresora: str = None, *,
                       texto: str = None, ruta_pdf_callback=None,
                       cortar_papel: bool = True, nombre_trabajo: str = "Documento"):
    """Punto de entrada único para imprimir un comprobante/factura ya
    generado, eligiendo automáticamente el método más apropiado:

    - formato == 'a4'  → imprime el PDF (se genera al vuelo llamando a
      ruta_pdf_callback(), que debe devolver la ruta del archivo).
    - formato en ('ticket80', 'ticket58') → imprime 'texto' directo en modo
      RAW/ESC-POS (sin generar PDF), ideal para impresoras térmicas.

    Devuelve una descripción corta de lo que se hizo, para mostrar en un
    mensaje de confirmación."""
    if formato == "a4":
        if ruta_pdf_callback is None:
            raise ErrorImpresora("Falta generar el PDF antes de imprimir en Hoja A4.")
        ruta = ruta_pdf_callback()
        imprimir_pdf(ruta, nombre_impresora=nombre_impresora)
        destino = nombre_impresora or impresora_predeterminada() or "la impresora predeterminada"
        return f"Documento enviado a '{destino}' (hoja A4)."
    else:
        if texto is None:
            raise ErrorImpresora("Falta el texto del ticket a imprimir.")
        imprimir_texto_raw(texto, nombre_impresora=nombre_impresora,
                           cortar_papel=cortar_papel, nombre_trabajo=nombre_trabajo)
        destino = nombre_impresora or impresora_predeterminada() or "la impresora predeterminada"
        return f"Ticket enviado a '{destino}' (impresión directa, sin PDF)."
