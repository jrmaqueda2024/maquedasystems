"""
reporte_uso_pdf.py
Genera el PDF "con dashboard" del módulo Uso del Sistema: portada con
KPIs, gráfico de barras de actividad por hora del día, y tabla con el
historial de sesiones.  Usa el mismo estilo visual que reporte_pdf.py
(ventas), basado en reportlab.
"""
import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart

AZUL       = colors.HexColor("#1d5fd6")
AZUL_OSC   = colors.HexColor("#163d8c")
VERDE      = colors.HexColor("#16a34a")
GRIS       = colors.HexColor("#6b7280")
GRIS_CLARO = colors.HexColor("#f3f4f6")
MORADO     = colors.HexColor("#7c3aed")
NARANJA    = colors.HexColor("#f59e0b")


def _fmt(segs: int) -> str:
    """Formatea segundos como HH:MM:SS."""
    h = segs // 3600
    m = (segs % 3600) // 60
    s = segs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def generar_pdf_uso_sistema(
    ruta_destino: str,
    tiempo_sesion_actual: int,
    uso_hoy: int,
    uso_general: int,
    hora_pico_datos,          # tuple (hora_int, segs) o None
    actividad_por_hora_datos, # list de (hora, segs) o []
    sesiones: list,           # lista de dicts con usuario_nombre, fecha_inicio, fecha_fin, duracion_segundos
    generado_por: str = "",
) -> str:
    doc = SimpleDocTemplate(
        ruta_destino, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    estilos = getSampleStyleSheet()
    ancho_util = A4[0] - 3 * cm

    estilo_titulo = ParagraphStyle("titulo", parent=estilos["Title"],
                                   textColor=AZUL, fontSize=20, spaceAfter=6)
    estilo_sub    = ParagraphStyle("sub",    parent=estilos["Normal"],
                                   textColor=GRIS, fontSize=10, spaceAfter=14)
    estilo_seccion = ParagraphStyle("sec",  parent=estilos["Heading2"],
                                    textColor=AZUL_OSC, fontSize=12,
                                    spaceBefore=14, spaceAfter=6)
    estilo_normal = estilos["Normal"]

    elementos = []

    # ── Encabezado ────────────────────────────────────────────
    elementos.append(Paragraph("Reporte de Uso del Sistema", estilo_titulo))
    ahora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    elementos.append(Paragraph(
        f"Generado: {ahora}"
        + (f"   |   Por: {generado_por}" if generado_por else ""),
        estilo_sub,
    ))
    elementos.append(HRFlowable(width="100%", thickness=1, color=AZUL))
    elementos.append(Spacer(1, 10))

    # ── KPIs ─────────────────────────────────────────────────
    if hora_pico_datos:
        h_pico, segs_pico = hora_pico_datos
        texto_pico = f"{h_pico:02d}:00 a {h_pico:02d}:59"
        sub_pico   = f"({_fmt(segs_pico)} acumulado)"
    else:
        texto_pico = "Sin datos"
        sub_pico   = ""

    kpis = [
        ("Sesión actual",        _fmt(tiempo_sesion_actual), AZUL),
        ("Uso de hoy",           _fmt(uso_hoy),              VERDE),
        ("Uso total acumulado",  _fmt(uso_general),          MORADO),
        ("Hora pico",            texto_pico + ("\n" + sub_pico if sub_pico else ""), NARANJA),
    ]
    ancho_kpi = ancho_util / 4
    datos_kpis = [[
        Table(
            [[Paragraph(f"<font color='#6b7280' size='8'>{label}</font>", estilo_normal)],
             [Paragraph(f"<font color='{color.hexval()}' size='13'><b>{valor}</b></font>",
                        estilo_normal)]],
            colWidths=[ancho_kpi - 0.4 * cm],
            style=TableStyle([
                ("BOX",        (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
                ("LEFTPADDING",  (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING",   (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
            ]),
        )
        for label, valor, color in kpis
    ]]
    tabla_kpis = Table(datos_kpis, colWidths=[ancho_kpi] * 4)
    tabla_kpis.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(tabla_kpis)
    elementos.append(Spacer(1, 14))

    # ── Gráfico de actividad por hora ─────────────────────────
    elementos.append(Paragraph("Actividad por hora del día (segundos acumulados)", estilo_seccion))
    mapa_horas = dict(actividad_por_hora_datos or [])
    valores_horas = [mapa_horas.get(h, 0) for h in range(24)]
    etiquetas_horas = [f"{h:02d}" for h in range(24)]

    if any(v > 0 for v in valores_horas):
        drawing = Drawing(ancho_util, 160)
        chart = VerticalBarChart()
        chart.x        = 30
        chart.y        = 10
        chart.height   = 120
        chart.width    = ancho_util - 50
        chart.data     = [valores_horas]
        chart.bars[0].fillColor = AZUL
        chart.categoryAxis.categoryNames = etiquetas_horas
        chart.categoryAxis.labels.fontSize = 6
        chart.valueAxis.labelTextFormat    = "%d"
        chart.valueAxis.labels.fontSize    = 7
        chart.groupSpacing = 1
        drawing.add(chart)
        elementos.append(drawing)
    else:
        elementos.append(Paragraph("Aún no hay datos de actividad por hora.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # ── Historial de sesiones ─────────────────────────────────
    elementos.append(Paragraph("Últimas sesiones", estilo_seccion))

    enc_cols = ["Usuario", "Inicio", "Fin", "Duración"]
    filas_sesiones = [enc_cols]
    for s in sesiones:
        filas_sesiones.append([
            s.get("usuario_nombre", ""),
            s.get("fecha_inicio", ""),
            s.get("fecha_fin", "") or "En curso",
            _fmt(s.get("duracion_segundos", 0)),
        ])

    anchos_ses = [ancho_util * p for p in (0.28, 0.28, 0.25, 0.19)]
    tabla_ses = Table(filas_sesiones, colWidths=anchos_ses, repeatRows=1)
    tabla_ses.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  AZUL),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("GRID",         (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("ALIGN",        (3, 0), (3, -1),  "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_ses)

    doc.build(elementos)
    return ruta_destino
