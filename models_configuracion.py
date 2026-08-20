"""
models_configuracion.py
Persistencia de las preferencias generales del sistema. Por ahora
contiene la configuración de Apariencia (fuente y tamaño de letra),
elegida desde el módulo 'Ajustes del Sistema'.
"""
from database import conectar

FAMILIAS_DE_FUENTE_DISPONIBLES = [
    "Segoe UI", "Arial", "Calibri", "Verdana", "Tahoma", "Century Gothic",
]

FUENTE_FAMILIA_PREDETERMINADA = "Segoe UI"
FUENTE_ESCALA_PREDETERMINADA = 100  # 100% = tamaño original de diseño
TEMA_PREDETERMINADO = "claro"


def obtener_tema() -> str:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT tema FROM configuracion_apariencia WHERE id = 1")
    fila = cursor.fetchone()
    conn.close()
    return (fila[0] if fila and fila[0] else TEMA_PREDETERMINADO)


def guardar_tema(tema: str) -> tuple[bool, str]:
    if tema not in ("claro", "oscuro"):
        return False, "Tema inválido."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO configuracion_apariencia (id, tema)
        VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET tema = excluded.tema
    """, (tema,))
    conn.commit()
    conn.close()
    return True, "Tema guardado correctamente."


def obtener_configuracion_apariencia() -> tuple[str, int]:
    """Devuelve (familia, escala) guardados, o los valores predeterminados
    si todavía no se guardó ninguna preferencia."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT fuente_familia, fuente_escala FROM configuracion_apariencia WHERE id = 1")
    fila = cursor.fetchone()
    conn.close()
    if not fila:
        return FUENTE_FAMILIA_PREDETERMINADA, FUENTE_ESCALA_PREDETERMINADA
    familia = fila[0] or FUENTE_FAMILIA_PREDETERMINADA
    escala = fila[1] or FUENTE_ESCALA_PREDETERMINADA
    return familia, escala


def guardar_configuracion_apariencia(familia: str, escala: int) -> tuple[bool, str]:
    familia = (familia or FUENTE_FAMILIA_PREDETERMINADA).strip()
    try:
        escala = int(escala)
    except (TypeError, ValueError):
        return False, "El tamaño de letra debe ser un número."
    if escala < 60 or escala > 200:
        return False, "El tamaño de letra debe estar entre 60% y 200%."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO configuracion_apariencia (id, fuente_familia, fuente_escala)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            fuente_familia = excluded.fuente_familia,
            fuente_escala  = excluded.fuente_escala
    """, (familia, escala))
    conn.commit()
    conn.close()
    return True, "Apariencia guardada correctamente."
