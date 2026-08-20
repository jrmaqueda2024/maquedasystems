"""
reporte_presupuestos_pdf.py
Genera el Reporte de Presupuestos en PDF para un rango de fechas: resumen
general (incluida la tasa de conversión a venta), gráfico de barras de
presupuestos por día, ranking de productos más cotizados, y el detalle
completo del período. Mismo estilo visual que reporte_compras_pdf.py.
"""
import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart

from models_presupuestos import (
    resumen_presupuestos_en_rango, presupuestos_por_dia_en_rango,
    productos_mas_presupuestados_en_rango,
)

AZUL_RIBBON = colors.HexColor("#1d5fd6")
GRIS_TEXTO = colors.HexColor("#555555")


def _formato_gs(monto: float) -> str:
    return f"Gs. {monto:,.0f}"


def _fecha_legible(fecha_iso: str) -> str:
    try:
        return datetime.date.fromisoformat(fecha_iso[:10]).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return fecha_iso or ""


def _construir_grafico(datos_dias: list[dict]) -> Drawing:
    ancho_dibujo, alto_dibujo = 480, 200
    drawing = Drawing(ancho_dibujo, alto_dibujo)
    valores = [d["total"] for d in datos_dias] or [0]
    etiquetas = [_fecha_legible(d["fecha"])[:5] for d in datos_dias] or [""]

    grafico = VerticalBarChart()
    grafico.x = 45
    grafico.y = 30
    grafico.width = ancho_dibujo - 65
    grafico.height = alto_dibujo - 50
    grafico.data = [valores]
    grafico.categoryAxis.categoryNames = etiquetas
    grafico.categoryAxis.labels.fontSize = 7
    grafico.valueAxis.valueMin = 0
    grafico.valueAxis.labels.fontSize = 7
    grafico.bars[0].fillColor = AZUL_RIBBON
    grafico.barSpacing = 4
    drawing.add(grafico)
    return drawing


def generar_reporte_presupuestos_pdf(ruta_destino: str, fecha_desde: str, fecha_hasta: str,
                                      generado_por: str = "") -> str:
    resumen = resumen_presupuestos_en_rango(fecha_desde, fecha_hasta)
    dias = presupuestos_por_dia_en_rango(fecha_desde, fecha_hasta)
    top_productos = productos_mas_presupuestados_en_rango(fecha_desde, fecha_hasta, limite=10)

    doc = SimpleDocTemplate(
        ruta_destino, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("Titulo", parent=estilos["Title"], fontSize=18, textColor=AZUL_RIBBON)
    estilo_subtitulo = ParagraphStyle("Subtitulo", parent=estilos["Normal"], fontSize=10,
                                      textColor=GRIS_TEXTO, alignment=TA_CENTER)
    estilo_seccion = ParagraphStyle("Seccion", parent=estilos["Heading2"], fontSize=12,
                                    textColor=colors.white, backColor=AZUL_RIBBON, spaceBefore=10,
                                    spaceAfter=6, leftIndent=4, borderPadding=4)
    estilo_normal = estilos["Normal"]

    elementos = [
        Paragraph("Reporte de Presupuestos", estilo_titulo),
        Paragraph(f"Período: {_fecha_legible(fecha_desde)} al {_fecha_legible(fecha_hasta)}",
                 estilo_subtitulo),
    ]
    pie_gen = f"Generado el {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
    if generado_por:
        pie_gen += f" por {generado_por}"
    elementos.append(Paragraph(pie_gen, estilo_subtitulo))
    elementos.append(Spacer(1, 14))

    elementos.append(Paragraph("RESUMEN GENERAL", estilo_seccion))
    datos_resumen = [
        ["Cantidad de Presupuestos", str(resumen["cantidad"])],
        ["Total Cotizado", _formato_gs(resumen["total_cotizado"])],
        ["Aprobados/Convertidos", str(resumen["cantidad_aprobados"])],
        ["Convertidos en Venta", str(resumen["cantidad_convertidos"])],
        ["Total Convertido en Venta", _formato_gs(resumen["total_convertido"])],
        ["Tasa de Conversión", f"{resumen['tasa_conversion']}%"],
    ]
    tabla_resumen = Table(datos_resumen, colWidths=[8 * cm, 8 * cm])
    tabla_resumen.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#dddddd")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("PRESUPUESTOS POR DÍA", estilo_seccion))
    if dias:
        elementos.append(_construir_grafico(dias))
    else:
        elementos.append(Paragraph("No hay presupuestos registrados en este período.", estilo_normal))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("PRODUCTOS MÁS COTIZADOS", estilo_seccion))
    if top_productos:
        filas_top = [["#", "Producto", "Cantidad", "Importe"]] + [
            [str(i + 1), p["nombre"], f"{p['cantidad']:g}", _formato_gs(p["importe"])]
            for i, p in enumerate(top_productos)
        ]
        tabla_top = Table(filas_top, colWidths=[1*cm, 8*cm, 3*cm, 4*cm])
        tabla_top.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"), ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tabla_top)
    else:
        elementos.append(Paragraph("No hay productos cotizados en este período.", estilo_normal))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("DETALLE DE PRESUPUESTOS DEL PERÍODO", estilo_seccion))
    if resumen["presupuestos"]:
        filas_det = [["Código", "Fecha", "Cliente", "Estado", "Total"]]
        for p in resumen["presupuestos"]:
            filas_det.append([
                str(p["id"]), _fecha_legible(p["fecha"]), p["cliente"][:26],
                p["estado_efectivo"], _formato_gs(p["total"]),
            ])
        tabla_det = Table(filas_det, colWidths=[2*cm, 3*cm, 6.5*cm, 3*cm, 3.5*cm], repeatRows=1)
        tabla_det.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (4, 0), (4, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elementos.append(tabla_det)
    else:
        elementos.append(Paragraph("No hay presupuestos registrados en este período.", estilo_normal))

    doc.build(elementos)
    return ruta_destino
