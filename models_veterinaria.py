"""
models_veterinaria.py
Lógica de negocio del módulo Veterinaria: ficha de Mascotas (ligadas
opcionalmente a un Cliente = dueño), catálogo de Especies (lista editable,
igual que Zona/Cobrador/Tipos de Equipo), Historial Clínico (consultas),
Vacunas aplicadas y Tratamientos/desparasitaciones en curso.
"""
import datetime
from database import conectar

SEXOS = ["Macho", "Hembra", "Desconocido"]
TIPOS_TRATAMIENTO = ["Desparasitación", "Medicación", "Otro"]
ESTADOS_TRATAMIENTO = ["Activo", "Finalizado"]


# ============================================================
# ESPECIES (catálogo editable, igual que Tipos de Equipo)
# ============================================================
def listar_especies() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM especies_mascota ORDER BY nombre")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1]} for f in filas]


def crear_especie(nombre: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre de la especie no puede estar vacío."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO especies_mascota (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        return True, "Especie creada."
    except Exception:
        return False, "Esa especie ya existe."
    finally:
        conn.close()


# ============================================================
# MASCOTAS
# ============================================================
def crear_mascota(nombre: str, cliente_id, dueño_nombre: str, dueño_telefono: str,
                   especie_id, especie_texto: str, raza: str, sexo: str,
                   fecha_nacimiento: str, color: str, peso_kg, microchip: str,
                   esterilizado: bool, observaciones: str) -> tuple[bool, str, int | None]:
    if not nombre.strip():
        return False, "El nombre de la mascota es obligatorio.", None
    if sexo not in SEXOS:
        sexo = "Desconocido"

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO mascotas
                (cliente_id, dueño_nombre, dueño_telefono, nombre, especie_id, especie_texto,
                 raza, sexo, fecha_nacimiento, color, peso_kg, microchip, esterilizado, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cliente_id, dueño_nombre.strip(), dueño_telefono.strip(), nombre.strip(),
              especie_id, especie_texto.strip(), raza.strip(), sexo,
              fecha_nacimiento or None, color.strip(), peso_kg, microchip.strip(),
              1 if esterilizado else 0, observaciones.strip()))
        mascota_id = cursor.lastrowid
        conn.commit()
        return True, f"Mascota '{nombre.strip()}' registrada correctamente.", mascota_id
    except Exception as e:
        conn.rollback()
        return False, f"Error al registrar la mascota: {e}", None
    finally:
        conn.close()


def editar_mascota(mascota_id: int, nombre: str, cliente_id, dueño_nombre: str, dueño_telefono: str,
                    especie_id, especie_texto: str, raza: str, sexo: str,
                    fecha_nacimiento: str, color: str, peso_kg, microchip: str,
                    esterilizado: bool, observaciones: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre de la mascota es obligatorio."
    if sexo not in SEXOS:
        sexo = "Desconocido"

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE mascotas
        SET cliente_id = ?, dueño_nombre = ?, dueño_telefono = ?, nombre = ?, especie_id = ?,
            especie_texto = ?, raza = ?, sexo = ?, fecha_nacimiento = ?, color = ?,
            peso_kg = ?, microchip = ?, esterilizado = ?, observaciones = ?
        WHERE id = ?
    """, (cliente_id, dueño_nombre.strip(), dueño_telefono.strip(), nombre.strip(), especie_id,
          especie_texto.strip(), raza.strip(), sexo, fecha_nacimiento or None, color.strip(),
          peso_kg, microchip.strip(), 1 if esterilizado else 0, observaciones.strip(), mascota_id))
    conn.commit()
    conn.close()
    return True, "Ficha de la mascota actualizada."


def _fila_mascota_a_dict(f) -> dict:
    return {
        "id": f[0], "nombre": f[1], "cliente_id": f[2],
        "dueño": f[3] or "Sin dueño registrado", "dueño_telefono": f[4] or "",
        "especie": f[5] or "", "raza": f[6] or "", "sexo": f[7],
        "fecha_nacimiento": f[8] or "", "color": f[9] or "", "peso_kg": f[10],
        "microchip": f[11] or "", "esterilizado": bool(f[12]), "fallecido": bool(f[13]),
        "observaciones": f[14] or "", "fecha_creacion": f[15],
    }


def listar_mascotas(busqueda: str = "", incluir_fallecidos: bool = True) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    condiciones = []
    parametros: list = []
    if not incluir_fallecidos:
        condiciones.append("m.fallecido = 0")
    if busqueda.strip():
        condiciones.append(
            "(m.nombre LIKE ? OR COALESCE(NULLIF(cl.nombre, ''), m.dueño_nombre, '') LIKE ? "
            "OR COALESCE(m.raza, '') LIKE ? OR COALESCE(m.microchip, '') LIKE ?)"
        )
        q = f"%{busqueda.strip()}%"
        parametros += [q, q, q, q]
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT m.id, m.nombre, m.cliente_id,
               COALESCE(NULLIF(cl.nombre, ''), m.dueño_nombre, ''), m.dueño_telefono,
               COALESCE(es.nombre, m.especie_texto, ''), m.raza, m.sexo,
               m.fecha_nacimiento, m.color, m.peso_kg, m.microchip,
               m.esterilizado, m.fallecido, m.observaciones, m.fecha_creacion
        FROM mascotas m
        LEFT JOIN clientes cl ON m.cliente_id = cl.id
        LEFT JOIN especies_mascota es ON m.especie_id = es.id
        {where}
        ORDER BY m.nombre
    """, parametros)
    filas = cursor.fetchall()
    conn.close()
    return [_fila_mascota_a_dict(f) for f in filas]


def listar_mascotas_por_cliente(cliente_id: int) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.nombre, m.cliente_id,
               COALESCE(NULLIF(cl.nombre, ''), m.dueño_nombre, ''), m.dueño_telefono,
               COALESCE(es.nombre, m.especie_texto, ''), m.raza, m.sexo,
               m.fecha_nacimiento, m.color, m.peso_kg, m.microchip,
               m.esterilizado, m.fallecido, m.observaciones, m.fecha_creacion
        FROM mascotas m
        LEFT JOIN clientes cl ON m.cliente_id = cl.id
        LEFT JOIN especies_mascota es ON m.especie_id = es.id
        WHERE m.cliente_id = ?
        ORDER BY m.nombre
    """, (cliente_id,))
    filas = cursor.fetchall()
    conn.close()
    return [_fila_mascota_a_dict(f) for f in filas]


def obtener_mascota(mascota_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.nombre, m.cliente_id,
               COALESCE(NULLIF(cl.nombre, ''), m.dueño_nombre, ''), m.dueño_telefono,
               m.especie_id, COALESCE(es.nombre, m.especie_texto, ''), m.raza, m.sexo,
               m.fecha_nacimiento, m.color, m.peso_kg, m.microchip,
               m.esterilizado, m.fallecido, m.observaciones, m.fecha_creacion
        FROM mascotas m
        LEFT JOIN clientes cl ON m.cliente_id = cl.id
        LEFT JOIN especies_mascota es ON m.especie_id = es.id
        WHERE m.id = ?
    """, (mascota_id,))
    f = cursor.fetchone()
    conn.close()
    if f is None:
        return None
    return {
        "id": f[0], "nombre": f[1], "cliente_id": f[2],
        "dueño": f[3] or "Sin dueño registrado", "dueño_telefono": f[4] or "",
        "especie_id": f[5], "especie": f[6] or "", "raza": f[7] or "", "sexo": f[8],
        "fecha_nacimiento": f[9] or "", "color": f[10] or "", "peso_kg": f[11],
        "microchip": f[12] or "", "esterilizado": bool(f[13]), "fallecido": bool(f[14]),
        "observaciones": f[15] or "", "fecha_creacion": f[16],
    }


def marcar_fallecido(mascota_id: int, fallecido: bool = True) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM mascotas WHERE id = ?", (mascota_id,))
    if cursor.fetchone() is None:
        conn.close()
        return False, "La mascota no existe."
    cursor.execute("UPDATE mascotas SET fallecido = ? WHERE id = ?", (1 if fallecido else 0, mascota_id))
    conn.commit()
    conn.close()
    return True, "Mascota marcada como fallecida." if fallecido else "Mascota reactivada."


def calcular_edad(fecha_nacimiento: str) -> str:
    if not fecha_nacimiento:
        return "—"
    try:
        nacimiento = datetime.date.fromisoformat(fecha_nacimiento)
    except ValueError:
        return "—"
    hoy = datetime.date.today()
    años = hoy.year - nacimiento.year
    meses = hoy.month - nacimiento.month
    if hoy.day < nacimiento.day:
        meses -= 1
    if meses < 0:
        años -= 1
        meses += 12
    if años <= 0:
        return f"{meses} mes(es)"
    if meses == 0:
        return f"{años} año(s)"
    return f"{años} año(s) y {meses} mes(es)"


# ============================================================
# CONSULTAS (historial clínico)
# ============================================================
def crear_consulta(mascota_id: int, motivo: str, diagnostico: str, tratamiento_indicado: str,
                    peso_kg, temperatura, observaciones: str, proxima_visita: str,
                    costo, usuario_id: int) -> tuple[bool, str, int | None]:
    if not motivo.strip():
        return False, "El motivo de la consulta es obligatorio.", None
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO consultas_veterinarias
                (mascota_id, motivo, diagnostico, tratamiento_indicado, peso_kg, temperatura,
                 observaciones, proxima_visita, costo, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (mascota_id, motivo.strip(), diagnostico.strip(), tratamiento_indicado.strip(),
              peso_kg, temperatura, observaciones.strip(), proxima_visita or None,
              costo or 0, usuario_id))
        consulta_id = cursor.lastrowid
        # Si se registró un peso nuevo, se actualiza el peso vigente de la ficha
        if peso_kg:
            cursor.execute("UPDATE mascotas SET peso_kg = ? WHERE id = ?", (peso_kg, mascota_id))
        conn.commit()
        return True, "Consulta registrada en el historial clínico.", consulta_id
    except Exception as e:
        conn.rollback()
        return False, f"Error al registrar la consulta: {e}", None
    finally:
        conn.close()


def listar_consultas_por_mascota(mascota_id: int) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cv.id, cv.fecha, cv.motivo, cv.diagnostico, cv.tratamiento_indicado,
               cv.peso_kg, cv.temperatura, cv.observaciones, cv.proxima_visita, cv.costo,
               COALESCE(u.nombre_completo, '')
        FROM consultas_veterinarias cv
        LEFT JOIN usuarios u ON cv.usuario_id = u.id
        WHERE cv.mascota_id = ?
        ORDER BY cv.fecha DESC, cv.id DESC
    """, (mascota_id,))
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "fecha": f[1], "motivo": f[2], "diagnostico": f[3] or "",
         "tratamiento_indicado": f[4] or "", "peso_kg": f[5], "temperatura": f[6],
         "observaciones": f[7] or "", "proxima_visita": f[8] or "", "costo": f[9],
         "atendido_por": f[10]}
        for f in filas
    ]


def listar_consultas_del_dia(fecha: str = None) -> list[dict]:
    """Todas las consultas registradas en una fecha puntual (por defecto,
    hoy), con el nombre de la mascota y su dueño, para el Dashboard."""
    fecha = fecha or datetime.date.today().isoformat()
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cv.id, cv.fecha, m.nombre,
               COALESCE(NULLIF(cl.nombre, ''), m.dueño_nombre, ''), cv.motivo, cv.proxima_visita
        FROM consultas_veterinarias cv
        JOIN mascotas m ON cv.mascota_id = m.id
        LEFT JOIN clientes cl ON m.cliente_id = cl.id
        WHERE date(cv.fecha) = date(?)
        ORDER BY cv.fecha DESC
    """, (fecha,))
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "fecha": f[1], "mascota": f[2], "dueño": f[3] or "", "motivo": f[4],
         "proxima_visita": f[5] or ""}
        for f in filas
    ]


# ============================================================
# VACUNAS
# ============================================================
def crear_vacuna(mascota_id: int, vacuna: str, proxima_dosis: str, lote: str,
                  veterinario: str, observaciones: str, usuario_id: int,
                  fecha_aplicacion: str = None) -> tuple[bool, str]:
    if not vacuna.strip():
        return False, "El nombre de la vacuna es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    if fecha_aplicacion:
        cursor.execute("""
            INSERT INTO vacunas_mascota (mascota_id, vacuna, fecha_aplicacion, proxima_dosis,
                                          lote, veterinario, observaciones, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (mascota_id, vacuna.strip(), fecha_aplicacion, proxima_dosis or None, lote.strip(),
              veterinario.strip(), observaciones.strip(), usuario_id))
    else:
        cursor.execute("""
            INSERT INTO vacunas_mascota (mascota_id, vacuna, proxima_dosis, lote, veterinario,
                                          observaciones, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (mascota_id, vacuna.strip(), proxima_dosis or None, lote.strip(),
              veterinario.strip(), observaciones.strip(), usuario_id))
    conn.commit()
    conn.close()
    return True, "Vacuna registrada."


def listar_vacunas_por_mascota(mascota_id: int) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, vacuna, fecha_aplicacion, proxima_dosis, lote, veterinario, observaciones
        FROM vacunas_mascota
        WHERE mascota_id = ?
        ORDER BY fecha_aplicacion DESC, id DESC
    """, (mascota_id,))
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "vacuna": f[1], "fecha_aplicacion": f[2], "proxima_dosis": f[3] or "",
         "lote": f[4] or "", "veterinario": f[5] or "", "observaciones": f[6] or ""}
        for f in filas
    ]


def listar_vacunas_proximas(dias: int = 30) -> list[dict]:
    """Vacunas cuya próxima dosis vence dentro de los próximos N días (o ya
    está vencida), para el Dashboard: permite avisar a los dueños a tiempo."""
    conn = conectar()
    cursor = conn.cursor()
    limite = (datetime.date.today() + datetime.timedelta(days=dias)).isoformat()
    cursor.execute("""
        SELECT v.id, v.vacuna, v.proxima_dosis, m.id, m.nombre,
               COALESCE(NULLIF(cl.nombre, ''), m.dueño_nombre, ''), m.dueño_telefono
        FROM vacunas_mascota v
        JOIN mascotas m ON v.mascota_id = m.id
        LEFT JOIN clientes cl ON m.cliente_id = cl.id
        WHERE v.proxima_dosis IS NOT NULL AND v.proxima_dosis != '' AND m.fallecido = 0
              AND date(v.proxima_dosis) <= date(?)
        ORDER BY v.proxima_dosis ASC
    """, (limite,))
    filas = cursor.fetchall()
    conn.close()
    hoy = datetime.date.today().isoformat()
    resultado = []
    for f in filas:
        resultado.append({
            "id": f[0], "vacuna": f[1], "proxima_dosis": f[2], "mascota_id": f[3],
            "mascota": f[4], "dueño": f[5] or "", "dueño_telefono": f[6] or "",
            "vencida": f[2] < hoy,
        })
    return resultado


# ============================================================
# TRATAMIENTOS (desparasitaciones / medicación en curso)
# ============================================================
def crear_tratamiento(mascota_id: int, tipo: str, producto: str, fecha_fin: str,
                       dosis: str, frecuencia: str, observaciones: str,
                       usuario_id: int) -> tuple[bool, str]:
    if not producto.strip():
        return False, "El producto/medicamento es obligatorio."
    if tipo not in TIPOS_TRATAMIENTO:
        tipo = "Otro"
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tratamientos_mascota
            (mascota_id, tipo, producto, fecha_fin, dosis, frecuencia, estado, observaciones, usuario_id)
        VALUES (?, ?, ?, ?, ?, ?, 'Activo', ?, ?)
    """, (mascota_id, tipo, producto.strip(), fecha_fin or None, dosis.strip(),
          frecuencia.strip(), observaciones.strip(), usuario_id))
    conn.commit()
    conn.close()
    return True, "Tratamiento registrado."


def listar_tratamientos_por_mascota(mascota_id: int) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, tipo, producto, fecha_inicio, fecha_fin, dosis, frecuencia, estado, observaciones
        FROM tratamientos_mascota
        WHERE mascota_id = ?
        ORDER BY (estado = 'Activo') DESC, fecha_inicio DESC, id DESC
    """, (mascota_id,))
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "tipo": f[1], "producto": f[2], "fecha_inicio": f[3],
         "fecha_fin": f[4] or "", "dosis": f[5] or "", "frecuencia": f[6] or "",
         "estado": f[7], "observaciones": f[8] or ""}
        for f in filas
    ]


def finalizar_tratamiento(tratamiento_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tratamientos_mascota
        SET estado = 'Finalizado', fecha_fin = COALESCE(fecha_fin, date('now', 'localtime'))
        WHERE id = ?
    """, (tratamiento_id,))
    conn.commit()
    conn.close()
    return True, "Tratamiento marcado como finalizado."


# ============================================================
# FICHA COMPLETA (para el reporte PDF entregable al dueño)
# ============================================================
def obtener_ficha_completa(mascota_id: int) -> dict | None:
    """Junta la ficha de la mascota con su historial clínico, vacunas y
    tratamientos en un solo dict, listo para pasar al generador de PDF."""
    mascota = obtener_mascota(mascota_id)
    if mascota is None:
        return None
    mascota["edad"] = calcular_edad(mascota["fecha_nacimiento"])
    return {
        "mascota": mascota,
        "consultas": listar_consultas_por_mascota(mascota_id),
        "vacunas": listar_vacunas_por_mascota(mascota_id),
        "tratamientos": listar_tratamientos_por_mascota(mascota_id),
    }


def obtener_vacuna_detalle(vacuna_id: int) -> dict | None:
    """Datos de una vacuna puntual junto con la mascota y el dueño, para el
    Certificado de Vacunación (reporte de un solo registro de vacuna)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.id, v.vacuna, v.fecha_aplicacion, v.proxima_dosis, v.lote, v.veterinario,
               v.observaciones, m.id, m.nombre, COALESCE(es.nombre, m.especie_texto, ''), m.raza,
               COALESCE(NULLIF(cl.nombre, ''), m.dueño_nombre, ''), m.dueño_telefono
        FROM vacunas_mascota v
        JOIN mascotas m ON v.mascota_id = m.id
        LEFT JOIN clientes cl ON m.cliente_id = cl.id
        LEFT JOIN especies_mascota es ON m.especie_id = es.id
        WHERE v.id = ?
    """, (vacuna_id,))
    f = cursor.fetchone()
    conn.close()
    if f is None:
        return None
    return {
        "id": f[0], "vacuna": f[1], "fecha_aplicacion": f[2], "proxima_dosis": f[3] or "",
        "lote": f[4] or "", "veterinario": f[5] or "", "observaciones": f[6] or "",
        "mascota_id": f[7], "mascota": f[8], "especie": f[9] or "", "raza": f[10] or "",
        "dueño": f[11] or "", "dueño_telefono": f[12] or "",
    }


def obtener_consulta_detalle(consulta_id: int) -> dict | None:
    """Datos de una consulta puntual junto con la mascota y el dueño, para
    la Constancia de Consulta (reporte de un solo registro de consulta),
    usado por ejemplo desde la grilla de 'Consultas de hoy' del Dashboard."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cv.id, cv.fecha, cv.motivo, cv.diagnostico, cv.tratamiento_indicado,
               cv.peso_kg, cv.temperatura, cv.observaciones, cv.proxima_visita, cv.costo,
               COALESCE(u.nombre_completo, ''),
               m.id, m.nombre, COALESCE(es.nombre, m.especie_texto, ''), m.raza, m.sexo,
               COALESCE(NULLIF(cl.nombre, ''), m.dueño_nombre, ''), m.dueño_telefono
        FROM consultas_veterinarias cv
        JOIN mascotas m ON cv.mascota_id = m.id
        LEFT JOIN clientes cl ON m.cliente_id = cl.id
        LEFT JOIN especies_mascota es ON m.especie_id = es.id
        LEFT JOIN usuarios u ON cv.usuario_id = u.id
        WHERE cv.id = ?
    """, (consulta_id,))
    f = cursor.fetchone()
    conn.close()
    if f is None:
        return None
    return {
        "id": f[0], "fecha": f[1], "motivo": f[2], "diagnostico": f[3] or "",
        "tratamiento_indicado": f[4] or "", "peso_kg": f[5], "temperatura": f[6],
        "observaciones": f[7] or "", "proxima_visita": f[8] or "", "costo": f[9],
        "atendido_por": f[10] or "",
        "mascota_id": f[11], "mascota": f[12], "especie": f[13] or "", "raza": f[14] or "",
        "sexo": f[15], "dueño": f[16] or "", "dueño_telefono": f[17] or "",
    }


# ============================================================
# DASHBOARD
# ============================================================
def conteos_dashboard() -> dict:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mascotas WHERE fallecido = 0")
    total_mascotas = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM consultas_veterinarias WHERE date(fecha) = date('now', 'localtime')
    """)
    consultas_hoy = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tratamientos_mascota WHERE estado = 'Activo'")
    tratamientos_activos = cursor.fetchone()[0]
    conn.close()
    return {
        "total_mascotas": total_mascotas,
        "consultas_hoy": consultas_hoy,
        "tratamientos_activos": tratamientos_activos,
        "vacunas_proximas": len(listar_vacunas_proximas()),
    }
