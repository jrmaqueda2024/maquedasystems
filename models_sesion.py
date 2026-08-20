"""
models_sesion.py
Cronómetro de uso del sistema: registra cada sesión de cada usuario
(inicio, fin, duración) para poder mostrar:
- Cuánto tiempo se usa el sistema en total y por día.
- En qué hora del día se usa más (hora pico).
- Historial de sesiones.
"""
from database import conectar


def iniciar_sesion(usuario_id: int | None, usuario_nombre: str) -> int:
    """Registra el inicio de una sesión y devuelve su id."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sesiones_uso (usuario_id, usuario_nombre, fecha_inicio)
        VALUES (?, ?, datetime('now', 'localtime'))
    """, (usuario_id, usuario_nombre))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def heartbeat_sesion(session_id: int) -> None:
    """Actualiza la sesión activa con la duración acumulada hasta ahora.
    Se llama periódicamente para no perder el conteo si la app se cierra
    inesperadamente."""
    if not session_id:
        return
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sesiones_uso
        SET duracion_segundos = CAST(
            (julianday(datetime('now', 'localtime')) - julianday(fecha_inicio)) * 86400 AS INTEGER
        )
        WHERE id = ?
    """, (session_id,))
    conn.commit()
    conn.close()


def cerrar_sesion(session_id: int) -> None:
    """Cierra la sesión y guarda la duración total."""
    if not session_id:
        return
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sesiones_uso
        SET fecha_fin = datetime('now', 'localtime'),
            duracion_segundos = CAST(
                (julianday(datetime('now', 'localtime')) - julianday(fecha_inicio)) * 86400 AS INTEGER
            )
        WHERE id = ?
    """, (session_id,))
    conn.commit()
    conn.close()


def tiempo_sesion_actual(session_id: int) -> int:
    """Segundos transcurridos desde que inició la sesión activa."""
    if not session_id:
        return 0
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT CAST(
            (julianday(datetime('now', 'localtime')) - julianday(fecha_inicio)) * 86400 AS INTEGER
        ) FROM sesiones_uso WHERE id = ?
    """, (session_id,))
    fila = cursor.fetchone()
    conn.close()
    return int(fila[0]) if fila and fila[0] is not None else 0


def tiempo_total_hoy(usuario_id: int | None = None) -> int:
    """Segundos totales de uso del día actual (global o por usuario)."""
    conn = conectar()
    cursor = conn.cursor()
    where = "WHERE date(fecha_inicio) = date('now', 'localtime')"
    params: tuple = ()
    if usuario_id is not None:
        where += " AND usuario_id = ?"
        params = (usuario_id,)
    cursor.execute(f"SELECT COALESCE(SUM(duracion_segundos),0) FROM sesiones_uso {where}", params)
    total = cursor.fetchone()[0]
    conn.close()
    return int(total or 0)


def tiempo_total_general(usuario_id: int | None = None) -> int:
    """Segundos totales de uso histórico."""
    conn = conectar()
    cursor = conn.cursor()
    if usuario_id is not None:
        cursor.execute(
            "SELECT COALESCE(SUM(duracion_segundos),0) FROM sesiones_uso WHERE usuario_id = ?",
            (usuario_id,),
        )
    else:
        cursor.execute("SELECT COALESCE(SUM(duracion_segundos),0) FROM sesiones_uso")
    total = cursor.fetchone()[0]
    conn.close()
    return int(total or 0)


def actividad_por_hora() -> list[tuple[int, int]]:
    """Devuelve una lista [(hora_0_a_23, segundos_acumulados), ...] usada para
    encontrar la hora pico de uso."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT CAST(strftime('%H', fecha_inicio) AS INTEGER) AS hora,
               COALESCE(SUM(duracion_segundos),0)
        FROM sesiones_uso
        GROUP BY hora
        ORDER BY hora
    """)
    filas = cursor.fetchall()
    conn.close()
    return [(int(f[0]), int(f[1])) for f in filas]


def hora_pico() -> tuple[int, int] | None:
    """Devuelve (hora, segundos) de la hora con más uso, o None si no hay datos."""
    datos = actividad_por_hora()
    if not datos:
        return None
    return max(datos, key=lambda x: x[1])


def ultimas_sesiones(limite: int = 30) -> list[dict]:
    """Últimas sesiones registradas con sus duraciones."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, usuario_nombre, fecha_inicio, fecha_fin, duracion_segundos
        FROM sesiones_uso
        ORDER BY id DESC
        LIMIT ?
    """, (limite,))
    filas = cursor.fetchall()
    conn.close()
    return [
        {
            "id": f[0],
            "usuario_nombre": f[1] or "",
            "fecha_inicio": f[2],
            "fecha_fin": f[3] or "(en curso)",
            "duracion_segundos": int(f[4] or 0),
        }
        for f in filas
    ]


def formatear_duracion(segundos: int) -> str:
    """Convierte segundos a 'HH:MM:SS' o '1d 2h 15m' si es muy largo."""
    segundos = int(segundos or 0)
    if segundos < 86400:
        h = segundos // 3600
        m = (segundos % 3600) // 60
        s = segundos % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    d = segundos // 86400
    resto = segundos % 86400
    h = resto // 3600
    m = (resto % 3600) // 60
    return f"{d}d {h}h {m}m"