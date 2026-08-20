"""
documento_presupuesto_pdf.py
Genera el documento de Presupuesto en PDF para entregar al cliente: datos
del local (si están configurados), datos del cliente, listado de
artículos cotizados, total, y validez de la oferta.

Requiere la librería 'reportlab' (pip install reportlab).
"""
import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

AZUL_RIBBON = colors.HexColor("#1d5fd6")
GRIS_TEXTO = colors.HexColor("#555555")


def _formato_gs(monto: float) -> str:
    return f"Gs. {monto:,.0f}"


def _fecha_legible(fecha_iso: str) -> str:
    if not fecha_iso:
        return "—"
    try:
        return datetime.date.fromisoformat(fecha_iso[:10]).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return fecha_iso


def _datos_local() -> dict:
    """Lee la configuración del local (nombre, RUC, dirección, teléfono)
    para el encabezado; si no está configurada, deja campos vacíos."""
    try:
        from models_comprobante import obtener_config_local
        cfg = obtener_config_local()
        return {
            "nombre": cfg.get("razon_social") or cfg.get("nombre_local") or "",
            "ruc": cfg.get("ruc", "") or "",
            "direccion": cfg.get("direccion", "") or "",
            "telefono": cfg.get("telefono", "") or "",
        }
    except Exception:
        return {"nombre": "", "ruc": "", "direccion": "", "telefono": ""}


def generar_documento_presupuesto_pdf(ruta_destino: str, presupuesto: dict) -> str:
    """presupuesto: el dict devuelto por models_presupuestos.obtener_presupuesto()."""
    local = _datos_local()

    doc = SimpleDocTemplate(
        ruta_destino, pagesize=A4,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    )
    estilos = getSampleStyleSheet()
    estilo_nombre_local = ParagraphStyle("NombreLocal", parent=estilos["Title"], fontSize=16,
                                        textColor=AZUL_RIBBON, spaceAfter=2)
    estilo_datos_local = ParagraphStyle("DatosLocal", parent=estilos["Normal"], fontSize=8,
                                        textColor=GRIS_TEXTO)
    estilo_titulo_doc = ParagraphStyle("TituloDoc", parent=estilos["Heading1"], fontSize=20,
                                       alignment=TA_RIGHT, textColor=colors.HexColor("#1e293b"))
    estilo_num_doc = ParagraphStyle("NumDoc", parent=estilos["Normal"], fontSize=10,
                                    alignment=TA_RIGHT, textColor=GRIS_TEXTO)
    estilo_seccion = ParagraphStyle("Seccion", parent=estilos["Heading3"], fontSize=10,
                                    textColor=AZUL_RIBBON, spaceBefore=8, spaceAfter=4)
    estilo_normal = estilos["Normal"]
    estilo_footer = ParagraphStyle("Footer", parent=estilos["Normal"], fontSize=8,
                                   textColor=GRIS_TEXTO, alignment=TA_CENTER)

    elementos = []

    # --- Encabezado: datos del local a la izquierda, "PRESUPUESTO" a la derecha ---
    encabezado = Table([[
        Paragraph(local["nombre"] or "Nombre del Local", estilo_nombre_local),
        Paragraph("PRESUPUESTO", estilo_titulo_doc),
    ]], colWidths=[10 * cm, 7 * cm])
    encabezado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(encabezado)

    datos_local_txt = f"RUC: {local['ruc']}   Tel: {local['telefono']}<br/>{local['direccion']}"
    fila2 = Table([[
        Paragraph(datos_local_txt, estilo_datos_local),
        Paragraph(f"N° {presupuesto['id']}<br/>Fecha: {_fecha_legible(presupuesto['fecha'])}",
                 estilo_num_doc),
    ]], colWidths=[10 * cm, 7 * cm])
    fila2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(fila2)
    elementos.append(Spacer(1, 4))
    elementos.append(Table([[""]], colWidths=[17 * cm], rowHeights=[1],
                           style=[("LINEBELOW", (0, 0), (-1, -1), 1, AZUL_RIBBON)]))
    elementos.append(Spacer(1, 14))

    # --- Datos del cliente ---
    elementos.append(Paragraph("PRESUPUESTO PARA:", estilo_seccion))
    elementos.append(Paragraph(f"<b>{presupuesto['cliente_nombre']}</b>", estilo_normal))
    if presupuesto["cliente_documento"]:
        elementos.append(Paragraph(f"CI/RUC: {presupuesto['cliente_documento']}", estilo_normal))
    if presupuesto["cliente_direccion"]:
        elementos.append(Paragraph(f"Dirección: {presupuesto['cliente_direccion']}", estilo_normal))
    if presupuesto["cliente_telefono"]:
        elementos.append(Paragraph(f"Teléfono: {presupuesto['cliente_telefono']}", estilo_normal))
    elementos.append(Spacer(1, 14))

    # --- Tabla de artículos ---
    encabezado_tabla = ["Cant.", "Descripción", "Precio Unit.", "Importe"]
    filas = [encabezado_tabla]
    for item in presupuesto["items"]:
        cantidad_txt = f"{item['cantidad']:g}"
        filas.append([cantidad_txt, item["nombre"], _formato_gs(item["precio_unitario"]),
                     _formato_gs(item["importe"])])
    tabla = Table(filas, colWidths=[2 * cm, 8.5 * cm, 3.25 * cm, 3.25 * cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 10))

    # --- Total ---
    tabla_total = Table([["TOTAL", _formato_gs(presupuesto["total"])]], colWidths=[13.75 * cm, 3.25 * cm])
    tabla_total.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TEXTCOLOR", (0, 0), (-1, -1), AZUL_RIBBON),
        ("LINEABOVE", (0, 0), (-1, 0), 1, AZUL_RIBBON),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    elementos.append(tabla_total)
    elementos.append(Spacer(1, 16))

    if presupuesto.get("observaciones"):
        elementos.append(Paragraph("Observaciones:", estilo_seccion))
        elementos.append(Paragraph(presupuesto["observaciones"], estilo_normal))
        elementos.append(Spacer(1, 10))

    elementos.append(Paragraph(
        f"Este presupuesto tiene validez hasta el <b>{_fecha_legible(presupuesto['fecha_validez'])}</b>.",
        estilo_normal,
    ))
    elementos.append(Spacer(1, 24))
    elementos.append(Paragraph("Documento sin validez fiscal — no constituye una factura.",
                               estilo_footer))

    doc.build(elementos)
    return ruta_destino
