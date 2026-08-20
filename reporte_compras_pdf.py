"""
reporte_compras_pdf.py
Genera el Reporte de Compras en PDF para un rango de fechas: resumen
general, gráfico de barras de compras por día, ranking de proveedores,
ranking de productos más comprados, y la lista completa de compras del
período. Mismo estilo visual que reporte_pdf.py (Ventas).

Requiere la librería 'reportlab' (pip install reportlab).
"""
import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart

from models_compras import (
    resumen_compras_en_rango, compras_por_dia_en_rango,
    productos_mas_comprados_en_rango, proveedores_en_rango,
)

AZUL_RIBBON = colors.HexColor("#1d5fd6")
GRIS_TEXTO = colors.HexColor("#555555")


def _formato_gs(monto: float) -> str:
    return f"Gs. {monto:,.0f}"


def _fecha_legible(fecha_iso: str) -> str:
    """Convierte 'YYYY-MM-DD' a 'DD/MM/YYYY'."""
    try:
        return datetime.date.fromisoformat(fecha_iso[:10]).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return fecha_iso or ""


def _fecha_hora_legible(fecha_hora: str) -> str:
    try:
        return datetime.datetime.fromisoformat(fecha_hora).strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return fecha_hora or ""


def _construir_grafico_compras_por_dia(datos_dias: list[dict]) -> Drawing:
    """Gráfico de barras verticales con el total comprado cada día del
    rango, usando reportlab.graphics (no necesita matplotlib)."""
    ancho_dibujo, alto_dibujo = 480, 200
    drawing = Drawing(ancho_dibujo, alto_dibujo)

    valores = [d["total"] for d in datos_dias] or [0]
    etiquetas = [_fecha_legible(d["fecha"])[:5] for d in datos_dias] or [""]  # "DD/MM"

    grafico = VerticalBarChart()
    grafico.x = 45
    grafico.y = 30
    grafico.width = ancho_dibujo - 65
    grafico.height = alto_dibujo - 50
    grafico.data = [valores]
    grafico.categoryAxis.categoryNames = etiquetas
    grafico.categoryAxis.labels.fontSize = 7
    grafico.categoryAxis.labels.angle = 0
    grafico.valueAxis.valueMin = 0
    grafico.valueAxis.labels.fontSize = 7
    grafico.bars[0].fillColor = AZUL_RIBBON
    grafico.barSpacing = 4

    drawing.add(grafico)
    return drawing


def generar_reporte_compras_pdf(ruta_destino: str, fecha_desde: str, fecha_hasta: str,
                                 generado_por: str = "") -> str:
    """Genera el PDF en ruta_destino. fecha_desde y fecha_hasta en formato
    'YYYY-MM-DD'. Devuelve la ruta del archivo generado."""

    resumen = resumen_compras_en_rango(fecha_desde, fecha_hasta)
    compras_dias = compras_por_dia_en_rango(fecha_desde, fecha_hasta)
    top_productos = productos_mas_comprados_en_rango(fecha_desde, fecha_hasta, limite=10)
    proveedores = proveedores_en_rango(fecha_desde, fecha_hasta)

    doc = SimpleDocTemplate(
        ruta_destino, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloReporte", parent=estilos["Title"], fontSize=18, textColor=AZUL_RIBBON, spaceAfter=4,
    )
    estilo_subtitulo = ParagraphStyle(
        "SubtituloReporte", parent=estilos["Normal"], fontSize=10, textColor=GRIS_TEXTO, alignment=TA_CENTER,
    )
    estilo_seccion = ParagraphStyle(
        "Seccion", parent=estilos["Heading2"], fontSize=12, textColor=colors.white,
        backColor=AZUL_RIBBON, spaceBefore=10, spaceAfter=6, leftIndent=4, borderPadding=4,
    )
    estilo_normal = estilos["Normal"]

    elementos = []

    # --- Encabezado ---
    elementos.append(Paragraph("Reporte de Compras", estilo_titulo))
    periodo_texto = f"Período: {_fecha_legible(fecha_desde)} al {_fecha_legible(fecha_hasta)}"
    elementos.append(Paragraph(periodo_texto, estilo_subtitulo))
    pie_generacion = f"Generado el {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
    if generado_por:
        pie_generacion += f" por {generado_por}"
    elementos.append(Paragraph(pie_generacion, estilo_subtitulo))
    elementos.append(Spacer(1, 14))

    # --- Resumen general ---
    elementos.append(Paragraph("RESUMEN GENERAL", estilo_seccion))
    datos_resumen = [
        ["Cantidad de Compras", str(resumen["cantidad"])],
        ["Total Comprado", _formato_gs(resumen["total"])],
        ["Promedio por Compra", _formato_gs(resumen["promedio"])],
        ["Proveedores Distintos", str(resumen["proveedores_distintos"])],
    ]
    tabla_resumen = Table(datos_resumen, colWidths=[8 * cm, 8 * cm])
    tabla_resumen.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#dddddd")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 10))

    # --- Gráfico de compras por día ---
    elementos.append(Paragraph("COMPRAS POR DÍA", estilo_seccion))
    if compras_dias:
        elementos.append(_construir_grafico_compras_por_dia(compras_dias))
    else:
        elementos.append(Paragraph("No hay compras registradas en este período.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Proveedores ---
    elementos.append(Paragraph("COMPRAS POR PROVEEDOR", estilo_seccion))
    if proveedores:
        encabezado_prov = ["Proveedor", "Cantidad de Compras", "Total"]
        filas_prov = [encabezado_prov] + [
            [p["proveedor"], str(p["cantidad"]), _formato_gs(p["total"])]
            for p in proveedores
        ]
        tabla_prov = Table(filas_prov, colWidths=[9 * cm, 4 * cm, 3.5 * cm], repeatRows=1)
        tabla_prov.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tabla_prov)
    else:
        elementos.append(Paragraph("No hay compras registradas en este período.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Top productos más comprados ---
    elementos.append(Paragraph("PRODUCTOS MÁS COMPRADOS", estilo_seccion))
    if top_productos:
        encabezado_top = ["#", "Producto", "Cantidad", "Importe"]
        filas_top = [encabezado_top] + [
            [str(i + 1), p["nombre"], f"{p['cantidad']:g}", _formato_gs(p["importe"])]
            for i, p in enumerate(top_productos)
        ]
        tabla_top = Table(filas_top, colWidths=[1 * cm, 8 * cm, 3 * cm, 4 * cm])
        tabla_top.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tabla_top)
    else:
        elementos.append(Paragraph("No hay productos comprados en este período.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Lista completa de compras ---
    elementos.append(Paragraph("DETALLE DE COMPRAS DEL PERÍODO", estilo_seccion))
    if resumen["compras"]:
        encabezado_compras = ["Código", "Fecha Compra", "Proveedor", "N° Comprobante", "Importe"]
        filas_compras = [encabezado_compras]
        for c in resumen["compras"]:
            filas_compras.append([
                str(c["id"]), _fecha_legible(c["fecha_compra"]), c["proveedor"][:26],
                c["nro_comprobante"] or "—", _formato_gs(c["importe"]),
            ])
        tabla_compras = Table(filas_compras, colWidths=[1.8 * cm, 3 * cm, 6 * cm, 3.5 * cm, 3.7 * cm], repeatRows=1)
        tabla_compras.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (4, 0), (4, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elementos.append(tabla_compras)
    else:
        elementos.append(Paragraph("No hay compras registradas en este período.", estilo_normal))

    doc.build(elementos)
    return ruta_destino
