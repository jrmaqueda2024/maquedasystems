"""
reporte_veterinaria_pdf.py
Genera el Reporte / Carnet de Salud de una Mascota en PDF para entregar al
cliente (dueño): membrete del local, datos del dueño y la mascota,
historial clínico completo, vacunas aplicadas y tratamientos registrados.
Usado desde el módulo Veterinaria → Ficha de la Mascota.

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
ROJO = colors.HexColor("#dc2626")
NARANJA = colors.HexColor("#d97706")


def _formato_gs(monto) -> str:
    try:
        return f"Gs. {float(monto):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "Gs. 0"


def _fecha_legible(fecha_texto: str) -> str:
    if not fecha_texto:
        return "—"
    try:
        return datetime.date.fromisoformat(fecha_texto[:10]).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return fecha_texto


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


def generar_reporte_mascota_pdf(ruta_destino: str, ficha: dict) -> str:
    """ficha: el dict devuelto por models_veterinaria.obtener_ficha_completa(),
    con las claves 'mascota', 'consultas', 'vacunas' y 'tratamientos'."""
    local = _datos_local()
    m = ficha["mascota"]

    doc = SimpleDocTemplate(
        ruta_destino, pagesize=A4,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    )
    estilos = getSampleStyleSheet()
    estilo_nombre_local = ParagraphStyle("NombreLocal", parent=estilos["Title"], fontSize=16,
                                        textColor=AZUL_RIBBON, spaceAfter=2)
    estilo_datos_local = ParagraphStyle("DatosLocal", parent=estilos["Normal"], fontSize=8,
                                        textColor=GRIS_TEXTO)
    estilo_titulo_doc = ParagraphStyle("TituloDoc", parent=estilos["Heading1"], fontSize=18,
                                       alignment=TA_RIGHT, textColor=colors.HexColor("#1e293b"))
    estilo_num_doc = ParagraphStyle("NumDoc", parent=estilos["Normal"], fontSize=10,
                                    alignment=TA_RIGHT, textColor=GRIS_TEXTO)
    estilo_seccion = ParagraphStyle("Seccion", parent=estilos["Heading2"], fontSize=12,
                                    textColor=colors.white, backColor=AZUL_RIBBON, spaceBefore=10,
                                    spaceAfter=6, leftIndent=4, borderPadding=4)
    estilo_normal = estilos["Normal"]
    estilo_footer = ParagraphStyle("Footer", parent=estilos["Normal"], fontSize=8,
                                   textColor=GRIS_TEXTO, alignment=TA_CENTER)

    elementos = []

    # --- Encabezado: datos del local a la izquierda, título a la derecha ---
    encabezado = Table([[
        Paragraph(local["nombre"] or "Nombre del Local", estilo_nombre_local),
        Paragraph("REPORTE VETERINARIO", estilo_titulo_doc),
    ]], colWidths=[10 * cm, 7 * cm])
    encabezado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(encabezado)

    datos_local_txt = f"RUC: {local['ruc']}   Tel: {local['telefono']}<br/>{local['direccion']}"
    fila2 = Table([[
        Paragraph(datos_local_txt, estilo_datos_local),
        Paragraph(f"Ficha N° {m['id']}<br/>Emitido: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
                 estilo_num_doc),
    ]], colWidths=[10 * cm, 7 * cm])
    fila2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(fila2)
    elementos.append(Spacer(1, 4))
    elementos.append(Table([[""]], colWidths=[17 * cm], rowHeights=[1],
                           style=[("LINEBELOW", (0, 0), (-1, -1), 1, AZUL_RIBBON)]))
    elementos.append(Spacer(1, 14))

    # --- Datos del dueño y de la mascota, lado a lado ---
    datos_dueño = (
        f"<b>{m['dueño']}</b><br/>"
        f"Teléfono: {m['dueño_telefono'] or '—'}"
    )
    peso_texto = f"{m['peso_kg']} Kg" if m['peso_kg'] else "—"
    datos_mascota = (
        f"<b>{m['nombre']}</b>{'  (Fallecido)' if m['fallecido'] else ''}<br/>"
        f"Especie: {m['especie'] or '—'}   Raza: {m['raza'] or '—'}<br/>"
        f"Sexo: {m['sexo']}   Edad: {m['edad']}<br/>"
        f"Color: {m['color'] or '—'}   Peso actual: {peso_texto}<br/>"
        f"Microchip: {m['microchip'] or '—'}   "
        f"Esterilizado: {'Sí' if m['esterilizado'] else 'No'}"
    )
    tabla_encabezados = Table([
        [Paragraph("DUEÑO", estilo_seccion), Paragraph("MASCOTA", estilo_seccion)],
        [Paragraph(datos_dueño, estilo_normal), Paragraph(datos_mascota, estilo_normal)],
    ], colWidths=[8.5 * cm, 8.5 * cm])
    tabla_encabezados.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    ]))
    elementos.append(tabla_encabezados)
    if m["observaciones"]:
        elementos.append(Spacer(1, 4))
        elementos.append(Paragraph(f"<b>Observaciones generales:</b> {m['observaciones']}", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Historial clínico ---
    elementos.append(Paragraph("HISTORIAL CLÍNICO", estilo_seccion))
    consultas = ficha["consultas"]
    if consultas:
        for c in consultas:
            encabezado_consulta = (
                f"<b>{_fecha_legible(c['fecha'])}</b> — {c['motivo']}"
                f"{'  ·  Costo: ' + _formato_gs(c['costo']) if c['costo'] else ''}"
            )
            elementos.append(Paragraph(encabezado_consulta, ParagraphStyle(
                "ConsultaFecha", parent=estilos["Normal"], fontSize=9.5,
                textColor=AZUL_RIBBON, spaceBefore=6)))
            detalle_partes = []
            if c["diagnostico"]:
                detalle_partes.append(f"<b>Diagnóstico:</b> {c['diagnostico']}")
            if c["tratamiento_indicado"]:
                detalle_partes.append(f"<b>Tratamiento indicado:</b> {c['tratamiento_indicado']}")
            signos = []
            if c["peso_kg"]:
                signos.append(f"Peso: {c['peso_kg']} Kg")
            if c["temperatura"]:
                signos.append(f"Temperatura: {c['temperatura']} °C")
            if signos:
                detalle_partes.append("  ·  ".join(signos))
            if c["observaciones"]:
                detalle_partes.append(f"<b>Observaciones:</b> {c['observaciones']}")
            if c["proxima_visita"]:
                detalle_partes.append(f"<b>Próxima visita:</b> {_fecha_legible(c['proxima_visita'])}")
            if c["atendido_por"]:
                detalle_partes.append(f"<i>Atendido por: {c['atendido_por']}</i>")
            if detalle_partes:
                elementos.append(Paragraph("<br/>".join(detalle_partes), estilo_normal))
    else:
        elementos.append(Paragraph("No hay consultas registradas.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Vacunas ---
    elementos.append(Paragraph("VACUNAS APLICADAS", estilo_seccion))
    vacunas = ficha["vacunas"]
    if vacunas:
        encabezado_tabla = ["Vacuna", "Fecha Aplicación", "Próxima Dosis", "Lote", "Veterinario"]
        filas = [encabezado_tabla]
        for v in vacunas:
            filas.append([
                v["vacuna"], _fecha_legible(v["fecha_aplicacion"]),
                _fecha_legible(v["proxima_dosis"]), v["lote"] or "—", v["veterinario"] or "—",
            ])
        tabla_vacunas = Table(filas, colWidths=[4*cm, 3.2*cm, 3.2*cm, 2.6*cm, 4*cm], repeatRows=1)
        tabla_vacunas.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tabla_vacunas)
    else:
        elementos.append(Paragraph("No hay vacunas registradas.", estilo_normal))
    elementos.append(Spacer(1, 10))

    # --- Tratamientos ---
    elementos.append(Paragraph("TRATAMIENTOS / DESPARASITACIONES", estilo_seccion))
    tratamientos = ficha["tratamientos"]
    if tratamientos:
        encabezado_tabla = ["Tipo", "Producto", "Inicio", "Fin", "Dosis", "Frecuencia", "Estado"]
        filas = [encabezado_tabla]
        for t in tratamientos:
            filas.append([
                t["tipo"], t["producto"], _fecha_legible(t["fecha_inicio"]),
                _fecha_legible(t["fecha_fin"]), t["dosis"] or "—", t["frecuencia"] or "—", t["estado"],
            ])
        tabla_trat = Table(filas, colWidths=[2.4*cm, 3.2*cm, 2.3*cm, 2.3*cm, 2.3*cm, 2.5*cm, 2*cm],
                          repeatRows=1)
        estilo_trat = [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_RIBBON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for i, t in enumerate(tratamientos, start=1):
            if t["estado"] == "Activo":
                estilo_trat.append(("TEXTCOLOR", (6, i), (6, i), VERDE))
                estilo_trat.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))
        tabla_trat.setStyle(TableStyle(estilo_trat))
        elementos.append(tabla_trat)
    else:
        elementos.append(Paragraph("No hay tratamientos registrados.", estilo_normal))

    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("Documento informativo — no constituye una factura ni un comprobante fiscal.",
                               estilo_footer))

    doc.build(elementos)
    return ruta_destino


def generar_certificado_vacuna_pdf(ruta_destino: str, v: dict) -> str:
    """v: el dict devuelto por models_veterinaria.obtener_vacuna_detalle().
    Genera un certificado de un único registro de vacunación, para
    entregar o enviar al dueño como comprobante."""
    local = _datos_local()

    doc = SimpleDocTemplate(
        ruta_destino, pagesize=A4,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    )
    estilos = getSampleStyleSheet()
    estilo_nombre_local = ParagraphStyle("NombreLocalV", parent=estilos["Title"], fontSize=16,
                                        textColor=AZUL_RIBBON, spaceAfter=2)
    estilo_datos_local = ParagraphStyle("DatosLocalV", parent=estilos["Normal"], fontSize=8,
                                        textColor=GRIS_TEXTO)
    estilo_titulo_doc = ParagraphStyle("TituloDocV", parent=estilos["Heading1"], fontSize=17,
                                       alignment=TA_RIGHT, textColor=colors.HexColor("#1e293b"))
    estilo_num_doc = ParagraphStyle("NumDocV", parent=estilos["Normal"], fontSize=10,
                                    alignment=TA_RIGHT, textColor=GRIS_TEXTO)
    estilo_seccion = ParagraphStyle("SeccionV", parent=estilos["Heading2"], fontSize=12,
                                    textColor=colors.white, backColor=AZUL_RIBBON, spaceBefore=10,
                                    spaceAfter=6, leftIndent=4, borderPadding=4)
    estilo_normal = estilos["Normal"]
    estilo_footer = ParagraphStyle("FooterV", parent=estilos["Normal"], fontSize=8,
                                   textColor=GRIS_TEXTO, alignment=TA_CENTER)

    elementos = []
    encabezado = Table([[
        Paragraph(local["nombre"] or "Nombre del Local", estilo_nombre_local),
        Paragraph("CERTIFICADO DE<br/>VACUNACIÓN", estilo_titulo_doc),
    ]], colWidths=[10 * cm, 7 * cm])
    encabezado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(encabezado)

    datos_local_txt = f"RUC: {local['ruc']}   Tel: {local['telefono']}<br/>{local['direccion']}"
    fila2 = Table([[
        Paragraph(datos_local_txt, estilo_datos_local),
        Paragraph(f"N° {v['id']}<br/>Emitido: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
                 estilo_num_doc),
    ]], colWidths=[10 * cm, 7 * cm])
    fila2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(fila2)
    elementos.append(Spacer(1, 4))
    elementos.append(Table([[""]], colWidths=[17 * cm], rowHeights=[1],
                           style=[("LINEBELOW", (0, 0), (-1, -1), 1, AZUL_RIBBON)]))
    elementos.append(Spacer(1, 14))

    datos_mascota = (
        f"<b>{v['mascota']}</b><br/>"
        f"Especie: {v['especie'] or '—'}   Raza: {v['raza'] or '—'}<br/>"
        f"Dueño: {v['dueño'] or '—'}   Teléfono: {v['dueño_telefono'] or '—'}"
    )
    elementos.append(Paragraph("DATOS DEL PACIENTE", estilo_seccion))
    elementos.append(Paragraph(datos_mascota, estilo_normal))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("DETALLE DE LA VACUNA APLICADA", estilo_seccion))
    datos_vacuna = [
        ["Vacuna", v["vacuna"]],
        ["Fecha de Aplicación", _fecha_legible(v["fecha_aplicacion"])],
        ["Próxima Dosis", _fecha_legible(v["proxima_dosis"])],
        ["Lote", v["lote"] or "—"],
        ["Veterinario Responsable", v["veterinario"] or "—"],
    ]
    tabla_vacuna = Table(datos_vacuna, colWidths=[6 * cm, 11 * cm])
    tabla_vacuna.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#dddddd")),
    ]))
    elementos.append(tabla_vacuna)

    if v["observaciones"]:
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph(f"<b>Observaciones:</b> {v['observaciones']}", estilo_normal))

    elementos.append(Spacer(1, 24))
    elementos.append(Paragraph("Documento informativo — no constituye una factura ni un comprobante fiscal.",
                               estilo_footer))

    doc.build(elementos)
    return ruta_destino


def generar_reporte_consulta_pdf(ruta_destino: str, c: dict) -> str:
    """c: el dict devuelto por models_veterinaria.obtener_consulta_detalle().
    Genera la constancia de una única consulta veterinaria, para entregar
    o enviar al dueño como resumen de la visita."""
    local = _datos_local()

    doc = SimpleDocTemplate(
        ruta_destino, pagesize=A4,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    )
    estilos = getSampleStyleSheet()
    estilo_nombre_local = ParagraphStyle("NombreLocalC", parent=estilos["Title"], fontSize=16,
                                        textColor=AZUL_RIBBON, spaceAfter=2)
    estilo_datos_local = ParagraphStyle("DatosLocalC", parent=estilos["Normal"], fontSize=8,
                                        textColor=GRIS_TEXTO)
    estilo_titulo_doc = ParagraphStyle("TituloDocC", parent=estilos["Heading1"], fontSize=17,
                                       alignment=TA_RIGHT, textColor=colors.HexColor("#1e293b"))
    estilo_num_doc = ParagraphStyle("NumDocC", parent=estilos["Normal"], fontSize=10,
                                    alignment=TA_RIGHT, textColor=GRIS_TEXTO)
    estilo_seccion = ParagraphStyle("SeccionC", parent=estilos["Heading2"], fontSize=12,
                                    textColor=colors.white, backColor=AZUL_RIBBON, spaceBefore=10,
                                    spaceAfter=6, leftIndent=4, borderPadding=4)
    estilo_normal = estilos["Normal"]
    estilo_footer = ParagraphStyle("FooterC", parent=estilos["Normal"], fontSize=8,
                                   textColor=GRIS_TEXTO, alignment=TA_CENTER)

    elementos = []
    encabezado = Table([[
        Paragraph(local["nombre"] or "Nombre del Local", estilo_nombre_local),
        Paragraph("CONSTANCIA DE<br/>CONSULTA", estilo_titulo_doc),
    ]], colWidths=[10 * cm, 7 * cm])
    encabezado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(encabezado)

    datos_local_txt = f"RUC: {local['ruc']}   Tel: {local['telefono']}<br/>{local['direccion']}"
    fila2 = Table([[
        Paragraph(datos_local_txt, estilo_datos_local),
        Paragraph(f"N° {c['id']}<br/>Emitido: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
                 estilo_num_doc),
    ]], colWidths=[10 * cm, 7 * cm])
    fila2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos.append(fila2)
    elementos.append(Spacer(1, 4))
    elementos.append(Table([[""]], colWidths=[17 * cm], rowHeights=[1],
                           style=[("LINEBELOW", (0, 0), (-1, -1), 1, AZUL_RIBBON)]))
    elementos.append(Spacer(1, 14))

    datos_mascota = (
        f"<b>{c['mascota']}</b><br/>"
        f"Especie: {c['especie'] or '—'}   Raza: {c['raza'] or '—'}   Sexo: {c['sexo']}<br/>"
        f"Dueño: {c['dueño'] or '—'}   Teléfono: {c['dueño_telefono'] or '—'}"
    )
    elementos.append(Paragraph("DATOS DEL PACIENTE", estilo_seccion))
    elementos.append(Paragraph(datos_mascota, estilo_normal))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("DETALLE DE LA CONSULTA", estilo_seccion))
    peso_texto = f"{c['peso_kg']} Kg" if c["peso_kg"] else "—"
    temperatura_texto = f"{c['temperatura']} °C" if c["temperatura"] else "—"
    datos_consulta = [
        ["Fecha", _fecha_legible(c["fecha"])],
        ["Motivo", c["motivo"]],
        ["Diagnóstico", c["diagnostico"] or "—"],
        ["Tratamiento Indicado", c["tratamiento_indicado"] or "—"],
        ["Peso", peso_texto],
        ["Temperatura", temperatura_texto],
        ["Próxima Visita", _fecha_legible(c["proxima_visita"])],
        ["Costo de la Consulta", _formato_gs(c["costo"]) if c["costo"] else "—"],
        ["Atendido por", c["atendido_por"] or "—"],
    ]
    tabla_consulta = Table(datos_consulta, colWidths=[5 * cm, 12 * cm])
    tabla_consulta.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#dddddd")),
    ]))
    elementos.append(tabla_consulta)

    if c["observaciones"]:
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph(f"<b>Observaciones:</b> {c['observaciones']}", estilo_normal))

    elementos.append(Spacer(1, 24))
    elementos.append(Paragraph("Documento informativo — no constituye una factura ni un comprobante fiscal.",
                               estilo_footer))

    doc.build(elementos)
    return ruta_destino
