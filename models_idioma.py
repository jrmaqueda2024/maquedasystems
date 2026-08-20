"""
models_idioma.py
Configuración del idioma de la interfaz del sistema (una sola fila,
válida para todo el sistema — no es una preferencia por usuario). Ver
traducciones.py para el diccionario de textos traducidos.
"""
from database import conectar

IDIOMA_POR_DEFECTO = "es"


def obtener_idioma_actual() -> str:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT idioma FROM configuracion_idioma WHERE id = 1")
    fila = cursor.fetchone()
    conn.close()
    return fila[0] if fila else IDIOMA_POR_DEFECTO


def guardar_idioma(idioma: str) -> tuple[bool, str]:
    from traducciones import IDIOMAS
    if idioma not in IDIOMAS:
        return False, "Idioma inválido."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO configuracion_idioma (id, idioma) VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET idioma = excluded.idioma
    """, (idioma,))
    conn.commit()
    conn.close()
    return True, "Idioma actualizado correctamente."
