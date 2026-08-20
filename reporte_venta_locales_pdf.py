"""
reporte_venta_locales_pdf.py
Genera el PDF del pedido armado "por Locales": una sección por cada local
con su propia lista de productos y subtotal, y al final un Resumen
Consolidado con las cantidades totales por producto (sumando los
repetidos entre locales) — el mismo cálculo que se usa al cargar el
pedido en la venta actual.

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
VERDE = colors.HexColor("#16a34a")


def _formato_gs(monto) -> str:
    try:
        return f"Gs. {float(monto):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "Gs. 0"


def _datos_local_negocio() -> dict:
    """Datos del propio negocio (el que arma el pedido) para el membrete,
    igual que en Presupuestos y los reportes de Veterinaria."""
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


def generar_pdf_venta_por_locales(ruta_destino: str, locales: list[dict], generado_por: str = "") -> str:
    """locales: lista de dicts {"nombre": str, "items": [item, ...]} donde
    cada item tiene la misma forma que en la venta: {"producto": {...},
    "cantidad": float, "precio_unitario": float}."""
    negocio = _datos_local_negocio()

    doc = SimpleDocTemplate(
        ruta_destino, pagesize=A4,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
    )
    estilos = getSampleStyleSheet()
    estilo_nombre_local = ParagraphStyle("NombreNegocio", parent=estilos["Title"], fontSize=15,
                                        textColor=AZUL_RIBBON, spaceAfter=2)
    estilo_datos_local = ParagraphStyle("DatosNegocio", parent=estilos["Normal"], fontSize=8,
                                        textColor=GRIS_TEXTO)
    estilo_titulo_doc = ParagraphStyle("TituloDoc", parent=estilos["Heading1"], fontSize=17,
                                       alignment=TA_RIGHT, textColor=colors.HexColor("#1e293b"))
    estilo_num_doc = ParagraphStyle("NumDoc", parent=estilos["Normal"], fontSize=9,
                                    alignment=TA_RIGHT, textColor=GRIS_TEXTO)
    estilo_seccion = ParagraphStyle("SeccionLocal", parent=estilos["Heading2"], fontSize=12,
                                    textColor=colors.white, backColor=AZUL_RIBBON, spaceBefore=10,
                                    spaceAfter=6, leftIndent=4, borderPadding=4)
    estilo_normal = estilos["Normal"]
    estilo_footer = ParagraphStyle("Footer", parent=estilos["Normal"], fontSize=8,
                                   textColor=GRIS_TEXTO, alignment=TA_CENTER)

    elementos = []

    encabezado = Table([[
        Paragraph(negocio["nombre"] or "Nombre del Local", estilo_nombre_local),
        Paragraph("PEDIDO POR<br/>LOCALES", estilo_titulo_doc),
    ]], colWidths=[10 * cm, 7 * cm])
    encabezado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(encabezado)

    datos_negocio_txt = f"RUC: {negocio['ruc']}   Tel: {negocio['telefono']}<br/>{negocio['direccion']}"
    info_extra = f"Emitido: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
    if generado_por:
        info_extra += f"<br/>Generado por: {generado_por}"
    fila2 = Table([[
        Paragraph(datos_negocio_txt, estilo_datos_local),
        Paragraph(info_extra, estilo_num_doc),
    ]], colWidths=[10 * cm, 7 * cm])
    fila2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(fila2)
    elementos.append(Spacer(1, 4))
    elementos.append(Table([[""]], colWidths=[17 * cm], rowHeights=[1],
                           style=[("LINEBELOW", (0, 0), (-1, -1), 1, AZUL_RIBBON)]))
    elementos.append(Spacer(1, 14))

    total_general = 0
    consolidado: dict = {}  # clave -> {"nombre":, "cantidad":, "precio_unitario":, "importe":}

    for local in locales:
        nombre_local = local["nombre"]
        items = local["items"]
        subtotal_local = sum(it["cantidad"] * it["precio_unitario"] for it in items)
        total_general += subtotal_local

        elementos.append(Paragraph(f"LOCAL: {nombre_local}", estilo_seccion))
        if items:
            encabezado_tabla = ["Código", "Descripción", "Cant.", "Precio Unit.", "Importe"]
            filas = [encabezado_tabla]
            for it in items:
                p = it["producto"]
                importe = it["cantidad"] * it["precio_unitario"]
                descripcion = f"{p['nombre']} (Mayoreo)" if it.get("es_mayoreo") else p["nombre"]
                filas.append([
                    str(p.get("id", "—")), descripcion, f"{it['cantidad']:g}",
                    _formato_gs(it["precio_unitario"]), _formato_gs(importe),
                ])
                clave = p.get("id") if p.get("id") is not None else f"libre:{p['nombre']}"
                if clave not in consolidado:
                    consolidado[clave] = {"nombre": p["nombre"], "cantidad": 0,
                                          "precio_unitario": it["precio_unitario"], "importe": 0}
                consolidado[clave]["cantidad"] += it["cantidad"]
                consolidado[clave]["importe"] += importe
            filas.append(["", "", "", "SUBTOTAL", _formato_gs(subtotal_local)])
            tabla = Table(filas, colWidths=[2*cm, 7.5*cm, 1.8*cm, 2.7*cm, 3*cm], repeatRows=1)
            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f5f7")]),
                ("GRID", (0, 0), (-1, -2), 0.4, colors.HexColor("#dddddd")),
                ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("LINEABOVE", (0, -1), (-1, -1), 1, AZUL_RIBBON),
                ("TEXTCOLOR", (-1, -1), (-1, -1), AZUL_RIBBON),
            ]))
            elementos.append(tabla)
        else:
            elementos.append(Paragraph("Este local no tiene productos cargados.", estilo_normal))
        elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("RESUMEN CONSOLIDADO (cantidades sumadas entre todos los locales)",
                               estilo_seccion))
    if consolidado:
        encabezado_tabla = ["Descripción", "Cant. Total", "Precio Unit.", "Importe"]
        filas = [encabezado_tabla]
        for datos in sorted(consolidado.values(), key=lambda d: d["nombre"]):
            filas.append([
                datos["nombre"], f"{datos['cantidad']:g}",
                _formato_gs(datos["precio_unitario"]), _formato_gs(datos["importe"]),
            ])
        filas.append(["", "", "TOTAL GENERAL", _formato_gs(total_general)])
        tabla_consolidado = Table(filas, colWidths=[8.5*cm, 2.7*cm, 2.9*cm, 2.9*cm], repeatRows=1)
        tabla_consolidado.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -2), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 11),
            ("LINEABOVE", (0, -1), (-1, -1), 1.2, AZUL_RIBBON),
            ("TEXTCOLOR", (-1, -1), (-1, -1), VERDE),
            ("TOPPADDING", (0, -1), (-1, -1), 8),
        ]))
        elementos.append(tabla_consolidado)
    else:
        elementos.append(Paragraph("No hay productos cargados en ningún local todavía.", estilo_normal))

    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("Documento informativo — no constituye una factura ni un comprobante fiscal.",
                               estilo_footer))

    doc.build(elementos)
    return ruta_destino
