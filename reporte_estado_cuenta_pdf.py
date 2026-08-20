"""
reporte_estado_cuenta_pdf.py
Genera el Estado de Cuenta de un cliente en PDF: datos del cliente,
listado de todos sus créditos con fechas, montos y saldo, y el total
general adeudado. Usado desde el módulo Créditos → Estado de Cuenta.

Requiere la librería 'reportlab' (pip install reportlab).
"""
import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

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


def generar_estado_cuenta_pdf(ruta_destino: str, estado: dict) -> str:
    """estado: el dict devuelto por models_creditos.estado_cuenta_cliente()."""
    doc = SimpleDocTemplate(
        ruta_destino, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("Titulo", parent=estilos["Title"], fontSize=17, textColor=AZUL_RIBBON)
    estilo_subtitulo = ParagraphStyle("Subtitulo", parent=estilos["Normal"], fontSize=10,
                                      textColor=GRIS_TEXTO, alignment=TA_CENTER)
    estilo_seccion = ParagraphStyle("Seccion", parent=estilos["Heading2"], fontSize=12,
                                    textColor=colors.white, backColor=AZUL_RIBBON, spaceBefore=10,
                                    spaceAfter=6, leftIndent=4, borderPadding=4)
    estilo_normal = estilos["Normal"]

    elementos = [
        Paragraph("Estado de Cuenta", estilo_titulo),
        Paragraph(estado["nombre"], estilo_subtitulo),
    ]
    datos_cliente = (
        f"CI/RUC: {estado['nro_documento'] or '—'}   "
        f"Dirección: {estado['direccion'] or '—'}   "
        f"Teléfono: {estado['telefono'] or '—'}"
    )
    elementos.append(Paragraph(datos_cliente, estilo_subtitulo))
    elementos.append(Paragraph(f"Generado el {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
                               estilo_subtitulo))
    elementos.append(Spacer(1, 14))

    elementos.append(Paragraph("RESUMEN GENERAL", estilo_seccion))
    datos_resumen = [
        ["Cantidad de Créditos", str(len(estado["creditos"]))],
        ["Deuda Total", _formato_gs(estado["deuda_total"])],
        ["Pagado", _formato_gs(estado["pagado"])],
        ["Saldo Pendiente", _formato_gs(estado["saldo"])],
    ]
    tabla_resumen = Table(datos_resumen, colWidths=[8 * cm, 8 * cm])
    tabla_resumen.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#dddddd")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TEXTCOLOR", (1, 3), (1, 3), colors.HexColor("#dc2626") if estado["saldo"] > 0.009
         else colors.HexColor("#16a34a")),
    ]))
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("DETALLE DE CRÉDITOS", estilo_seccion))
    if estado["creditos"]:
        encabezado = ["N°", "Fecha", "Vencim.", "Descripción", "Factura", "Deuda", "Pagado", "Saldo"]
        filas = [encabezado]
        for c in estado["creditos"]:
            filas.append([
                str(c["id"]), _fecha_legible(c["fecha"]), _fecha_legible(c["fecha_vencimiento"]),
                (c["descripcion"] or "—")[:22], c["nro_factura"] or "—",
                _formato_gs(c["deuda_total"]), _formato_gs(c["pagado"]), _formato_gs(c["saldo"]),
            ])
        tabla = Table(filas, colWidths=[1*cm, 2.2*cm, 2.2*cm, 4.3*cm, 2.6*cm, 2.3*cm, 2.3*cm, 2.3*cm],
                     repeatRows=1)
        estilo_tabla = [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("ALIGN", (5, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        for i, c in enumerate(estado["creditos"], start=1):
            if c["saldo"] <= 0.009:
                estilo_tabla.append(("TEXTCOLOR", (0, i), (-1, i), colors.HexColor("#9ca3af")))
        tabla.setStyle(TableStyle(estilo_tabla))
        elementos.append(tabla)
    else:
        elementos.append(Paragraph("Este cliente no tiene créditos registrados.", estilo_normal))

    doc.build(elementos)
    return ruta_destino
