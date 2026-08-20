"""
reporte_pdf.py
Genera el Reporte de Ventas en PDF para un rango de fechas: resumen
financiero general, gráfico de barras de ventas por día, ranking de
productos más vendidos, y la lista completa de ventas del período.

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

from models_ventas import (
    resumen_financiero_en_rango, ventas_por_dia_en_rango, productos_mas_vendidos_en_rango,
    listar_movimientos_caja,
)

AZUL_RIBBON = colors.HexColor("#1d5fd6")
GRIS_TEXTO = colors.HexColor("#555555")


def _formato_gs(monto: float) -> str:
    return f"Gs. {monto:,.0f}"


def _fecha_legible(fecha_iso: str) -> str:
    """Convierte 'YYYY-MM-DD' a 'DD/MM/YYYY'."""
    try:
        return datetime.date.fromisoformat(fecha_iso).strftime("%d/%m/%Y")
    except ValueError:
        return fecha_iso


def _construir_grafico_ventas_por_dia(datos_dias: list[dict]) -> Drawing:
    """Construye un gráfico de barras verticales con el total vendido cada
    día del rango, usando reportlab.graphics (no necesita matplotlib)."""
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


def generar_reporte_pdf(ruta_destino: str, fecha_desde: str, fecha_hasta: str,
                         generado_por: str = "", usuario_id: int | None = None) -> str:
    """Genera el PDF en ruta_destino. fecha_desde y fecha_hasta en formato
    'YYYY-MM-DD'. Devuelve la ruta del archivo generado.

    usuario_id: si se indica, limita las ventas y sus totales derivados a
    las de ese usuario (ver models_ventas.resumen_financiero_en_rango)."""

    resumen = resumen_financiero_en_rango(fecha_desde, fecha_hasta, usuario_id=usuario_id)
    ventas_dias = ventas_por_dia_en_rango(fecha_desde, fecha_hasta, usuario_id=usuario_id)
    top_productos = productos_mas_vendidos_en_rango(fecha_desde, fecha_hasta, limite=10, usuario_id=usuario_id)
    movimientos_caja = listar_movimientos_caja(fecha_desde, fecha_hasta)

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
    elementos.append(Paragraph("Reporte de Ventas", estilo_titulo))
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
        ["Cantidad de Ventas", str(len(resumen["ventas"]))],
        ["Ventas Totales", _formato_gs(resumen["ventas_totales"])],
        ["Ganancia Estimada", _formato_gs(resumen["ganancia"])],
        ["Ventas en Efectivo", _formato_gs(resumen["ventas_efectivo"])],
        ["Ventas por Transferencia", _formato_gs(resumen["ventas_transferencia"])],
        ["Entradas de Efectivo", _formato_gs(resumen["entradas"])],
        ["Salidas de Efectivo", _formato_gs(resumen["salidas"])],
        ["Devoluciones", _formato_gs(resumen["devoluciones"])],
        ["Dinero en Caja", _formato_gs(resumen["dinero_en_caja"])],
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

    # --- Gráfico de ventas por día ---
    elementos.append(Paragraph("VENTAS POR DÍA", estilo_seccion))
    if ventas_dias:
        elementos.append(_construir_grafico_ventas_por_dia(ventas_dias))
    else:
        elementos.append(Paragraph("No hay ventas registradas en este período.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Entradas y Salidas de Efectivo ---
    elementos.append(Paragraph("ENTRADAS Y SALIDAS DE EFECTIVO", estilo_seccion))
    if movimientos_caja:
        encabezado_caja = ["Fecha", "Tipo", "Monto", "Motivo", "Registrado por"]
        filas_caja = [encabezado_caja] + [
            [m["fecha"], "Entrada" if m["tipo"] == "entrada" else "Salida",
             _formato_gs(m["monto"]), m["descripcion"], m["usuario"]]
            for m in movimientos_caja
        ]
        tabla_caja = Table(filas_caja, colWidths=[3.2 * cm, 2.3 * cm, 2.8 * cm, 5.5 * cm, 2.2 * cm], repeatRows=1)
        estilo_tabla_caja = [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        for i, m in enumerate(movimientos_caja, start=1):
            color_tipo = colors.HexColor("#16a34a") if m["tipo"] == "entrada" else colors.HexColor("#dc2626")
            estilo_tabla_caja.append(("TEXTCOLOR", (1, i), (2, i), color_tipo))
        tabla_caja.setStyle(TableStyle(estilo_tabla_caja))
        elementos.append(tabla_caja)
    else:
        elementos.append(Paragraph("No hay entradas ni salidas de efectivo registradas en este período.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Top productos más vendidos ---
    elementos.append(Paragraph("PRODUCTOS MÁS VENDIDOS", estilo_seccion))
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
        elementos.append(Paragraph("No hay productos vendidos en este período.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Lista completa de ventas ---
    elementos.append(Paragraph("DETALLE DE VENTAS DEL PERÍODO", estilo_seccion))
    if resumen["ventas"]:
        encabezado_ventas = ["Código", "Fecha y Hora", "Cliente", "Importe", "Estado", "Forma de Pago"]
        filas_ventas = [encabezado_ventas]
        for v in resumen["ventas"]:
            filas_ventas.append([
                str(v["id"]), v["fecha"], v["cliente"][:24], _formato_gs(v["importe"]),
                v["estado"], v["forma_pago"],
            ])
        tabla_ventas = Table(filas_ventas, colWidths=[1.8 * cm, 3.6 * cm, 4.5 * cm, 3 * cm, 2.5 * cm, 3.6 * cm], repeatRows=1)
        estilo_tabla_ventas = [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        # Resaltar en gris las ventas canceladas
        for i, v in enumerate(resumen["ventas"], start=1):
            if v["estado"] == "Cancelado":
                estilo_tabla_ventas.append(("TEXTCOLOR", (0, i), (-1, i), colors.HexColor("#9ca3af")))
        tabla_ventas.setStyle(TableStyle(estilo_tabla_ventas))
        elementos.append(tabla_ventas)
    else:
        elementos.append(Paragraph("No hay ventas registradas en este período.", estilo_normal))

    doc.build(elementos)
    return ruta_destino
