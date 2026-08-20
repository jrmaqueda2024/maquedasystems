"""
reporte_prestamo_pdf.py
Genera el Extracto completo de un Préstamo en PDF: datos del préstamo y
del cliente, cronograma completo de cuotas (pagadas, pendientes y
vencidas), historial de todos los pagos realizados, y el resumen total
de lo abonado hasta el momento y del saldo pendiente.
Usado desde el módulo Préstamos → Detalle del Préstamo.

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
VERDE = colors.HexColor("#16a34a")
ROJO = colors.HexColor("#dc2626")
NARANJA = colors.HexColor("#d97706")

NOMBRES_SISTEMA = {"frances": "Sistema Francés (cuota fija)", "aleman": "Sistema Alemán (capital fijo)"}
NOMBRES_FRECUENCIA = {"diaria": "Diaria", "semanal": "Semanal", "quincenal": "Quincenal", "mensual": "Mensual"}


def _formato_gs(monto: float) -> str:
    return f"Gs. {monto:,.0f}".replace(",", ".")


def _fecha_legible(fecha) -> str:
    if not fecha:
        return "—"
    if isinstance(fecha, str):
        try:
            fecha = datetime.date.fromisoformat(fecha[:10])
        except (ValueError, TypeError):
            return fecha
    return fecha.strftime("%d/%m/%Y")


def generar_extracto_prestamo_pdf(ruta_destino: str, detalle: dict) -> str:
    """detalle: el dict devuelto por models_prestamos.obtener_detalle_prestamo()."""
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

    total_abonado = sum(p["total"] for p in detalle["pagos"])
    cuotas_pagadas = sum(1 for c in detalle["cuotas"] if c["estado"] == "Pagada")
    cuotas_pendientes = detalle["cantidad_cuotas"] - cuotas_pagadas

    elementos = [
        Paragraph("Extracto de Préstamo", estilo_titulo),
        Paragraph(f"Préstamo Nro. {detalle['id']}  —  {detalle['cliente']}", estilo_subtitulo),
        Paragraph(NOMBRES_SISTEMA.get(detalle["sistema"], detalle["sistema"]), estilo_subtitulo),
        Paragraph(f"Generado el {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_subtitulo),
    ]
    elementos.append(Spacer(1, 14))

    elementos.append(Paragraph("DATOS DEL PRÉSTAMO", estilo_seccion))
    datos_prestamo = [
        ["Cliente", detalle["cliente"]],
        ["CI/RUC", detalle["nro_documento"] or "—"],
        ["Teléfono", detalle["telefono"] or "—"],
        ["Capital Prestado", _formato_gs(detalle["capital"])],
        ["Tasa de Interés", f"{detalle['tasa_interes']}% {NOMBRES_FRECUENCIA.get(detalle['frecuencia'], '')}"],
        ["Mora Diaria", f"{detalle['tasa_mora_diaria']}%"],
        ["Fecha de Desembolso", _fecha_legible(detalle["fecha_desembolso"])],
        ["Cantidad de Cuotas", str(detalle["cantidad_cuotas"])],
        ["Estado", detalle["estado"].capitalize()],
    ]
    tabla_datos = Table(datos_prestamo, colWidths=[6 * cm, 10 * cm])
    tabla_datos.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#dddddd")),
    ]))
    elementos.append(tabla_datos)
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("RESUMEN GENERAL", estilo_seccion))
    datos_resumen = [
        ["Cuotas Pagadas", f"{cuotas_pagadas} de {detalle['cantidad_cuotas']}"],
        ["Cuotas Restantes", str(cuotas_pendientes)],
        ["Total Abonado hasta el Momento", _formato_gs(total_abonado)],
        ["Saldo Pendiente", _formato_gs(detalle["saldo_total"])],
    ]
    tabla_resumen = Table(datos_resumen, colWidths=[8 * cm, 8 * cm])
    tabla_resumen.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#dddddd")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TEXTCOLOR", (1, 2), (1, 2), VERDE),
        ("TEXTCOLOR", (1, 3), (1, 3), ROJO if detalle["saldo_total"] > 0.009 else VERDE),
    ]))
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("CRONOGRAMA DE CUOTAS", estilo_seccion))
    if detalle["cuotas"]:
        encabezado = ["Cuota", "Vencim.", "Capital", "Interés", "Mora", "Total a Pagar", "Estado"]
        filas = [encabezado]
        for c in detalle["cuotas"]:
            filas.append([
                str(c["nro_cuota"]), _fecha_legible(c["fecha_venc"]),
                _formato_gs(c["capital"]), _formato_gs(c["interes"]),
                _formato_gs(c["mora_pendiente"]), _formato_gs(c["total_a_pagar"]), c["estado"],
            ])
        tabla = Table(filas, colWidths=[1.6*cm, 2.4*cm, 2.6*cm, 2.6*cm, 2.2*cm, 3*cm, 2.4*cm],
                     repeatRows=1)
        estilo_tabla = [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        color_por_estado = {"Vencida": ROJO, "Pagada": VERDE, "Pendiente": NARANJA}
        for i, c in enumerate(detalle["cuotas"], start=1):
            color = color_por_estado.get(c["estado"])
            if color:
                estilo_tabla.append(("TEXTCOLOR", (6, i), (6, i), color))
                estilo_tabla.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))
        tabla.setStyle(TableStyle(estilo_tabla))
        elementos.append(tabla)
    else:
        elementos.append(Paragraph("Este préstamo no tiene cuotas registradas.", estilo_normal))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("HISTORIAL DE PAGOS", estilo_seccion))
    if detalle["pagos"]:
        encabezado = ["Fecha", "Capital", "Interés", "Mora", "Total Pagado"]
        filas = [encabezado]
        for p in detalle["pagos"]:
            filas.append([
                _fecha_legible(p["fecha"]), _formato_gs(p["capital"]),
                _formato_gs(p["interes"]), _formato_gs(p["mora"]), _formato_gs(p["total"]),
            ])
        filas.append(["TOTAL ABONADO", "", "", "", _formato_gs(total_abonado)])
        tabla_pagos = Table(filas, colWidths=[3*cm, 3.2*cm, 3.2*cm, 3.2*cm, 3.4*cm], repeatRows=1)
        tabla_pagos.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -2), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE", (0, -1), (-1, -1), 1, AZUL_RIBBON),
            ("TEXTCOLOR", (-1, -1), (-1, -1), VERDE),
            ("TOPPADDING", (0, -1), (-1, -1), 6),
        ]))
        elementos.append(tabla_pagos)
    else:
        elementos.append(Paragraph("Todavía no se registraron pagos para este préstamo.", estilo_normal))

    doc.build(elementos)
    return ruta_destino
