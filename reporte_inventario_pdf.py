"""
reporte_inventario_pdf.py
Genera el Reporte General de Inventario en PDF: resumen general, productos
bajo stock mínimo, top productos por valor de inventario, y el listado
completo de productos.

Requiere la librería 'reportlab' (pip install reportlab).
"""
import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from models_catalogo import listar_productos, productos_bajo_stock_minimo, top_productos_por_valor_inventario, resumen_inventario

AZUL_RIBBON = colors.HexColor("#1d5fd6")
GRIS_TEXTO = colors.HexColor("#555555")
ROJO_CLARO = colors.HexColor("#fde8e8")


def _formato_gs(monto: float) -> str:
    return f"Gs. {monto:,.0f}"


def generar_reporte_inventario_pdf(ruta_destino: str, generado_por: str = "") -> str:
    """Genera el PDF en ruta_destino. Devuelve la ruta del archivo generado."""
    resumen = resumen_inventario()
    bajo_stock = productos_bajo_stock_minimo()
    top_valor = top_productos_por_valor_inventario(limite=10)
    productos = listar_productos()

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
    elementos.append(Paragraph("Reporte General de Inventario", estilo_titulo))
    pie_generacion = f"Generado el {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
    if generado_por:
        pie_generacion += f" por {generado_por}"
    elementos.append(Paragraph(pie_generacion, estilo_subtitulo))
    elementos.append(Spacer(1, 14))

    # --- Resumen general ---
    elementos.append(Paragraph("RESUMEN GENERAL", estilo_seccion))
    datos_resumen = [
        ["Cantidad de Productos Distintos", str(len(productos))],
        ["Cantidad Total de Unidades en Stock", f"{resumen['cantidad_total']:,.2f}"],
        ["Valor del Inventario (a Precio de Compra)", _formato_gs(resumen["valor_inventario"])],
        ["Valor Comprometido (a Precio de Compra)", _formato_gs(resumen["valor_comprometido"])],
        ["Productos Bajo Stock Mínimo", str(len(bajo_stock))],
    ]
    tabla_resumen = Table(datos_resumen, colWidths=[10 * cm, 6 * cm])
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

    # --- Productos bajo stock mínimo ---
    elementos.append(Paragraph("PRODUCTOS BAJO STOCK MÍNIMO", estilo_seccion))
    if bajo_stock:
        encabezado_bajo = ["Código", "Descripción", "Stock Actual", "Stock Mínimo", "Faltante"]
        filas_bajo = [encabezado_bajo] + [
            [str(p["id"]), p["nombre"], f"{p['stock']:,.2f}", f"{p['stock_minimo']:,.2f}",
             f"{p['stock_minimo'] - p['stock']:,.2f}"]
            for p in bajo_stock
        ]
        tabla_bajo = Table(filas_bajo, colWidths=[2 * cm, 7 * cm, 3 * cm, 3 * cm, 3 * cm])
        tabla_bajo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("BACKGROUND", (0, 1), (-1, -1), ROJO_CLARO),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tabla_bajo)
    else:
        elementos.append(Paragraph("No hay productos bajo el stock mínimo.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Top productos por valor de inventario ---
    elementos.append(Paragraph("TOP PRODUCTOS POR VALOR DE INVENTARIO", estilo_seccion))
    if top_valor:
        encabezado_top = ["#", "Producto", "Stock", "Precio Compra", "Valor en Inventario"]
        filas_top = [encabezado_top] + [
            [str(i + 1), p["nombre"], f"{p['stock']:,.2f}", _formato_gs(p["precio_compra"]), _formato_gs(p["valor"])]
            for i, p in enumerate(top_valor)
        ]
        tabla_top = Table(filas_top, colWidths=[1 * cm, 7 * cm, 3 * cm, 3.5 * cm, 3.5 * cm])
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
        elementos.append(Paragraph("No hay productos con valor de inventario.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Listado completo ---
    elementos.append(Paragraph("LISTADO COMPLETO DE PRODUCTOS", estilo_seccion))
    if productos:
        encabezado_listado = ["Código", "Descripción", "P. Compra", "P. Venta", "Stock", "Disponible"]
        filas_listado = [encabezado_listado]
        for p in productos:
            disponible = p["disponible"] if isinstance(p["disponible"], str) else f"{p['disponible']:,.2f}"
            stock_texto = "—" if p["tipo_producto"] == "Servicio" else f"{p['stock']:,.2f}"
            filas_listado.append([
                str(p["id"]), p["nombre"][:30], _formato_gs(p["precio_compra"]),
                _formato_gs(p["precio_venta"]), stock_texto, disponible,
            ])
        tabla_listado = Table(filas_listado, colWidths=[1.8 * cm, 6.5 * cm, 3 * cm, 3 * cm, 2.5 * cm, 2.5 * cm], repeatRows=1)
        estilo_tabla_listado = [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        ids_bajo_stock = {p["id"] for p in bajo_stock}
        for i, p in enumerate(productos, start=1):
            if p["id"] in ids_bajo_stock:
                estilo_tabla_listado.append(("BACKGROUND", (0, i), (-1, i), ROJO_CLARO))
        tabla_listado.setStyle(TableStyle(estilo_tabla_listado))
        elementos.append(tabla_listado)
    else:
        elementos.append(Paragraph("No hay productos registrados.", estilo_normal))

    doc.build(elementos)
    return ruta_destino
