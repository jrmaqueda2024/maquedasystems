"""
models_comprobante.py
Gestión de la configuración del local (datos que aparecen en los
comprobantes de venta y facturas) y la numeración correlativa.
"""
import sqlite3
from database import conectar
from utilidades_ui import formatear_gs

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import mm
    PDF_OK = True
except ImportError:
    PDF_OK = False


# ─────────────────────────────────────────────────────────────
#  TAMAÑOS DE PAPEL SOPORTADOS: hoja A4 o rollo de ticketera
# ─────────────────────────────────────────────────────────────

FORMATOS_IMPRESION = {
    "a4":       {"etiqueta": "Hoja A4",         "ancho_txt": 56, "fuente": 10},
    "ticket80": {"etiqueta": "Ticketera 80mm",  "ancho_txt": 42, "fuente": 8,
                 "ancho_mm": 80, "margen_mm": 3},
    "ticket58": {"etiqueta": "Ticketera 58mm",  "ancho_txt": 32, "fuente": 7,
                 "ancho_mm": 58, "margen_mm": 2.5},
}


def ancho_texto_para_formato(formato: str) -> int:
    """Devuelve cuántos caracteres por línea entran en el tamaño de papel
    elegido, para armar la vista previa / el texto del comprobante."""
    return FORMATOS_IMPRESION.get(formato, FORMATOS_IMPRESION["a4"])["ancho_txt"]


# ─────────────────────────────────────────────────────────────
#  INICIALIZACIÓN
# ─────────────────────────────────────────────────────────────

def inicializar_tablas_comprobante():
    conn = conectar()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS config_local (
            clave   TEXT PRIMARY KEY,
            valor   TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS numeracion_comprobante (
            tipo            TEXT PRIMARY KEY,
            establecimiento TEXT NOT NULL DEFAULT '001',
            punto_exp       TEXT NOT NULL DEFAULT '001',
            ultimo_numero   INTEGER NOT NULL DEFAULT 0
        );
    """)

    # Valores por defecto si no existen
    defaults = [
        ("nombre_local",        "Nombre Local"),
        ("ruc",                 ""),
        ("razon_social",        ""),
        ("direccion",           ""),
        ("telefono",            ""),
        ("email",               ""),
        ("ciudad",              "Asunción"),
        ("actividad_economica", ""),
        ("timbrado_nro",        ""),
        ("timbrado_vigencia_desde", ""),
        ("timbrado_vigencia_hasta", ""),
        ("tipo_iva",            "10"),  # 10, 5, o exento
        ("incluye_iva",         "1"),   # 1 = precios incluyen IVA
        ("mensaje_pie",         "¡Gracias por su compra!"),
        ("formato_comprobante", "a4"),   # a4, ticket80 o ticket58
        ("formato_factura",     "a4"),   # a4, ticket80 o ticket58
        # Nombre de la impresora elegida para cada documento. Vacío = usar
        # la impresora predeterminada del sistema.
        ("impresora_comprobante", ""),
        ("impresora_factura",     ""),
    ]
    for clave, valor in defaults:
        c.execute(
            "INSERT OR IGNORE INTO config_local (clave, valor) VALUES (?,?)",
            (clave, valor)
        )

    # Numeración inicial para facturas y comprobantes
    for tipo in ("factura", "comprobante"):
        c.execute(
            "INSERT OR IGNORE INTO numeracion_comprobante "
            "(tipo, establecimiento, punto_exp, ultimo_numero) VALUES (?,?,?,0)",
            (tipo, "001", "001")
        )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
#  CONFIG LOCAL
# ─────────────────────────────────────────────────────────────

def obtener_config_local() -> dict:
    inicializar_tablas_comprobante()
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT clave, valor FROM config_local")
    config = dict(c.fetchall())
    conn.close()
    return config


def guardar_config_local(datos: dict):
    """Guarda un dict {clave: valor} en config_local."""
    conn = conectar()
    c = conn.cursor()
    for clave, valor in datos.items():
        c.execute(
            "INSERT INTO config_local (clave, valor) VALUES (?,?) "
            "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
            (clave, str(valor))
        )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
#  NUMERACIÓN
# ─────────────────────────────────────────────────────────────

def obtener_numeracion(tipo: str) -> dict:
    inicializar_tablas_comprobante()
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM numeracion_comprobante WHERE tipo=?", (tipo,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {"tipo": tipo, "establecimiento": "001",
                "punto_exp": "001", "ultimo_numero": 0}
    return {
        "tipo": row[0], "establecimiento": row[1],
        "punto_exp": row[2], "ultimo_numero": row[3]
    }


def guardar_numeracion(tipo: str, establecimiento: str,
                       punto_exp: str, ultimo_numero: int):
    inicializar_tablas_comprobante()
    conn = conectar()
    conn.execute("""
        INSERT INTO numeracion_comprobante
            (tipo, establecimiento, punto_exp, ultimo_numero)
        VALUES (?,?,?,?)
        ON CONFLICT(tipo) DO UPDATE SET
            establecimiento=excluded.establecimiento,
            punto_exp=excluded.punto_exp,
            ultimo_numero=excluded.ultimo_numero
    """, (tipo, establecimiento, punto_exp, ultimo_numero))
    conn.commit()
    conn.close()


def siguiente_numero(tipo: str) -> tuple[str, int]:
    """Incrementa el contador y devuelve (numero_formateado, numero_entero).
    Formato: 001-001-0000001 (establecimiento-punto_exp-numero 7 dígitos)
    """
    conn = conectar()
    c = conn.cursor()
    c.execute(
        "UPDATE numeracion_comprobante SET ultimo_numero = ultimo_numero + 1 "
        "WHERE tipo=?", (tipo,))
    conn.commit()
    c.execute("SELECT establecimiento, punto_exp, ultimo_numero "
              "FROM numeracion_comprobante WHERE tipo=?", (tipo,))
    row = c.fetchone()
    conn.close()
    if not row:
        return "001-001-0000001", 1
    est, pto, num = row
    return f"{est}-{pto}-{num:07d}", num


# ─────────────────────────────────────────────────────────────
#  IVA
# ─────────────────────────────────────────────────────────────

def calcular_iva(subtotal: float, tasa: int, incluye_iva: bool) -> dict:
    """
    Calcula la liquidación del IVA según las leyes paraguayas.
    Si incluye_iva: el precio ya contiene el IVA (precio IVA incluido).
    Devuelve: {base_imponible, iva, total}
    """
    if tasa == 0:
        return {"base_imponible": subtotal, "iva": 0.0, "total": subtotal}
    if incluye_iva:
        # Extraer IVA del precio ya incluido: IVA = Total × tasa / (100 + tasa)
        iva = subtotal * tasa / (100 + tasa)
        base = subtotal - iva
    else:
        base = subtotal
        iva = subtotal * tasa / 100
    total = base + iva
    return {"base_imponible": round(base), "iva": round(iva), "total": round(total)}


# ─────────────────────────────────────────────────────────────
#  COMPROBANTE DE UNA VENTA REAL (para el panel de Resumen y
#  para la reimpresión), con el mismo formato de ticket que se
#  ve en la vista previa de Configuración Local.
# ─────────────────────────────────────────────────────────────

def datos_comprobante(detalle: dict) -> dict:
    """Reúne configuración del local, numeración e IVA para el comprobante
    de una venta ya registrada (dict devuelto por obtener_detalle_venta)."""
    cfg = obtener_config_local()
    # El número real ya quedó fijado al procesar la venta (según la
    # numeración configurada en Config. Local), y viaja en 'detalle' —
    # no se debe recalcular acá con la numeración ACTUAL ni con el ID de
    # la venta, porque eso ignoraría lo que el usuario configuró y haría
    # que el número cambiara cada vez que se reimprime.
    numero = detalle.get("nro_comprobante") or f"001-001-{detalle['id']:07d}"
    tasa = int(cfg.get("tipo_iva", "10") or "10")
    incluye_iva = cfg.get("incluye_iva", "1") == "1"
    iva_d = calcular_iva(detalle["total"], tasa, incluye_iva)
    items = [l for l in detalle["lineas"] if l["cantidad_activa"] > 0]
    return {"cfg": cfg, "numero": numero, "tasa": tasa,
            "incluye_iva": incluye_iva, "iva": iva_d, "items": items}


def partes_comprobante(detalle: dict, ancho: int = 40) -> dict:
    """Devuelve el comprobante partido en 'encabezado' y 'pie' (texto ya
    formateado, listo para mostrar), más la lista de 'items' — para que la
    interfaz pueda intercalar una tabla interactiva (devolución de
    artículos) entre ambos bloques."""
    d = datos_comprobante(detalle)
    cfg = d["cfg"]

    enc = ["=" * ancho]
    nombre = cfg.get("razon_social") or cfg.get("nombre_local") or "Nombre Local"
    enc.append(f"{nombre[:ancho]:^{ancho}}")
    if cfg.get("nombre_local") and cfg.get("razon_social") and cfg["nombre_local"] != cfg["razon_social"]:
        enc.append(f"{cfg['nombre_local'][:ancho]:^{ancho}}")
    if cfg.get("ruc"):
        enc.append(f"{('RUC: ' + cfg['ruc'])[:ancho]:^{ancho}}")
    if cfg.get("direccion"):
        enc.append(f"{cfg['direccion'][:ancho]:^{ancho}}")
    if cfg.get("telefono"):
        enc.append(f"{('Tel: ' + cfg['telefono'])[:ancho]:^{ancho}}")
    enc.append("-" * ancho)
    enc.append(f"{'COMPROBANTE DE VENTA':^{ancho}}")
    enc.append(f"{'** NO VÁLIDO PARA USO LEGAL **':^{ancho}}")
    if cfg.get("timbrado_nro"):
        enc.append(f"Timbrado Nº: {cfg['timbrado_nro']}"[:ancho])
        enc.append((f"Vigencia: {cfg.get('timbrado_vigencia_desde','-')} al "
                    f"{cfg.get('timbrado_vigencia_hasta','-')}")[:ancho])
    enc.append("-" * ancho)
    enc.append(f"Comp. Nº: {d['numero']}"[:ancho])
    enc.append(f"Fecha: {detalle['fecha']}"[:ancho])
    enc.append(f"Cliente: {detalle['cliente_nombre']}"[:ancho])
    enc.append(f"CI/RUC: {detalle['cliente_documento'] or '-'}"[:ancho])
    enc.append(f"CONDICIÓN: [{detalle['condicion'].upper()}]"[:ancho])
    if detalle["estado"] == "Cancelado":
        enc.append(f"{'*** VENTA CANCELADA ***':^{ancho}}")
    enc.append("-" * ancho)

    pie = ["-" * ancho]
    pie.append(f"{'TOTAL':<{max(ancho-14, 5)}}{formatear_gs(detalle['total']):>14}")
    pie.append(f"Pago Con: {detalle['forma_pago']}"[:ancho])
    pie.append("-" * ancho)
    pie.append(f"Liquidación IVA ({d['tasa']}%)"[:ancho])
    pie.append(f"Base imponible: {formatear_gs(d['iva']['base_imponible'])}"[:ancho])
    pie.append(f"IVA ({d['tasa']}%): {formatear_gs(d['iva']['iva'])}"[:ancho])
    pie.append("-" * ancho)
    if cfg.get("mensaje_pie"):
        pie.append(f"{cfg['mensaje_pie'][:ancho]:^{ancho}}")
    pie.append("=" * ancho)

    return {"encabezado": "\n".join(enc), "pie": "\n".join(pie),
            "items": d["items"], "numero": d["numero"]}


def generar_texto_comprobante(detalle: dict, ancho: int = 40) -> str:
    """Texto plano completo del comprobante (formato ticket), listo para
    imprimir o guardar en un .txt. Usa el mismo contenido que se muestra
    en el panel de Resumen de Ventas."""
    partes = partes_comprobante(detalle, ancho)
    ancho_desc = max(ancho - 5 - 14, 8)
    L = [partes["encabezado"], f"{'CANT':<5}{'DESCRIPCIÓN'[:ancho_desc]:<{ancho_desc}}{'IMPORTE':>14}"]
    for l in partes["items"]:
        cant = f"{l['cantidad_activa']:g}"
        desc = l["nombre_producto"][:ancho_desc]
        imp = formatear_gs(l["importe"])
        L.append(f"{cant:<5}{desc:<{ancho_desc}}{imp:>14}")
    if not partes["items"]:
        L.append("(Todos los artículos fueron devueltos)")
    L.append(partes["pie"])
    return "\n".join(L)


def generar_pdf_comprobante(ruta: str, detalle: dict, formato: str = "a4") -> str:
    """Genera el comprobante de venta (ticket, no válido para uso legal) en
    PDF, en el tamaño de papel elegido:
      - 'a4'      → hoja A4 completa
      - 'ticket80'/'ticket58' → rollo de impresora ticketera, con el alto
        del PDF calculado según la cantidad de líneas (papel continuo).
    Devuelve la ruta del archivo generado."""
    if not PDF_OK:
        raise RuntimeError("reportlab no está instalado (pip install reportlab)")

    spec = FORMATOS_IMPRESION.get(formato, FORMATOS_IMPRESION["a4"])
    texto = generar_texto_comprobante(detalle, ancho=spec["ancho_txt"])
    lineas = texto.split("\n")
    interlineado = spec["fuente"] * 1.35

    if formato == "a4":
        ancho_pt, alto_pt = A4
        margen = 20 * mm
    else:
        ancho_pt = spec["ancho_mm"] * mm
        margen = spec["margen_mm"] * mm
        alto_pt = margen * 2 + len(lineas) * interlineado

    c = rl_canvas.Canvas(ruta, pagesize=(ancho_pt, alto_pt))
    c.setFont("Courier", spec["fuente"])
    x = margen
    y = alto_pt - margen
    for linea in lineas:
        c.drawString(x, y, linea)
        y -= interlineado
        if formato == "a4" and y < margen:
            c.showPage()
            c.setFont("Courier", spec["fuente"])
            y = alto_pt - margen
    c.save()
    return ruta


def generar_comprobante_desde_venta(venta_id: int, formato: str = None) -> str:
    """Genera el Comprobante de Venta (no válido para uso legal) en PDF
    para una venta ya registrada, y devuelve la ruta del archivo. Si no
    se indica 'formato', usa el tamaño de papel configurado en
    Configuración Local (pestaña 'Comprobante de Venta'). Análoga a
    generar_factura_desde_venta(), pero para el comprobante simple."""
    import os, tempfile
    from models_ventas import obtener_detalle_venta

    detalle = obtener_detalle_venta(venta_id)
    if detalle is None:
        raise ValueError(f"No se encontró la venta #{venta_id}")

    cfg = obtener_config_local()
    if formato is None:
        formato = cfg.get("formato_comprobante", "a4") or "a4"

    numero = datos_comprobante(detalle)["numero"]
    ruta = os.path.join(tempfile.gettempdir(), f"comprobante_{numero.replace('-', '_')}.pdf")
    generar_pdf_comprobante(ruta, detalle, formato=formato)
    return ruta
