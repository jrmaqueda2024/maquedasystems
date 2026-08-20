"""
models_rrhh.py
Capa de datos del módulo de Recursos Humanos (RRHH).
Tablas:
  - rrhh_empleados      : registro de personal
  - rrhh_asistencia     : registro diario de asistencia
  - rrhh_adelantos      : vales / adelantos de sueldo
"""
import sqlite3
import datetime
import os
from database import conectar


# ─────────────────────────────────────────────────────────────
#  INICIALIZACIÓN DE TABLAS
# ─────────────────────────────────────────────────────────────

def inicializar_tablas_rrhh():
    conn = conectar()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS rrhh_empleados (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre          TEXT    NOT NULL,
            cargo           TEXT    DEFAULT '',
            departamento    TEXT    DEFAULT '',
            telefono        TEXT    DEFAULT '',
            email           TEXT    DEFAULT '',
            fecha_ingreso   TEXT    NOT NULL,
            sueldo_mensual  REAL    NOT NULL DEFAULT 0,
            horas_dia       REAL    NOT NULL DEFAULT 8,
            activo          INTEGER NOT NULL DEFAULT 1,
            observaciones   TEXT    DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS rrhh_asistencia (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id     INTEGER NOT NULL REFERENCES rrhh_empleados(id),
            fecha           TEXT    NOT NULL,
            estado          TEXT    NOT NULL DEFAULT 'Presente',
            hora_entrada    TEXT    DEFAULT '',
            hora_salida     TEXT    DEFAULT '',
            observaciones   TEXT    DEFAULT '',
            UNIQUE(empleado_id, fecha)
        );

        CREATE TABLE IF NOT EXISTS rrhh_adelantos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id     INTEGER NOT NULL REFERENCES rrhh_empleados(id),
            fecha           TEXT    NOT NULL,
            monto           REAL    NOT NULL DEFAULT 0,
            descripcion     TEXT    DEFAULT '',
            estado          TEXT    NOT NULL DEFAULT 'Pendiente',
            archivo_adjunto TEXT    DEFAULT '',
            registrado_por  TEXT    DEFAULT '',
            fecha_descuento TEXT    DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
#  EMPLEADOS
# ─────────────────────────────────────────────────────────────

def listar_empleados(solo_activos=True) -> list:
    conn = conectar()
    c = conn.cursor()
    if solo_activos:
        c.execute("SELECT * FROM rrhh_empleados WHERE activo=1 ORDER BY nombre")
    else:
        c.execute("SELECT * FROM rrhh_empleados ORDER BY activo DESC, nombre")
    cols = [d[0] for d in c.description]
    rows = [dict(zip(cols, r)) for r in c.fetchall()]
    conn.close()
    return rows


def obtener_empleado(emp_id: int) -> dict:
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM rrhh_empleados WHERE id=?", (emp_id,))
    cols = [d[0] for d in c.description]
    row  = c.fetchone()
    conn.close()
    return dict(zip(cols, row)) if row else {}


def crear_empleado(nombre, cargo, departamento, telefono, email,
                   fecha_ingreso, sueldo_mensual, horas_dia, observaciones) -> int:
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        INSERT INTO rrhh_empleados
            (nombre, cargo, departamento, telefono, email,
             fecha_ingreso, sueldo_mensual, horas_dia, observaciones)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (nombre, cargo, departamento, telefono, email,
          fecha_ingreso, sueldo_mensual, horas_dia, observaciones))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id


def editar_empleado(emp_id, nombre, cargo, departamento, telefono, email,
                    fecha_ingreso, sueldo_mensual, horas_dia, observaciones):
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        UPDATE rrhh_empleados SET
            nombre=?, cargo=?, departamento=?, telefono=?, email=?,
            fecha_ingreso=?, sueldo_mensual=?, horas_dia=?, observaciones=?
        WHERE id=?
    """, (nombre, cargo, departamento, telefono, email,
          fecha_ingreso, sueldo_mensual, horas_dia, observaciones, emp_id))
    conn.commit()
    conn.close()


def desactivar_empleado(emp_id):
    conn = conectar()
    conn.execute("UPDATE rrhh_empleados SET activo=0 WHERE id=?", (emp_id,))
    conn.commit()
    conn.close()


def activar_empleado(emp_id):
    conn = conectar()
    conn.execute("UPDATE rrhh_empleados SET activo=1 WHERE id=?", (emp_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
#  ASISTENCIA
# ─────────────────────────────────────────────────────────────

ESTADOS_ASISTENCIA = ["Presente", "Ausente", "Tardanza", "Licencia", "Feriado"]


def registrar_asistencia(empleado_id, fecha, estado,
                         hora_entrada="", hora_salida="", observaciones=""):
    conn = conectar()
    conn.execute("""
        INSERT INTO rrhh_asistencia
            (empleado_id, fecha, estado, hora_entrada, hora_salida, observaciones)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(empleado_id, fecha) DO UPDATE SET
            estado=excluded.estado,
            hora_entrada=excluded.hora_entrada,
            hora_salida=excluded.hora_salida,
            observaciones=excluded.observaciones
    """, (empleado_id, fecha, estado, hora_entrada, hora_salida, observaciones))
    conn.commit()
    conn.close()


def obtener_asistencia_dia(fecha: str) -> list:
    """Devuelve la asistencia de TODOS los empleados activos para una fecha."""
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        SELECT e.id, e.nombre, e.cargo, e.sueldo_mensual,
               COALESCE(a.estado, 'Sin registro') as estado,
               COALESCE(a.hora_entrada, '') as hora_entrada,
               COALESCE(a.hora_salida,  '') as hora_salida,
               COALESCE(a.observaciones,'') as observaciones
        FROM rrhh_empleados e
        LEFT JOIN rrhh_asistencia a
               ON a.empleado_id = e.id AND a.fecha = ?
        WHERE e.activo = 1
        ORDER BY e.nombre
    """, (fecha,))
    cols = [d[0] for d in c.description]
    rows = [dict(zip(cols, r)) for r in c.fetchall()]
    conn.close()
    return rows


def obtener_resumen_periodo(emp_id: int, desde: str, hasta: str) -> dict:
    """Calcula días trabajados, ausencias, tardanzas y licencias en el período."""
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        SELECT estado, COUNT(*) as total
        FROM rrhh_asistencia
        WHERE empleado_id=? AND fecha BETWEEN ? AND ?
        GROUP BY estado
    """, (emp_id, desde, hasta))
    conteos = {row[0]: row[1] for row in c.fetchall()}
    conn.close()

    # Días calendario del período (sin contar feriados marcados)
    d1 = datetime.date.fromisoformat(desde)
    d2 = datetime.date.fromisoformat(hasta)
    dias_calendario = (d2 - d1).days + 1

    presentes  = conteos.get("Presente", 0) + conteos.get("Tardanza", 0)
    ausentes   = conteos.get("Ausente", 0)
    licencias  = conteos.get("Licencia", 0)
    feriados   = conteos.get("Feriado", 0)
    tardanzas  = conteos.get("Tardanza", 0)

    return {
        "dias_calendario": dias_calendario,
        "presentes":  presentes,
        "ausentes":   ausentes,
        "licencias":  licencias,
        "feriados":   feriados,
        "tardanzas":  tardanzas,
    }


def calcular_liquidacion(emp_id: int, desde: str, hasta: str) -> dict:
    """Calcula el sueldo neto del período considerando ausencias y adelantos."""
    emp     = obtener_empleado(emp_id)
    sueldo  = emp.get("sueldo_mensual", 0)
    resumen = obtener_resumen_periodo(emp_id, desde, hasta)

    # Días hábiles del período (lunes a viernes)
    d1 = datetime.date.fromisoformat(desde)
    d2 = datetime.date.fromisoformat(hasta)
    dias_habiles = sum(1 for i in range((d2 - d1).days + 1)
                       if (d1 + datetime.timedelta(days=i)).weekday() < 5)

    valor_dia    = sueldo / 30 if sueldo else 0
    descuento    = valor_dia * resumen["ausentes"]
    adelantos    = sum_adelantos_pendientes(emp_id, hasta)
    sueldo_bruto = sueldo * (dias_habiles / 30) if dias_habiles < 30 else sueldo
    sueldo_neto  = max(0, sueldo_bruto - descuento - adelantos)

    return {
        **resumen,
        "sueldo_mensual": sueldo,
        "dias_habiles":   dias_habiles,
        "valor_dia":      valor_dia,
        "descuento_ausencias": descuento,
        "adelantos_pendientes": adelantos,
        "sueldo_bruto":   sueldo_bruto,
        "sueldo_neto":    sueldo_neto,
    }


# ─────────────────────────────────────────────────────────────
#  ADELANTOS / VALES
# ─────────────────────────────────────────────────────────────

def listar_adelantos(empleado_id=None, estado=None) -> list:
    conn = conectar()
    c = conn.cursor()
    sql = """
        SELECT a.*, e.nombre as empleado_nombre
        FROM rrhh_adelantos a
        JOIN rrhh_empleados e ON e.id = a.empleado_id
        WHERE 1=1
    """
    params = []
    if empleado_id:
        sql += " AND a.empleado_id=?"
        params.append(empleado_id)
    if estado:
        sql += " AND a.estado=?"
        params.append(estado)
    sql += " ORDER BY a.fecha DESC"
    c.execute(sql, params)
    cols = [d[0] for d in c.description]
    rows = [dict(zip(cols, r)) for r in c.fetchall()]
    conn.close()
    return rows


def registrar_adelanto(empleado_id, fecha, monto, descripcion,
                       archivo_adjunto="", registrado_por="") -> int:
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        INSERT INTO rrhh_adelantos
            (empleado_id, fecha, monto, descripcion, estado,
             archivo_adjunto, registrado_por)
        VALUES (?,?,?,?,'Pendiente',?,?)
    """, (empleado_id, fecha, monto, descripcion, archivo_adjunto, registrado_por))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id


def marcar_adelanto_descontado(adelanto_id: int, fecha_descuento: str):
    conn = conectar()
    conn.execute("""
        UPDATE rrhh_adelantos SET estado='Descontado', fecha_descuento=?
        WHERE id=?
    """, (fecha_descuento, adelanto_id))
    conn.commit()
    conn.close()


def eliminar_adelanto(adelanto_id: int):
    conn = conectar()
    conn.execute("DELETE FROM rrhh_adelantos WHERE id=?", (adelanto_id,))
    conn.commit()
    conn.close()


def sum_adelantos_pendientes(empleado_id: int, hasta: str = None) -> float:
    conn = conectar()
    c = conn.cursor()
    if hasta:
        c.execute("""
            SELECT COALESCE(SUM(monto), 0) FROM rrhh_adelantos
            WHERE empleado_id=? AND estado='Pendiente' AND fecha<=?
        """, (empleado_id, hasta))
    else:
        c.execute("""
            SELECT COALESCE(SUM(monto), 0) FROM rrhh_adelantos
            WHERE empleado_id=? AND estado='Pendiente'
        """, (empleado_id,))
    total = c.fetchone()[0]
    conn.close()
    return total or 0


def sum_adelantos_pendientes_por_empleado() -> dict:
    """Igual que sum_adelantos_pendientes() pero para TODOS los empleados
    de una sola vez (una sola consulta agregada en vez de N consultas
    individuales -N conexiones a la BD-, una por cada fila de la grilla).
    Se usa en la pestaña Personal para que la grilla cargue al instante
    sin importar cuántos empleados haya."""
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        SELECT empleado_id, COALESCE(SUM(monto), 0)
        FROM rrhh_adelantos
        WHERE estado='Pendiente'
        GROUP BY empleado_id
    """)
    resultado = {fila[0]: fila[1] for fila in c.fetchall()}
    conn.close()
    return resultado


# ─────────────────────────────────────────────────────────────
#  RESUMEN GENERAL (para el panel inferior)
# ─────────────────────────────────────────────────────────────

def resumen_rrhh() -> dict:
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(sueldo_mensual),0) FROM rrhh_empleados WHERE activo=1")
    cant, total_sueldos = c.fetchone()
    c.execute("SELECT COALESCE(SUM(monto),0) FROM rrhh_adelantos WHERE estado='Pendiente'")
    total_adelantos = c.fetchone()[0]
    conn.close()
    total_sueldos = total_sueldos or 0
    total_adelantos = total_adelantos or 0
    return {
        "cantidad_empleados": cant or 0,
        "total_sueldos":      total_sueldos,
        "total_adelantos":    total_adelantos,
        "total_resta_sueldo": max(0, total_sueldos - total_adelantos),
    }


# ─────────────────────────────────────────────────────────────
#  DIRECTORIO DE ARCHIVOS ADJUNTOS
# ─────────────────────────────────────────────────────────────

def carpeta_adjuntos_rrhh() -> str:
    from utilidades_ui import obtener_carpeta_base
    ruta = os.path.join(obtener_carpeta_base(), "rrhh_adjuntos")
    os.makedirs(ruta, exist_ok=True)
    return ruta
