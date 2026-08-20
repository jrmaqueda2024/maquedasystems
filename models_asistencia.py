"""
models_asistencia.py
Lógica de negocio del módulo Asistencia Técnica: ingreso de equipos a
reparación (casos técnicos), catálogo de Tipos de Equipo (lista editable,
igual que Zona/Cobrador), catálogo de Equipos Registrados (para F3 -
Buscar Equipo, útil con clientes recurrentes) y el flujo de estados de
cada caso.
"""
from database import conectar

ESTADOS = ["Entrada", "En Espera", "En Revisión", "Disponible para Retiro", "Retirado"]
PRIORIDADES = ["Baja", "Media", "Alta", "Urgente"]


# ============================================================
# TIPOS DE EQUIPO (lista editable, igual que Zona/Cobrador)
# ============================================================
def listar_tipos_equipo() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM tipos_equipo ORDER BY nombre")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1]} for f in filas]


def crear_tipo_equipo(nombre: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del tipo de equipo no puede estar vacío."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO tipos_equipo (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        return True, "Tipo de equipo creado."
    except Exception:
        return False, "Ese tipo de equipo ya existe."
    finally:
        conn.close()


# ============================================================
# EQUIPOS REGISTRADOS (catálogo para F3 - Buscar Equipo y pestaña Equipos)
# ============================================================
def buscar_equipos(texto_busqueda: str = "") -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    condiciones = []
    parametros: list = []
    if texto_busqueda.strip():
        condiciones.append(
            "(er.descripcion LIKE ? OR COALESCE(er.nro_serie,'') LIKE ? "
            "OR COALESCE(cl.nombre,'') LIKE ? OR COALESCE(te.nombre,'') LIKE ?)"
        )
        q = f"%{texto_busqueda.strip()}%"
        parametros += [q, q, q, q]
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT er.id, er.descripcion, COALESCE(te.nombre, ''), COALESCE(er.nro_serie, ''),
               COALESCE(cl.nombre, 'Sin cliente'), er.cliente_id, er.tipo_equipo_id
        FROM equipos_registrados er
        LEFT JOIN clientes cl ON er.cliente_id = cl.id
        LEFT JOIN tipos_equipo te ON er.tipo_equipo_id = te.id
        {where}
        ORDER BY er.descripcion
    """, parametros)
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "descripcion": f[1], "tipo_equipo": f[2], "nro_serie": f[3],
         "cliente": f[4], "cliente_id": f[5], "tipo_equipo_id": f[6]}
        for f in filas
    ]


def registrar_equipo_si_no_existe(cliente_id, tipo_equipo_id, nro_serie: str, descripcion: str):
    """Guarda el equipo en el catálogo para que la próxima vez se pueda
    encontrar con F3 - Buscar Equipo. Evita duplicar si ya existe uno con
    la misma descripción + N° de serie para el mismo cliente."""
    if not descripcion.strip():
        return
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM equipos_registrados
        WHERE descripcion = ? AND COALESCE(nro_serie, '') = ? AND COALESCE(cliente_id, -1) = COALESCE(?, -1)
    """, (descripcion.strip(), (nro_serie or "").strip(), cliente_id))
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO equipos_registrados (cliente_id, tipo_equipo_id, nro_serie, descripcion)
            VALUES (?, ?, ?, ?)
        """, (cliente_id, tipo_equipo_id, (nro_serie or "").strip(), descripcion.strip()))
        conn.commit()
    conn.close()


# ============================================================
# CASOS TÉCNICOS
# ============================================================
def crear_caso(cliente_id, cliente_nombre: str, cliente_documento: str, cliente_direccion: str,
               cliente_telefono: str, tipo_equipo_id, tipo_equipo_texto: str, nro_serie: str,
               descripcion_equipo: str, prioridad: str, observaciones: str,
               usuario_id: int) -> tuple[bool, str, int | None]:
    if not descripcion_equipo.strip():
        return False, "La descripción del equipo es obligatoria.", None
    if prioridad not in PRIORIDADES:
        prioridad = "Media"

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO casos_tecnicos
                (cliente_id, cliente_nombre, cliente_documento, cliente_direccion, cliente_telefono,
                 tipo_equipo_id, tipo_equipo_texto, nro_serie, descripcion_equipo,
                 prioridad, estado, observaciones, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Entrada', ?, ?)
        """, (cliente_id, cliente_nombre.strip(), cliente_documento.strip(), cliente_direccion.strip(),
              cliente_telefono.strip(), tipo_equipo_id, tipo_equipo_texto.strip(), nro_serie.strip(),
              descripcion_equipo.strip(), prioridad, observaciones.strip(), usuario_id))
        caso_id = cursor.lastrowid
        conn.commit()

        registrar_equipo_si_no_existe(cliente_id, tipo_equipo_id, nro_serie, descripcion_equipo)

        return True, f"Caso Nro. {caso_id} registrado correctamente.", caso_id
    except Exception as e:
        conn.rollback()
        return False, f"Error al registrar el caso: {e}", None
    finally:
        conn.close()


def _fila_a_dict(f) -> dict:
    return {
        "id": f[0], "fecha_entrada": f[1], "fecha_estado": f[2], "cliente": f[3],
        "tipo_equipo": f[4], "descripcion_equipo": f[5], "nro_serie": f[6],
        "estado": f[7], "prioridad": f[8], "anulado": bool(f[9]), "recibido_por": f[10] or "",
    }


def listar_casos(mostrar_ultimos: str = "25", incluir_pendientes: bool = True,
                  incluir_anulados: bool = True, incluir_retirados: bool = True,
                  busqueda: str = "") -> list[dict]:
    """mostrar_ultimos: '25', '50', '100' o 'Todos'. Los tres checkboxes
    (Pendientes/Anulados/Retirados) son un OR entre sí: se muestra un caso
    si cumple con AL MENOS UNO de los que estén tildados."""
    conn = conectar()
    cursor = conn.cursor()

    condiciones_estado = []
    if incluir_pendientes:
        condiciones_estado.append("(ct.anulado = 0 AND ct.estado != 'Retirado')")
    if incluir_anulados:
        condiciones_estado.append("(ct.anulado = 1)")
    if incluir_retirados:
        condiciones_estado.append("(ct.anulado = 0 AND ct.estado = 'Retirado')")
    if not condiciones_estado:
        conn.close()
        return []

    condiciones = ["(" + " OR ".join(condiciones_estado) + ")"]
    parametros: list = []
    if busqueda.strip():
        condiciones.append(
            "(ct.cliente_nombre LIKE ? OR COALESCE(ct.nro_serie,'') LIKE ? "
            "OR ct.descripcion_equipo LIKE ? OR CAST(ct.id AS TEXT) LIKE ?)"
        )
        q = f"%{busqueda.strip()}%"
        parametros += [q, q, q, q]
    where = f"WHERE {' AND '.join(condiciones)}"

    limite_sql = ""
    if mostrar_ultimos != "Todos":
        try:
            limite_sql = f" LIMIT {int(mostrar_ultimos)}"
        except ValueError:
            limite_sql = " LIMIT 25"

    cursor.execute(f"""
        SELECT ct.id, ct.fecha_entrada, ct.fecha_estado,
               COALESCE(NULLIF(cl.nombre, ''), ct.cliente_nombre, 'Sin datos'),
               COALESCE(te.nombre, ct.tipo_equipo_texto, ''),
               ct.descripcion_equipo, COALESCE(ct.nro_serie, ''), ct.estado, ct.prioridad,
               ct.anulado, u.nombre_completo
        FROM casos_tecnicos ct
        LEFT JOIN clientes cl ON ct.cliente_id = cl.id
        LEFT JOIN tipos_equipo te ON ct.tipo_equipo_id = te.id
        LEFT JOIN usuarios u ON ct.usuario_id = u.id
        {where}
        ORDER BY ct.id DESC
        {limite_sql}
    """, parametros)
    filas = cursor.fetchall()
    conn.close()
    return [_fila_a_dict(f) for f in filas]


def listar_pendientes(busqueda: str = "") -> list[dict]:
    return listar_casos(mostrar_ultimos="Todos", incluir_pendientes=True,
                        incluir_anulados=False, incluir_retirados=False, busqueda=busqueda)


def listar_casos_por_estado(estado: str) -> list[dict]:
    """Usado por el Dashboard: todos los casos activos (no anulados) en un
    estado puntual."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ct.id, ct.fecha_entrada, ct.fecha_estado,
               COALESCE(NULLIF(cl.nombre, ''), ct.cliente_nombre, 'Sin datos'),
               COALESCE(te.nombre, ct.tipo_equipo_texto, ''),
               ct.descripcion_equipo, COALESCE(ct.nro_serie, ''), ct.estado, ct.prioridad,
               ct.anulado, u.nombre_completo
        FROM casos_tecnicos ct
        LEFT JOIN clientes cl ON ct.cliente_id = cl.id
        LEFT JOIN tipos_equipo te ON ct.tipo_equipo_id = te.id
        LEFT JOIN usuarios u ON ct.usuario_id = u.id
        WHERE ct.anulado = 0 AND ct.estado = ?
        ORDER BY ct.id DESC
    """, (estado,))
    filas = cursor.fetchall()
    conn.close()
    return [_fila_a_dict(f) for f in filas]


def listar_retirados_recientes(limite: int = 25) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ct.id, ct.fecha_entrada, ct.fecha_estado,
               COALESCE(NULLIF(cl.nombre, ''), ct.cliente_nombre, 'Sin datos'),
               COALESCE(te.nombre, ct.tipo_equipo_texto, ''),
               ct.descripcion_equipo, COALESCE(ct.nro_serie, ''), ct.estado, ct.prioridad,
               ct.anulado, u.nombre_completo
        FROM casos_tecnicos ct
        LEFT JOIN clientes cl ON ct.cliente_id = cl.id
        LEFT JOIN tipos_equipo te ON ct.tipo_equipo_id = te.id
        LEFT JOIN usuarios u ON ct.usuario_id = u.id
        WHERE ct.anulado = 0 AND ct.estado = 'Retirado'
        ORDER BY ct.fecha_retiro DESC
        LIMIT ?
    """, (limite,))
    filas = cursor.fetchall()
    conn.close()
    return [_fila_a_dict(f) for f in filas]


def conteos_dashboard() -> dict:
    """Cantidad de casos activos (no anulados) en cada estado, para las
    cabeceras del Dashboard."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT estado, COUNT(*) FROM casos_tecnicos
        WHERE anulado = 0
        GROUP BY estado
    """)
    conteos = {estado: 0 for estado in ESTADOS}
    for estado, cantidad in cursor.fetchall():
        if estado in conteos:
            conteos[estado] = cantidad
    conn.close()
    return conteos


def obtener_caso(caso_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ct.id, ct.fecha_entrada, ct.fecha_estado, ct.fecha_retiro,
               ct.cliente_id, COALESCE(NULLIF(cl.nombre, ''), ct.cliente_nombre, 'Sin datos'),
               ct.cliente_documento, ct.cliente_direccion, ct.cliente_telefono,
               ct.tipo_equipo_id, COALESCE(te.nombre, ct.tipo_equipo_texto, ''),
               ct.nro_serie, ct.descripcion_equipo, ct.prioridad, ct.estado,
               ct.observaciones, ct.anulado, COALESCE(u.nombre_completo, '')
        FROM casos_tecnicos ct
        LEFT JOIN clientes cl ON ct.cliente_id = cl.id
        LEFT JOIN tipos_equipo te ON ct.tipo_equipo_id = te.id
        LEFT JOIN usuarios u ON ct.usuario_id = u.id
        WHERE ct.id = ?
    """, (caso_id,))
    f = cursor.fetchone()
    conn.close()
    if f is None:
        return None
    return {
        "id": f[0], "fecha_entrada": f[1], "fecha_estado": f[2], "fecha_retiro": f[3],
        "cliente_id": f[4], "cliente_nombre": f[5], "cliente_documento": f[6] or "",
        "cliente_direccion": f[7] or "", "cliente_telefono": f[8] or "",
        "tipo_equipo_id": f[9], "tipo_equipo": f[10] or "",
        "nro_serie": f[11] or "", "descripcion_equipo": f[12], "prioridad": f[13],
        "estado": f[14], "observaciones": f[15] or "", "anulado": bool(f[16]),
        "recibido_por": f[17],
    }


def cambiar_estado_caso(caso_id: int, nuevo_estado: str) -> tuple[bool, str]:
    if nuevo_estado not in ESTADOS:
        return False, "Estado inválido."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT anulado FROM casos_tecnicos WHERE id = ?", (caso_id,))
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        return False, "El caso no existe."
    if fila[0]:
        conn.close()
        return False, "El caso está anulado; no se puede cambiar su estado."

    if nuevo_estado == "Retirado":
        cursor.execute("""
            UPDATE casos_tecnicos
            SET estado = ?, fecha_estado = datetime('now', 'localtime'),
                fecha_retiro = datetime('now', 'localtime')
            WHERE id = ?
        """, (nuevo_estado, caso_id))
    else:
        cursor.execute("""
            UPDATE casos_tecnicos
            SET estado = ?, fecha_estado = datetime('now', 'localtime')
            WHERE id = ?
        """, (nuevo_estado, caso_id))
    conn.commit()
    conn.close()
    return True, f"El caso Nro. {caso_id} ahora está en estado '{nuevo_estado}'."


def actualizar_observaciones(caso_id: int, observaciones: str) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE casos_tecnicos SET observaciones = ? WHERE id = ?",
                   (observaciones.strip(), caso_id))
    conn.commit()
    conn.close()
    return True, "Observaciones actualizadas."


def anular_caso(caso_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM casos_tecnicos WHERE id = ?", (caso_id,))
    if cursor.fetchone() is None:
        conn.close()
        return False, "El caso no existe."
    cursor.execute("UPDATE casos_tecnicos SET anulado = 1 WHERE id = ?", (caso_id,))
    conn.commit()
    conn.close()
    return True, f"El caso Nro. {caso_id} fue anulado."
